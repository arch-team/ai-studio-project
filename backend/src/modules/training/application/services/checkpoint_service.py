"""Checkpoint Service - 检查点管理综合服务 (T038).

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
from src.modules.training.application.services.checkpoint_base_service import CheckpointBaseService
from src.modules.training.application.services.checkpoint_creation_service import CheckpointCreationService
from src.modules.training.application.services.checkpoint_trigger_service import CheckpointTriggerService
from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.repositories import (
    ICheckpointRepository,
    ITrainingJobRepository,
)
from src.modules.training.domain.value_objects import CheckpointTriggerType


class CheckpointService:
    """检查点管理综合服务 - 组合多个专门服务."""

    def __init__(
        self,
        repository: ICheckpointRepository,
        training_job_repository: ITrainingJobRepository | None = None,
        storage_service: IStorageService | None = None,
    ):
        # 创建专门的子服务
        self._base_service = CheckpointBaseService(repository)
        self._creation_service = CheckpointCreationService(
            repository=repository,
            training_job_repository=training_job_repository,
            storage_service=storage_service,
        )
        self._trigger_service = CheckpointTriggerService(
            creation_service=self._creation_service,
            training_job_repo=training_job_repository,
        )

    # =========================================================================
    # 基础查询方法 - 委派给 base_service
    # =========================================================================

    async def get_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """根据 ID 获取检查点."""
        return await self._base_service.get_checkpoint(checkpoint_id)

    async def get_checkpoints_for_job(self, training_job_id: int) -> list[Checkpoint]:
        """获取训练任务的所有检查点."""
        return await self._base_service.get_checkpoints_for_job(training_job_id)

    async def get_latest_checkpoint(self, training_job_id: int) -> Checkpoint | None:
        """获取训练任务的最新检查点."""
        return await self._base_service.get_latest_checkpoint(training_job_id)

    async def count_checkpoints_for_job(self, training_job_id: int) -> int:
        """统计训练任务的检查点数量."""
        return await self._base_service.count_checkpoints_for_job(training_job_id)

    async def archive_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """归档检查点（移至冷存储）."""
        return await self._base_service.archive_checkpoint(checkpoint_id)

    async def delete_checkpoint(self, checkpoint_id: int) -> None:
        """软删除检查点."""
        await self._base_service.delete_checkpoint(checkpoint_id)

    # =========================================================================
    # 创建方法 - 委派给 creation_service
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
        """创建检查点 - 统一入口."""
        return await self._creation_service.create_checkpoint(
            job_id=job_id,
            trigger_type=trigger_type,
            checkpoint_name=checkpoint_name,
            epoch=epoch,
            step=step,
            loss=loss,
            accuracy=accuracy,
            metrics=metrics,
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
        return await self._creation_service.create_manual_checkpoint(
            training_job_id=training_job_id,
            checkpoint_name=checkpoint_name,
            storage_path=storage_path,
            epoch=epoch,
            step=step,
            loss=loss,
            accuracy=accuracy,
        )

    # =========================================================================
    # 特定场景方法 - 委派给 trigger_service
    # =========================================================================

    async def create_scheduled_checkpoints(self) -> list[Checkpoint]:
        """为所有 Running 状态的任务创建定期检查点."""
        return await self._trigger_service.create_scheduled_checkpoints()

    async def create_checkpoint_on_interrupt(self, job_id: int) -> Checkpoint | None:
        """训练中断时创建检查点."""
        return await self._trigger_service.create_checkpoint_on_interrupt(job_id)

    async def create_checkpoint_on_node_failure(
        self,
        job_id: int,
        pod_name: str,
    ) -> Checkpoint | None:
        """节点故障时创建检查点."""
        return await self._trigger_service.create_checkpoint_on_node_failure(job_id, pod_name)

    async def create_checkpoint_on_preemption(
        self,
        job_id: int,
        timeout_seconds: int = 300,
    ) -> Checkpoint | None:
        """资源抢占时创建检查点."""
        return await self._trigger_service.create_checkpoint_on_preemption(job_id, timeout_seconds)
