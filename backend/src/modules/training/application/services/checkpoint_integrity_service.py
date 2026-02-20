"""Checkpoint Integrity Service - 检查点完整性验证服务.

负责验证检查点的完整性和获取有效的恢复检查点。
"""

import structlog

from src.modules.training.application.interfaces import IStorageService
from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.repositories import ICheckpointRepository

logger = structlog.get_logger(__name__)


class CheckpointIntegrityService:
    """检查点完整性验证服务"""

    def __init__(
        self,
        checkpoint_repository: ICheckpointRepository,
        storage_service: IStorageService,
    ):
        self._checkpoint_repo = checkpoint_repository
        self._storage = storage_service

    async def verify_checkpoint_integrity(self, checkpoint_id: int) -> bool:
        """验证检查点完整性

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            bool: 是否完整
        """
        checkpoint = await self._checkpoint_repo.get_by_id(checkpoint_id)
        if checkpoint is None:
            logger.warning("checkpoint_not_found", checkpoint_id=checkpoint_id)
            return False

        if checkpoint.checksum is None:
            logger.warning("checkpoint_no_checksum", checkpoint_id=checkpoint_id)
            return False

        is_valid = await self._storage.verify_integrity(
            checkpoint.storage_path,
            checkpoint.checksum,
        )

        if not is_valid:
            logger.warning(
                "checkpoint_integrity_failed",
                checkpoint_id=checkpoint_id,
                path=checkpoint.storage_path,
            )

        return is_valid

    async def get_valid_checkpoint_for_restore(
        self,
        training_job_id: int,
    ) -> Checkpoint | None:
        """获取用于恢复的有效检查点

        如果最新检查点损坏，回退到上一个有效检查点。

        Args:
            training_job_id: 训练任务 ID

        Returns:
            Checkpoint | None: 有效检查点或 None
        """
        checkpoints = await self._checkpoint_repo.get_by_training_job_id(training_job_id)

        for checkpoint in checkpoints:
            if checkpoint.checksum is None:
                logger.debug(
                    "checkpoint_skipped_no_checksum",
                    checkpoint_id=checkpoint.id,
                    training_job_id=training_job_id,
                )
                continue

            is_valid = await self._storage.verify_integrity(
                checkpoint.storage_path,
                checkpoint.checksum,
            )

            if is_valid:
                logger.info(
                    "valid_checkpoint_found",
                    checkpoint_id=checkpoint.id,
                    training_job_id=training_job_id,
                    storage_tier=checkpoint.storage_tier.value,
                )
                return checkpoint

            logger.warning(
                "checkpoint_corrupted",
                checkpoint_id=checkpoint.id,
                training_job_id=training_job_id,
            )

        logger.error(
            "no_valid_checkpoint_found",
            training_job_id=training_job_id,
            checked_count=len(checkpoints),
        )
        return None

    async def validate_batch(
        self,
        checkpoint_ids: list[int],
    ) -> dict[int, bool]:
        """批量验证检查点完整性

        Args:
            checkpoint_ids: 检查点 ID 列表

        Returns:
            dict[int, bool]: 检查点 ID 到完整性状态的映射
        """
        results = {}
        for checkpoint_id in checkpoint_ids:
            results[checkpoint_id] = await self.verify_checkpoint_integrity(checkpoint_id)
        return results
