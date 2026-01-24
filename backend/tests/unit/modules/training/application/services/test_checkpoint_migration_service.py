"""CheckpointMigrationService 单元测试 (T038b-1)

测试覆盖:
- 分层策略: 热检查点保留、温检查点迁移、冷检查点归档
- 迁移时机: 空闲时段执行、存储满载紧急迁移
- 容错处理: 迁移失败保留原位置、重试机制、告警
- 完整性验证: 校验和验证、损坏回退

参考: spec.md 检查点分层存储规范
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.value_objects import (
    CheckpointStatus,
    CheckpointTriggerType,
    CheckpointType,
    StorageTier,
)


# =============================================================================
# 测试 Fixtures
# =============================================================================


@pytest.fixture
def mock_checkpoint_repository():
    """Mock ICheckpointRepository"""
    repository = AsyncMock()
    repository.get_by_id = AsyncMock(return_value=None)
    repository.get_by_training_job_id = AsyncMock(return_value=[])
    repository.get_checkpoints_for_migration = AsyncMock(return_value=[])
    repository.get_oldest_checkpoints = AsyncMock(return_value=[])
    repository.get_by_storage_tier = AsyncMock(return_value=[])
    repository.update = AsyncMock(side_effect=lambda cp: cp)
    return repository


@pytest.fixture
def mock_storage_service():
    """Mock IStorageService"""
    service = AsyncMock()
    service.get_storage_usage = AsyncMock(return_value=0.5)  # 50% 使用率
    service.migrate_checkpoint = AsyncMock(return_value="/new/path/checkpoint")
    service.verify_integrity = AsyncMock(return_value=True)
    service.delete_checkpoint = AsyncMock()
    return service


@pytest.fixture
def mock_notification_service():
    """Mock INotificationService"""
    service = AsyncMock()
    service.send_alert = AsyncMock()
    return service


@pytest.fixture
def migration_service(mock_checkpoint_repository, mock_storage_service, mock_notification_service):
    """创建 CheckpointMigrationService 实例"""
    from src.modules.training.application.services.checkpoint_migration_service import (
        CheckpointMigrationService,
    )

    return CheckpointMigrationService(
        checkpoint_repository=mock_checkpoint_repository,
        storage_service=mock_storage_service,
        notification_service=mock_notification_service,
    )


def _create_checkpoint(
    id: int,
    training_job_id: int = 1,
    storage_tier: StorageTier = StorageTier.NVME,
    created_at: datetime | None = None,
) -> Checkpoint:
    """创建测试用检查点"""
    return Checkpoint(
        id=id,
        training_job_id=training_job_id,
        checkpoint_name=f"checkpoint-{id}",
        storage_path=f"/path/checkpoint-{id}",
        size_bytes=1024 * 1024 * 100,  # 100MB
        checkpoint_type=CheckpointType.EPOCH,
        trigger_type=CheckpointTriggerType.SCHEDULED,
        storage_tier=storage_tier,
        status=CheckpointStatus.AVAILABLE,
        checksum="abc123",
        created_at=created_at or datetime.utcnow(),
    )


# =============================================================================
# 测试热检查点保留策略
# =============================================================================


class TestHotCheckpointRetention:
    """测试热检查点 (NVMe) 保留策略"""

    @pytest.mark.asyncio
    async def test_keep_latest_3_checkpoints_in_nvme(
        self, migration_service, mock_checkpoint_repository, mock_storage_service
    ):
        """验证最新 3 个检查点保留在 NVMe (热存储)"""
        # Arrange: 5 个检查点，按时间排序 (最新在前)
        now = datetime.utcnow()
        checkpoints = [
            _create_checkpoint(i, storage_tier=StorageTier.NVME, created_at=now - timedelta(hours=i))
            for i in range(5)
        ]
        # get_by_storage_tier 返回所有 NVME 检查点
        mock_checkpoint_repository.get_by_storage_tier.return_value = checkpoints

        # Act
        result = await migration_service.run_migration_cycle()

        # Assert: 迁移了 2 个 (第 4、5 个)
        assert result.migrated_count == 2
        assert mock_storage_service.migrate_checkpoint.call_count == 2


# =============================================================================
# 测试温检查点迁移策略
# =============================================================================


class TestWarmCheckpointMigration:
    """测试温检查点 (FSx) 迁移策略"""

    @pytest.mark.asyncio
    async def test_migrate_4th_to_10th_checkpoint_to_fsx(
        self, migration_service, mock_checkpoint_repository, mock_storage_service
    ):
        """验证第 4-10 个检查点迁移到 FSx (温存储)"""
        # Arrange: 7 个检查点 (只有 4 个需要迁移，前 3 个保留)
        now = datetime.utcnow()
        checkpoints = [
            _create_checkpoint(i, storage_tier=StorageTier.NVME, created_at=now - timedelta(hours=i))
            for i in range(7)
        ]
        mock_checkpoint_repository.get_by_storage_tier.return_value = checkpoints

        # Act
        result = await migration_service.run_migration_cycle()

        # Assert: 迁移了 4 个 (第 4-7 个)
        assert mock_storage_service.migrate_checkpoint.call_count == 4


# =============================================================================
# 测试冷检查点归档策略
# =============================================================================


class TestColdCheckpointArchival:
    """测试冷检查点 (S3) 归档策略"""

    @pytest.mark.asyncio
    async def test_archive_checkpoints_older_than_72h_to_s3(
        self, migration_service, mock_checkpoint_repository, mock_storage_service
    ):
        """验证超过 72 小时的检查点归档到 S3 (冷存储)"""
        # Arrange: FSx 中有 3 个检查点，其中 2 个超过 72 小时
        old_time = datetime.utcnow() - timedelta(hours=80)
        fsx_checkpoints = [
            _create_checkpoint(1, storage_tier=StorageTier.FSX, created_at=datetime.utcnow()),
            _create_checkpoint(2, storage_tier=StorageTier.FSX, created_at=old_time),
            _create_checkpoint(3, storage_tier=StorageTier.FSX, created_at=old_time),
        ]
        mock_checkpoint_repository.get_by_storage_tier.side_effect = [
            [],  # NVME
            fsx_checkpoints,  # FSX
        ]
        mock_checkpoint_repository.get_oldest_checkpoints.return_value = fsx_checkpoints[1:]  # 旧的 2 个

        # Act
        result = await migration_service.run_migration_cycle()

        # Assert: get_oldest_checkpoints 被调用
        mock_checkpoint_repository.get_oldest_checkpoints.assert_called()


# =============================================================================
# 测试迁移时机
# =============================================================================


class TestMigrationTiming:
    """测试迁移执行时机"""

    @pytest.mark.asyncio
    async def test_migration_runs_during_idle_period(
        self, migration_service, mock_storage_service
    ):
        """验证迁移在空闲时段执行 (存储使用率正常)"""
        # Arrange: 存储使用率 50% (正常)
        mock_storage_service.get_storage_usage.return_value = 0.5

        # Act
        result = await migration_service.run_migration_cycle()

        # Assert: 正常执行迁移
        assert result.is_emergency is False

    @pytest.mark.asyncio
    async def test_emergency_migration_when_storage_above_90_percent(
        self, migration_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证存储使用率 >90% 时触发紧急迁移"""
        # Arrange: 存储使用率 95%
        mock_storage_service.get_storage_usage.return_value = 0.95
        checkpoints = [_create_checkpoint(i, storage_tier=StorageTier.NVME) for i in range(5)]
        mock_checkpoint_repository.get_by_storage_tier.return_value = checkpoints

        # Act
        result = await migration_service.handle_storage_pressure(
            tier=StorageTier.NVME,
            usage_percent=0.95,
        )

        # Assert: 触发紧急迁移
        assert result.is_emergency is True
        mock_storage_service.migrate_checkpoint.assert_called()


# =============================================================================
# 测试容错处理
# =============================================================================


class TestErrorHandling:
    """测试迁移失败处理"""

    @pytest.mark.asyncio
    async def test_migration_failure_preserves_original_checkpoint(
        self, migration_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证迁移失败时保留原检查点位置"""
        # Arrange: 迁移会失败
        mock_storage_service.migrate_checkpoint.side_effect = Exception("Storage error")
        now = datetime.utcnow()
        checkpoints = [
            _create_checkpoint(i, storage_tier=StorageTier.NVME, created_at=now - timedelta(hours=i))
            for i in range(5)
        ]
        mock_checkpoint_repository.get_by_storage_tier.return_value = checkpoints

        # Act
        result = await migration_service.run_migration_cycle()

        # Assert: 有失败记录
        assert result.failed_count >= 1

    @pytest.mark.asyncio
    async def test_retry_failed_migration_max_3_times(
        self, migration_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证迁移失败最多重试 3 次"""
        # Arrange: 前 2 次失败，第 3 次成功
        mock_storage_service.migrate_checkpoint.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            "/new/path",  # 第 3 次成功
        ]
        checkpoint = _create_checkpoint(1, storage_tier=StorageTier.NVME)

        # Act
        result = await migration_service.migrate_checkpoint(
            checkpoint=checkpoint,
            target_tier=StorageTier.FSX,
        )

        # Assert: 重试后成功
        assert result.success is True
        assert mock_storage_service.migrate_checkpoint.call_count == 3

    @pytest.mark.asyncio
    async def test_alert_on_persistent_migration_failure(
        self, migration_service, mock_storage_service, mock_notification_service, mock_checkpoint_repository
    ):
        """验证持续失败触发告警"""
        # Arrange: 所有重试都失败
        mock_storage_service.migrate_checkpoint.side_effect = Exception("Persistent error")
        checkpoint = _create_checkpoint(1, storage_tier=StorageTier.NVME)

        # Act
        result = await migration_service.migrate_checkpoint(
            checkpoint=checkpoint,
            target_tier=StorageTier.FSX,
        )

        # Assert: 发送告警
        assert result.success is False
        mock_notification_service.send_alert.assert_called()


# =============================================================================
# 测试完整性验证
# =============================================================================


class TestIntegrityVerification:
    """测试检查点完整性验证"""

    @pytest.mark.asyncio
    async def test_verify_checksum_before_restore(
        self, migration_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证恢复前验证校验和"""
        # Arrange
        checkpoint = _create_checkpoint(1, storage_tier=StorageTier.FSX)
        checkpoint.checksum = "expected-checksum"
        mock_checkpoint_repository.get_by_id.return_value = checkpoint
        mock_storage_service.verify_integrity.return_value = True

        # Act
        is_valid = await migration_service.verify_checkpoint_integrity(checkpoint.id)

        # Assert
        assert is_valid is True
        mock_storage_service.verify_integrity.assert_called_with(
            checkpoint.storage_path, checkpoint.checksum
        )

    @pytest.mark.asyncio
    async def test_fallback_to_previous_checkpoint_on_corruption(
        self, migration_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证损坏时回退到上一个检查点"""
        # Arrange: 当前检查点损坏，上一个有效
        corrupted_checkpoint = _create_checkpoint(2, storage_tier=StorageTier.FSX)
        previous_checkpoint = _create_checkpoint(1, storage_tier=StorageTier.FSX)

        # 模拟获取任务的所有检查点
        mock_checkpoint_repository.get_by_training_job_id.return_value = [
            corrupted_checkpoint,
            previous_checkpoint,
        ]
        # 第一个检查点损坏，第二个有效
        mock_storage_service.verify_integrity.side_effect = [False, True]

        # Act
        fallback = await migration_service.get_valid_checkpoint_for_restore(
            training_job_id=1,
        )

        # Assert: 返回上一个有效检查点
        assert fallback is not None
        assert fallback.id == 1  # 上一个检查点


# =============================================================================
# 测试迁移结果统计
# =============================================================================


class TestMigrationResults:
    """测试迁移结果统计"""

    @pytest.mark.asyncio
    async def test_migration_cycle_returns_statistics(
        self, migration_service, mock_checkpoint_repository, mock_storage_service
    ):
        """验证迁移周期返回统计信息"""
        # Arrange
        now = datetime.utcnow()
        checkpoints = [
            _create_checkpoint(i, storage_tier=StorageTier.NVME, created_at=now - timedelta(hours=i))
            for i in range(5)
        ]
        mock_checkpoint_repository.get_by_storage_tier.return_value = checkpoints

        # Act
        result = await migration_service.run_migration_cycle()

        # Assert: 返回包含统计的结果
        assert hasattr(result, "migrated_count")
        assert hasattr(result, "failed_count")
        assert hasattr(result, "skipped_count")
        assert hasattr(result, "is_emergency")
