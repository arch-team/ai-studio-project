"""Checkpoint Base Service - 检查点基础查询服务."""

from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.exceptions import CheckpointNotFoundError
from src.modules.training.domain.repositories import ICheckpointRepository
from src.shared.application.base_service_unified import BaseApplicationService


class CheckpointBaseService(BaseApplicationService[Checkpoint, int]):
    """检查点基础查询服务 - 提供基本的 CRUD 操作."""

    def __init__(self, repository: ICheckpointRepository):
        super().__init__(repository, "Checkpoint")
        self._not_found_error_factory = CheckpointNotFoundError

    async def get_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """根据 ID 获取检查点."""
        return await self._get_or_raise(checkpoint_id)

    async def get_checkpoints_for_job(self, training_job_id: int) -> list[Checkpoint]:
        """获取训练任务的所有检查点."""
        return await self._repository.get_by_training_job_id(training_job_id)

    async def get_latest_checkpoint(self, training_job_id: int) -> Checkpoint | None:
        """获取训练任务的最新检查点."""
        return await self._repository.get_latest_by_training_job_id(training_job_id)

    async def archive_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """归档检查点（移至冷存储）."""
        checkpoint = await self.get_checkpoint(checkpoint_id)
        checkpoint.archive()
        return await self._repository.update(checkpoint)

    async def delete_checkpoint(self, checkpoint_id: int) -> None:
        """软删除检查点."""
        checkpoint = await self.get_checkpoint(checkpoint_id)
        checkpoint.soft_delete()
        await self._repository.update(checkpoint)