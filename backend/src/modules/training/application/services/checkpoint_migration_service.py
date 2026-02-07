"""Checkpoint Migration Service - 检查点分层迁移服务 (T038b-1).

协调检查点的分层存储迁移流程。
"""

import structlog

from src.modules.training.application.interfaces import (
    Alert,
    INotificationService,
    IStorageService,
)
from src.modules.training.application.services.checkpoint_integrity_service import (
    CheckpointIntegrityService,
)
from src.modules.training.application.services.checkpoint_migration_strategy import (
    CHECKPOINT_MIGRATION_CONFIG,
    CheckpointMigrationStrategy,
    MigrationResult,
    SingleMigrationResult,
)
from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.exceptions import CheckpointMigrationError
from src.modules.training.domain.repositories import ICheckpointRepository
from src.modules.training.domain.value_objects import StorageTier

logger = structlog.get_logger(__name__)


# =============================================================================
# CheckpointMigrationService
# =============================================================================


class CheckpointMigrationService:
    """检查点分层迁移服务"""

    def __init__(
        self,
        checkpoint_repository: ICheckpointRepository,
        storage_service: IStorageService,
        notification_service: INotificationService | None = None,
    ):
        self._checkpoint_repo = checkpoint_repository
        self._storage = storage_service
        self._notification = notification_service
        self._strategy = CheckpointMigrationStrategy()
        self._integrity_service = CheckpointIntegrityService(
            checkpoint_repository,
            storage_service,
        )

    # =========================================================================
    # 主入口方法
    # =========================================================================

    async def run_migration_cycle(self) -> MigrationResult:
        """执行迁移周期 (定时任务每 10 分钟调用)

        Returns:
            MigrationResult: 迁移结果统计
        """
        result = MigrationResult()

        # 检查是否需要紧急迁移
        nvme_usage = await self._storage.get_storage_usage(StorageTier.NVME.value)
        if self._strategy.is_storage_under_pressure(nvme_usage):
            return await self.handle_storage_pressure(StorageTier.NVME, nvme_usage)

        # 正常迁移流程
        # 1. 获取需要从 NVMe 迁移到 FSx 的检查点
        await self._migrate_nvme_to_fsx(result)

        # 2. 获取需要从 FSx 迁移到 S3 的检查点
        await self._migrate_fsx_to_s3(result)

        return result

    async def handle_storage_pressure(
        self,
        tier: StorageTier,
        usage_percent: float,
    ) -> MigrationResult:
        """处理存储压力 (>90% 触发紧急迁移)

        Args:
            tier: 存储层级
            usage_percent: 当前使用率

        Returns:
            MigrationResult: 迁移结果
        """
        result = MigrationResult(is_emergency=True)

        logger.warning(
            "storage_pressure_detected",
            tier=tier.value,
            usage_percent=usage_percent,
        )

        # 获取该存储层的所有检查点
        checkpoints = await self._checkpoint_repo.get_by_storage_tier(tier, limit=50)

        # 确定目标层
        target_tier = self._strategy.get_next_tier(tier)
        if target_tier is None:
            logger.error("no_target_tier_available", source_tier=tier.value)
            return result

        # 迁移所有检查点 (保留最新 3 个)
        hot_retention = CHECKPOINT_MIGRATION_CONFIG["hot_retention_count"]
        for checkpoint in checkpoints[hot_retention:]:
            migration_result = await self.migrate_checkpoint(checkpoint, target_tier)
            if migration_result.success:
                result.migrated_count += 1
            else:
                result.failed_count += 1

        return result

    # =========================================================================
    # 单个检查点迁移
    # =========================================================================

    async def migrate_checkpoint(
        self,
        checkpoint: Checkpoint,
        target_tier: StorageTier,
    ) -> SingleMigrationResult:
        """迁移单个检查点到目标存储层。"""
        max_retries = int(CHECKPOINT_MIGRATION_CONFIG["max_retry_count"])
        last_error = None

        for attempt in range(max_retries):
            try:
                result = await self._attempt_migration(checkpoint, target_tier)
                return result
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                self._log_migration_attempt_failure(checkpoint, attempt + 1, max_retries, e)
                continue

        # 所有重试都失败
        await self._send_migration_failure_alert(checkpoint, target_tier, last_error)
        return self._create_failure_result(checkpoint, target_tier, last_error)

    async def _attempt_migration(
        self,
        checkpoint: Checkpoint,
        target_tier: StorageTier,
    ) -> SingleMigrationResult:
        """执行单次迁移尝试。"""
        # 执行迁移
        new_path = await self._storage.migrate_checkpoint(
            source_path=checkpoint.storage_path,
            target_tier=target_tier.value,
            job_id=checkpoint.training_job_id,
        )

        # 验证完整性
        await self._verify_migration_integrity(checkpoint, new_path, target_tier)

        # 更新检查点记录
        await self._update_checkpoint_after_migration(checkpoint, target_tier, new_path)

        # 记录成功日志
        self._log_migration_success(checkpoint, target_tier)

        return SingleMigrationResult(
            success=True,
            checkpoint_id=checkpoint.id or 0,
            source_tier=checkpoint.storage_tier,
            target_tier=target_tier,
            new_path=new_path,
        )

    async def _verify_migration_integrity(
        self,
        checkpoint: Checkpoint,
        new_path: str,
        target_tier: StorageTier,
    ) -> None:
        """验证迁移后的检查点完整性。"""
        if not checkpoint.checksum:
            return

        is_valid = await self._storage.verify_integrity(new_path, checkpoint.checksum)
        if not is_valid:
            raise CheckpointMigrationError(
                checkpoint_id=checkpoint.id or 0,
                source_tier=checkpoint.storage_tier.value,
                target_tier=target_tier.value,
                reason="Integrity verification failed after migration",
            )

    async def _update_checkpoint_after_migration(
        self,
        checkpoint: Checkpoint,
        target_tier: StorageTier,
        new_path: str,
    ) -> None:
        """更新迁移后的检查点记录。"""
        checkpoint.migrate_to(target_tier)
        checkpoint.storage_path = new_path
        await self._checkpoint_repo.update(checkpoint)

    def _log_migration_success(self, checkpoint: Checkpoint, target_tier: StorageTier) -> None:
        """记录迁移成功日志。"""
        logger.info(
            "checkpoint_migrated",
            checkpoint_id=checkpoint.id,
            source_tier=checkpoint.storage_tier.value,
            target_tier=target_tier.value,
        )

    def _log_migration_attempt_failure(
        self,
        checkpoint: Checkpoint,
        attempt: int,
        max_retries: int,
        error: Exception,
    ) -> None:
        """记录迁移尝试失败日志。"""
        logger.warning(
            "migration_attempt_failed",
            checkpoint_id=checkpoint.id,
            attempt=attempt,
            max_retries=max_retries,
            error_type=type(error).__name__,
            error=str(error),
        )

    def _create_failure_result(
        self,
        checkpoint: Checkpoint,
        target_tier: StorageTier,
        error_message: str | None,
    ) -> SingleMigrationResult:
        """创建失败结果对象。"""
        return SingleMigrationResult(
            success=False,
            checkpoint_id=checkpoint.id or 0,
            source_tier=checkpoint.storage_tier,
            target_tier=target_tier,
            error_message=error_message,
        )

    # =========================================================================
    # 完整性验证（委托给 CheckpointIntegrityService）
    # =========================================================================

    async def verify_checkpoint_integrity(self, checkpoint_id: int) -> bool:
        """验证检查点完整性"""
        return await self._integrity_service.verify_checkpoint_integrity(checkpoint_id)

    async def get_valid_checkpoint_for_restore(
        self,
        training_job_id: int,
    ) -> Checkpoint | None:
        """获取用于恢复的有效检查点"""
        return await self._integrity_service.get_valid_checkpoint_for_restore(training_job_id)

    # =========================================================================
    # 私有方法
    # =========================================================================

    async def _migrate_nvme_to_fsx(self, result: MigrationResult) -> None:
        """从 NVMe 迁移到 FSx"""
        checkpoints = await self._checkpoint_repo.get_by_storage_tier(StorageTier.NVME, limit=100)
        job_checkpoints = self._strategy.group_checkpoints_by_job(checkpoints)

        # 对每个任务，迁移第 4 个及以后的检查点到 FSx
        for job_id, cps in job_checkpoints.items():
            for position, cp in enumerate(cps):
                if self._strategy.should_migrate_from_nvme(cp, position):
                    migration_result = await self.migrate_checkpoint(cp, StorageTier.FSX)
                    if migration_result.success:
                        result.migrated_count += 1
                    else:
                        result.failed_count += 1

    async def _migrate_fsx_to_s3(self, result: MigrationResult) -> None:
        """从 FSx 迁移到 S3 (归档)"""
        cold_threshold_hours = CHECKPOINT_MIGRATION_CONFIG["cold_age_threshold_hours"]

        # 获取超过阈值时间的旧检查点
        old_checkpoints = await self._checkpoint_repo.get_oldest_checkpoints(
            training_job_id=None,  # 获取所有任务的旧检查点
            hours_threshold=cold_threshold_hours,
        )

        for checkpoint in old_checkpoints:
            if checkpoint.storage_tier == StorageTier.FSX:
                migration_result = await self.migrate_checkpoint(checkpoint, StorageTier.S3)
                if migration_result.success:
                    result.migrated_count += 1
                else:
                    result.failed_count += 1

    async def _send_migration_failure_alert(
        self,
        checkpoint: Checkpoint,
        target_tier: StorageTier,
        error_message: str | None,
    ) -> None:
        """发送迁移失败告警"""
        if self._notification is None:
            return

        alert = Alert(
            title="检查点迁移失败",
            message=f"检查点 {checkpoint.id} 从 {checkpoint.storage_tier.value} 迁移到 {target_tier.value} 失败: {error_message}",
            severity="error",
            recipient_ids=[],  # TODO: 配置管理员 ID
            metadata={
                "checkpoint_id": checkpoint.id,
                "training_job_id": checkpoint.training_job_id,
                "source_tier": checkpoint.storage_tier.value,
                "target_tier": target_tier.value,
            },
        )
        await self._notification.send_alert(alert)
