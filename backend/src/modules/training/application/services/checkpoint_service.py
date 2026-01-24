"""Checkpoint Service - Business logic for checkpoint management (T038).

支持 5 种检查点触发场景:
- SCHEDULED: 定期自动创建
- INTERRUPT: 训练中断时创建
- NODE_FAILURE: 节点故障时创建
- PREEMPTION: 资源抢占时创建
- MANUAL: 用户手动触发

存储策略: NVMe (热) -> FSx (温) -> S3 (冷)
"""

from decimal import Decimal

from src.modules.training.application.interfaces import IStorageService
from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.exceptions import (
    CheckpointNotFoundError,
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
from src.shared.application import BaseService
from src.shared.utils import utc_now


class CheckpointService(BaseService[Checkpoint, int]):
    """Service for managing training checkpoints."""

    _not_found_error_factory = CheckpointNotFoundError

    def __init__(
        self,
        repository: ICheckpointRepository,
        training_job_repository: ITrainingJobRepository | None = None,
        storage_service: IStorageService | None = None,
    ):
        super().__init__(repository, "Checkpoint")
        self._training_job_repo = training_job_repository
        self._storage_service = storage_service

    # =========================================================================
    # 基础查询方法 (原有方法)
    # =========================================================================

    async def get_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """Get checkpoint by ID."""
        return await self._get_or_raise(checkpoint_id)

    async def get_checkpoints_for_job(self, training_job_id: int) -> list[Checkpoint]:
        """Get all checkpoints for a training job."""
        return await self._repository.get_by_training_job_id(training_job_id)

    async def get_latest_checkpoint(self, training_job_id: int) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""
        return await self._repository.get_latest_by_training_job_id(training_job_id)

    # =========================================================================
    # 统一入口方法 (T038 新增)
    # =========================================================================

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
        """创建检查点 - 统一入口

        Args:
            job_id: 训练任务 ID
            trigger_type: 触发类型 (SCHEDULED, INTERRUPT, NODE_FAILURE, PREEMPTION, MANUAL)
            checkpoint_name: 检查点名称 (可选，自动生成)
            epoch: 训练轮次
            step: 训练步数
            loss: 当前损失值
            accuracy: 当前准确率
            metrics: 其他指标

        Returns:
            Checkpoint: 创建的检查点实体

        Raises:
            TrainingJobNotFoundError: 任务不存在
            InvalidJobStateError: 任务状态不允许创建检查点
            CheckpointStorageError: 存储不可用
        """
        # 1. 验证任务存在且状态正确
        await self._validate_job_for_checkpoint(job_id)

        # 2. 生成检查点名称
        if checkpoint_name is None:
            checkpoint_name = self._generate_checkpoint_name(trigger_type, epoch, step)

        # 3. 确定存储层并保存
        storage_tier, storage_path, checksum, size_bytes = await self._save_to_storage(
            job_id, checkpoint_name
        )

        # 4. 确定检查点类型
        checkpoint_type = self._determine_checkpoint_type(trigger_type, epoch, step)

        # 5. 创建检查点实体
        checkpoint = Checkpoint(
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

        return await self._repository.create(checkpoint)

    # =========================================================================
    # 特定场景方法 (T038 新增)
    # =========================================================================

    async def create_scheduled_checkpoints(self) -> list[Checkpoint]:
        """为所有 Running 状态的任务创建定期检查点

        由定时任务调用，按配置的 checkpoint_interval 执行。

        Returns:
            list[Checkpoint]: 创建的检查点列表
        """
        if self._training_job_repo is None:
            return []

        # 查询所有 Running 状态的任务
        running_jobs, _ = await self._training_job_repo.list_jobs(
            status=JobStatus.RUNNING,
            page=1,
            page_size=1000,  # 假设不会超过 1000 个并行任务
        )

        checkpoints = []
        for job in running_jobs:
            try:
                checkpoint = await self.create_checkpoint(
                    job_id=job.id,
                    trigger_type=CheckpointTriggerType.SCHEDULED,
                )
                checkpoints.append(checkpoint)
            except (InvalidJobStateError, CheckpointStorageError):
                # 跳过无法创建检查点的任务，继续处理其他任务
                continue

        return checkpoints

    async def create_checkpoint_on_interrupt(self, job_id: int) -> Checkpoint | None:
        """训练中断时创建检查点

        Args:
            job_id: 训练任务 ID

        Returns:
            Checkpoint | None: 创建的检查点，失败返回 None
        """
        try:
            return await self.create_checkpoint(
                job_id=job_id,
                trigger_type=CheckpointTriggerType.INTERRUPT,
            )
        except (TrainingJobNotFoundError, InvalidJobStateError, CheckpointStorageError):
            return None

    async def create_checkpoint_on_node_failure(
        self,
        job_id: int,
        pod_name: str,
    ) -> Checkpoint | None:
        """节点故障时创建检查点

        当检测到 PodsReady=False 持续 >30s 时触发。

        Args:
            job_id: 训练任务 ID
            pod_name: 故障 Pod 名称

        Returns:
            Checkpoint | None: 创建的检查点，失败返回 None
        """
        try:
            checkpoint_name = f"node-failure-{pod_name}-{utc_now().strftime('%Y%m%d%H%M%S')}"
            return await self.create_checkpoint(
                job_id=job_id,
                trigger_type=CheckpointTriggerType.NODE_FAILURE,
                checkpoint_name=checkpoint_name,
                metrics={"failed_pod": pod_name},
            )
        except (TrainingJobNotFoundError, InvalidJobStateError, CheckpointStorageError):
            return None

    async def create_checkpoint_on_preemption(
        self,
        job_id: int,
        timeout_seconds: int = 300,
    ) -> Checkpoint | None:
        """资源抢占时创建检查点

        在抢占前触发，必须在 timeout_seconds 内完成。

        Args:
            job_id: 训练任务 ID
            timeout_seconds: 超时时间 (默认 5 分钟)

        Returns:
            Checkpoint | None: 创建的检查点，失败返回 None
        """
        # TODO: 实现超时控制逻辑
        try:
            return await self.create_checkpoint(
                job_id=job_id,
                trigger_type=CheckpointTriggerType.PREEMPTION,
            )
        except (TrainingJobNotFoundError, InvalidJobStateError, CheckpointStorageError):
            return None

    # =========================================================================
    # 原有方法 (保留兼容性)
    # =========================================================================

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
        """Create a manual checkpoint (保留兼容性)."""
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

    async def archive_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """Archive a checkpoint (move to cold storage)."""
        checkpoint = await self.get_checkpoint(checkpoint_id)
        checkpoint.archive()
        return await self._repository.update(checkpoint)

    async def delete_checkpoint(self, checkpoint_id: int) -> None:
        """Soft delete a checkpoint."""
        checkpoint = await self.get_checkpoint(checkpoint_id)
        checkpoint.soft_delete()
        await self._repository.update(checkpoint)

    # =========================================================================
    # 私有辅助方法
    # =========================================================================

    async def _validate_job_for_checkpoint(self, job_id: int):
        """验证任务是否存在且状态允许创建检查点"""
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
        """保存检查点到存储层

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
        storage_path = await self._storage_service.get_storage_path(
            job_id, checkpoint_name, storage_tier.value
        )

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
        """生成检查点名称"""
        timestamp = utc_now().strftime("%Y%m%d%H%M%S")
        prefix = trigger_type.value.lower()

        if epoch is not None and step is not None:
            return f"{prefix}-epoch{epoch}-step{step}-{timestamp}"
        elif epoch is not None:
            return f"{prefix}-epoch{epoch}-{timestamp}"
        elif step is not None:
            return f"{prefix}-step{step}-{timestamp}"
        else:
            return f"{prefix}-{timestamp}"

    def _determine_checkpoint_type(
        self,
        trigger_type: CheckpointTriggerType,
        epoch: int | None,
        step: int | None,
    ) -> CheckpointType:
        """根据触发类型和进度确定检查点类型"""
        if trigger_type == CheckpointTriggerType.MANUAL:
            return CheckpointType.MANUAL

        if epoch is not None:
            return CheckpointType.EPOCH
        elif step is not None:
            return CheckpointType.STEP
        else:
            return CheckpointType.EPOCH  # 默认按轮次
