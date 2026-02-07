"""Checkpoint Migration Strategy - 检查点迁移策略和配置.

负责确定检查点的迁移策略和目标层级。
"""

from dataclasses import dataclass

from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.value_objects import StorageTier


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
# 迁移策略
# =============================================================================


class CheckpointMigrationStrategy:
    """检查点迁移策略"""

    @staticmethod
    def get_next_tier(current_tier: StorageTier) -> StorageTier | None:
        """获取下一个存储层级

        Args:
            current_tier: 当前存储层级

        Returns:
            下一个存储层级或 None
        """
        tier_order = [StorageTier.NVME, StorageTier.FSX, StorageTier.S3]
        try:
            current_index = tier_order.index(current_tier)
            return tier_order[current_index + 1] if current_index < len(tier_order) - 1 else None
        except (ValueError, IndexError):
            return None

    @staticmethod
    def should_migrate_from_nvme(checkpoint: Checkpoint, position: int) -> bool:
        """判断是否应该从 NVMe 迁移

        Args:
            checkpoint: 检查点实体
            position: 在同一任务检查点中的位置（0 为最新）

        Returns:
            是否应该迁移
        """
        hot_retention_count = CHECKPOINT_MIGRATION_CONFIG["hot_retention_count"]
        return position >= hot_retention_count

    @staticmethod
    def should_migrate_from_fsx(checkpoint: Checkpoint, age_hours: float) -> bool:
        """判断是否应该从 FSx 迁移到 S3

        Args:
            checkpoint: 检查点实体
            age_hours: 检查点年龄（小时）

        Returns:
            是否应该迁移
        """
        cold_threshold = CHECKPOINT_MIGRATION_CONFIG["cold_age_threshold_hours"]
        return age_hours >= cold_threshold

    @staticmethod
    def is_storage_under_pressure(usage_percent: float) -> bool:
        """判断存储是否有压力

        Args:
            usage_percent: 使用率百分比（0.0 - 1.0）

        Returns:
            是否有压力
        """
        threshold = CHECKPOINT_MIGRATION_CONFIG["storage_pressure_threshold"]
        return usage_percent >= threshold

    @staticmethod
    def group_checkpoints_by_job(
        checkpoints: list[Checkpoint],
    ) -> dict[int, list[Checkpoint]]:
        """按训练任务分组检查点

        Args:
            checkpoints: 检查点列表

        Returns:
            按 training_job_id 分组的检查点字典
        """
        job_checkpoints: dict[int, list[Checkpoint]] = {}
        for cp in checkpoints:
            if cp.training_job_id not in job_checkpoints:
                job_checkpoints[cp.training_job_id] = []
            job_checkpoints[cp.training_job_id].append(cp)

        # 对每个任务的检查点按创建时间排序（最新在前）
        for job_id in job_checkpoints:
            job_checkpoints[job_id].sort(key=lambda x: x.created_at, reverse=True)

        return job_checkpoints