"""Checkpoint Creation Service - 检查点创建核心逻辑."""

from decimal import Decimal

from src.modules.training.application.interfaces import IStorageService
from src.modules.training.domain.entities import Checkpoint, TrainingJob
from src.modules.training.domain.exceptions import (
    CheckpointStorageError,
    InvalidJobStateError,
    TrainingJobNotFoundError,
)
from src.modules.training.domain.repositories import (
    ICheckpointRepository,
    ITrainingJobRepository,
)
from src.modules.training.domain.value_objects import (
    CheckpointTriggerType,
    CheckpointType,
    JobStatus,
    StorageTier,
)
from src.shared.utils import utc_now


class CheckpointCreationService:
    """检查点创建服务 - 处理检查点创建的核心逻辑."""

    def __init__(
        self,
        repository: ICheckpointRepository,
        training_job_repository: ITrainingJobRepository | None = None,
        storage_service: IStorageService | None = None,
    ):
        self._repository = repository
        self._training_job_repo = training_job_repository
        self._storage_service = storage_service

    async def create_checkpoint(
        self,
        job_id: int,
        trigger_type: CheckpointTriggerType,
        checkpoint_name: str | None = None,
        epoch: int | None = None,
        step: int | None = None,
        loss: Decimal | None = None,
        accuracy: Decimal | None = None,
        metrics: dict | None = None,
    ) -> Checkpoint:
        """创建检查点 - 统一入口.

        Raises:
            TrainingJobNotFoundError: 任务不存在
            InvalidJobStateError: 任务状态不允许创建检查点
            CheckpointStorageError: 存储不可用
        """
        # 验证任务
        await self._validate_job_for_checkpoint(job_id)

        # 生成名称
        if checkpoint_name is None:
            checkpoint_name = self._generate_checkpoint_name(trigger_type, epoch, step)

        # 保存到存储
        storage_info = await self._save_to_storage(job_id, checkpoint_name)

        # 创建实体
        checkpoint = self._build_checkpoint_entity(
            job_id=job_id,
            checkpoint_name=checkpoint_name,
            trigger_type=trigger_type,
            storage_info=storage_info,
            epoch=epoch,
            step=step,
            loss=loss,
            accuracy=accuracy,
            metrics=metrics,
        )

        return await self._repository.create(checkpoint)

    def _build_checkpoint_entity(
        self,
        job_id: int,
        checkpoint_name: str,
        trigger_type: CheckpointTriggerType,
        storage_info: tuple,
        epoch: int | None,
        step: int | None,
        loss: Decimal | None,
        accuracy: Decimal | None,
        metrics: dict | None,
    ) -> Checkpoint:
        """构建检查点实体."""
        storage_tier, storage_path, checksum, size_bytes = storage_info
        checkpoint_type = self._determine_checkpoint_type(trigger_type, epoch, step)

        return Checkpoint(
            id=0,  # 由数据库生成
            training_job_id=job_id,
            checkpoint_name=checkpoint_name,
            storage_path=storage_path,
            size_bytes=size_bytes,
            checkpoint_type=checkpoint_type,
            trigger_type=trigger_type,
            epoch=epoch,
            step=step,
            checksum=checksum,
            loss=loss,
            accuracy=accuracy,
            metrics=metrics,
            storage_tier=storage_tier,
        )

    async def create_manual_checkpoint(
        self,
        training_job_id: int,
        checkpoint_name: str,
        storage_path: str,
        epoch: int | None = None,
        step: int | None = None,
        loss: Decimal | None = None,
        accuracy: Decimal | None = None,
    ) -> Checkpoint:
        """创建手动检查点 (保留兼容性)."""
        checkpoint = Checkpoint(
            id=0,
            training_job_id=training_job_id,
            checkpoint_name=checkpoint_name,
            storage_path=storage_path,
            size_bytes=0,  # Will be updated when actual checkpoint is saved
            checkpoint_type=CheckpointType.MANUAL,
            trigger_type=CheckpointTriggerType.MANUAL,
            epoch=epoch,
            step=step,
            loss=loss,
            accuracy=accuracy,
        )
        return await self._repository.create(checkpoint)

    async def _validate_job_for_checkpoint(self, job_id: int) -> TrainingJob | None:
        """验证任务是否存在且状态允许创建检查点."""
        if self._training_job_repo is None:
            # 无任务仓库时跳过验证 (用于测试)
            return None

        job = await self._training_job_repo.get_by_id(job_id)
        if job is None:
            raise TrainingJobNotFoundError(str(job_id))

        if job.status != JobStatus.RUNNING:
            raise InvalidJobStateError(
                job_id=job_id,
                current_state=job.status.value,
                operation="create checkpoint (only RUNNING jobs can create checkpoints)",
            )

        return job

    async def _save_to_storage(
        self,
        job_id: int,
        checkpoint_name: str,
    ) -> tuple[StorageTier, str, str, int]:
        """保存检查点到存储层.

        优先使用 NVMe，不可用时回退到 FSx。

        Returns:
            tuple: (storage_tier, storage_path, checksum, size_bytes)
        """
        if self._storage_service is None:
            # 无存储服务时使用默认值 (用于测试)
            return (
                StorageTier.NVME,
                f"/mnt/nvme/checkpoints/{job_id}/{checkpoint_name}",
                "default-checksum",
                0,
            )

        # 检查 NVMe 可用性
        if await self._storage_service.check_nvme_available(job_id):
            storage_tier = StorageTier.NVME
        elif await self._storage_service.check_fsx_available(job_id):
            storage_tier = StorageTier.FSX
        else:
            raise CheckpointStorageError(
                "No storage available (both NVMe and FSx unavailable)",
                job_id=job_id,
            )

        # 获取存储路径
        storage_path = await self._storage_service.get_storage_path(job_id, checkpoint_name, storage_tier.value)

        # 计算校验和和大小
        checksum = await self._storage_service.calculate_checksum(storage_path)
        size_bytes = await self._storage_service.get_checkpoint_size(storage_path)

        return storage_tier, storage_path, checksum, size_bytes

    def _generate_checkpoint_name(
        self,
        trigger_type: CheckpointTriggerType,
        epoch: int | None,
        step: int | None,
    ) -> str:
        """生成检查点名称."""
        timestamp = utc_now().strftime("%Y%m%d%H%M%S")
        prefix = trigger_type.value.lower()

        # 构建名称部分
        parts = [prefix]
        if epoch is not None:
            parts.append(f"epoch{epoch}")
        if step is not None:
            parts.append(f"step{step}")
        parts.append(timestamp)

        return "-".join(parts)

    def _determine_checkpoint_type(
        self,
        trigger_type: CheckpointTriggerType,
        epoch: int | None,
        step: int | None,
    ) -> CheckpointType:
        """根据触发类型和进度确定检查点类型."""
        if trigger_type == CheckpointTriggerType.MANUAL:
            return CheckpointType.MANUAL

        if epoch is not None:
            return CheckpointType.EPOCH
        if step is not None:
            return CheckpointType.STEP
        return CheckpointType.EPOCH  # 默认按轮次