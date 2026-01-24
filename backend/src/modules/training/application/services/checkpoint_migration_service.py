"""Checkpoint Migration Service - 检查点分层迁移服务 (T038b-1).

实现分层存储策略:
- 热检查点 (NVMe): 保留最近 3 个
- 温检查点 (FSx): 保留第 4-10 个
- 冷检查点 (S3): 超过 72 小时或第 10 个以后

迁移策略:
- 定期迁移: 每 10 分钟执行一次
- 紧急迁移: 存储使用率 >90% 时立即执行
- 重试机制: 失败最多重试 3 次
"""

import logging
from dataclasses import dataclass

from src.modules.training.application.interfaces import (
    Alert,
    INotificationService,
    IStorageService,
)
from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.exceptions import CheckpointMigrationError
from src.modules.training.domain.repositories import ICheckpointRepository
from src.modules.training.domain.value_objects import StorageTier

logger = logging.getLogger(__name__)


# =============================================================================
# 配置常量
# =============================================================================

CHECKPOINT_MIGRATION_CONFIG = {
    "hot_retention_count": 3,  # NVMe 保留最近 3 个
    "warm_retention_count": 10,  # FSx 保留 4-10
    "cold_age_threshold_hours": 72,  # 超过 72 小时归档
    "migration_interval_minutes": 10,
    "storage_pressure_threshold": 0.9,  # 90% 触发紧急迁移
    "max_retry_count": 3,
}


# =============================================================================
# 结果数据类
# =============================================================================


@dataclass
class MigrationResult:
    """迁移结果"""

    migrated_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    is_emergency: bool = False


@dataclass
class SingleMigrationResult:
    """单个检查点迁移结果"""

    success: bool
    checkpoint_id: int
    source_tier: StorageTier
    target_tier: StorageTier
    new_path: str | None = None
    error_message: str | None = None


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
        if nvme_usage >= CHECKPOINT_MIGRATION_CONFIG["storage_pressure_threshold"]:
            emergency_result = await self.handle_storage_pressure(
                tier=StorageTier.NVME,
                usage_percent=nvme_usage,
            )
            return emergency_result

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
            f"Storage pressure detected: {tier.value} at {usage_percent:.1%}, triggering emergency migration"
        )

        # 获取该存储层的所有检查点
        checkpoints = await self._checkpoint_repo.get_by_storage_tier(tier, limit=50)

        # 确定目标层
        target_tier = self._get_next_tier(tier)
        if target_tier is None:
            logger.error(f"No target tier available for migration from {tier.value}")
            return result

        # 迁移所有检查点 (保留最新 3 个)
        for checkpoint in checkpoints[CHECKPOINT_MIGRATION_CONFIG["hot_retention_count"]:]:
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
        """迁移单个检查点到目标存储层

        Args:
            checkpoint: 待迁移的检查点
            target_tier: 目标存储层级

        Returns:
            SingleMigrationResult: 迁移结果
        """
        max_retries = CHECKPOINT_MIGRATION_CONFIG["max_retry_count"]
        last_error = None

        for attempt in range(max_retries):
            try:
                # 执行迁移
                new_path = await self._storage.migrate_checkpoint(
                    source_path=checkpoint.storage_path,
                    target_tier=target_tier.value,
                    job_id=checkpoint.training_job_id,
                )

                # 验证迁移后的完整性
                is_valid = await self._storage.verify_integrity(
                    new_path, checkpoint.checksum
                )
                if not is_valid:
                    raise CheckpointMigrationError(
                        checkpoint_id=checkpoint.id,
                        source_tier=checkpoint.storage_tier.value,
                        target_tier=target_tier.value,
                        reason="Integrity verification failed after migration",
                    )

                # 更新检查点记录
                checkpoint.migrate_to(target_tier)
                checkpoint.storage_path = new_path
                await self._checkpoint_repo.update(checkpoint)

                logger.info(
                    f"Checkpoint {checkpoint.id} migrated from {checkpoint.storage_tier.value} to {target_tier.value}"
                )

                return SingleMigrationResult(
                    success=True,
                    checkpoint_id=checkpoint.id,
                    source_tier=checkpoint.storage_tier,
                    target_tier=target_tier,
                    new_path=new_path,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Migration attempt {attempt + 1}/{max_retries} failed for checkpoint {checkpoint.id}: {e}"
                )
                continue

        # 所有重试都失败
        await self._send_migration_failure_alert(checkpoint, target_tier, last_error)

        return SingleMigrationResult(
            success=False,
            checkpoint_id=checkpoint.id,
            source_tier=checkpoint.storage_tier,
            target_tier=target_tier,
            error_message=last_error,
        )

    # =========================================================================
    # 完整性验证
    # =========================================================================

    async def verify_checkpoint_integrity(self, checkpoint_id: int) -> bool:
        """验证检查点完整性

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            bool: 是否完整
        """
        checkpoint = await self._checkpoint_repo.get_by_id(checkpoint_id)
        if checkpoint is None:
            return False

        if checkpoint.checksum is None:
            return False

        return await self._storage.verify_integrity(
            checkpoint.storage_path, checkpoint.checksum
        )

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
                continue

            is_valid = await self._storage.verify_integrity(
                checkpoint.storage_path, checkpoint.checksum
            )
            if is_valid:
                return checkpoint

        return None

    # =========================================================================
    # 私有方法
    # =========================================================================

    async def _migrate_nvme_to_fsx(self, result: MigrationResult) -> None:
        """从 NVMe 迁移到 FSx"""
        # 获取所有需要迁移的检查点 (排除最新 3 个)
        # 这里简化处理，实际需要按 training_job_id 分组
        checkpoints = await self._checkpoint_repo.get_by_storage_tier(
            StorageTier.NVME, limit=100
        )

        # 按 training_job_id 分组
        job_checkpoints: dict[int, list[Checkpoint]] = {}
        for cp in checkpoints:
            if cp.training_job_id not in job_checkpoints:
                job_checkpoints[cp.training_job_id] = []
            job_checkpoints[cp.training_job_id].append(cp)

        # 对每个任务，迁移第 4 个及以后的检查点到 FSx
        for job_id, cps in job_checkpoints.items():
            # 按创建时间排序 (最新在前)
            sorted_cps = sorted(cps, key=lambda x: x.created_at, reverse=True)

            # 迁移第 4 个及以后的
            for cp in sorted_cps[CHECKPOINT_MIGRATION_CONFIG["hot_retention_count"]:]:
                migration_result = await self.migrate_checkpoint(cp, StorageTier.FSX)
                if migration_result.success:
                    result.migrated_count += 1
                else:
                    result.failed_count += 1

    async def _migrate_fsx_to_s3(self, result: MigrationResult) -> None:
        """从 FSx 迁移到 S3 (归档)"""
        # 获取超过 72 小时的检查点
        # 这里需要按 training_job_id 获取
        checkpoints = await self._checkpoint_repo.get_by_storage_tier(
            StorageTier.FSX, limit=100
        )

        for cp in checkpoints:
            old_checkpoints = await self._checkpoint_repo.get_oldest_checkpoints(
                cp.training_job_id,
                hours_threshold=CHECKPOINT_MIGRATION_CONFIG["cold_age_threshold_hours"],
            )

            for old_cp in old_checkpoints:
                if old_cp.storage_tier == StorageTier.FSX:
                    migration_result = await self.migrate_checkpoint(old_cp, StorageTier.S3)
                    if migration_result.success:
                        result.migrated_count += 1
                    else:
                        result.failed_count += 1

    def _get_next_tier(self, current_tier: StorageTier) -> StorageTier | None:
        """获取下一个存储层"""
        tier_order = [StorageTier.NVME, StorageTier.FSX, StorageTier.S3]
        try:
            current_index = tier_order.index(current_tier)
            return tier_order[current_index + 1] if current_index < len(tier_order) - 1 else None
        except (ValueError, IndexError):
            return None

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
