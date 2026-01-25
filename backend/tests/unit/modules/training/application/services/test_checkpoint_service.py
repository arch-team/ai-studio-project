"""CheckpointService 单元测试 (T038)

测试覆盖:
- 核心功能: create_checkpoint, create_scheduled_checkpoints
- 触发场景: 定期、中断、节点故障、抢占、手动
- 存储策略: NVMe 优先、FSx 回退
- 元数据: 校验和验证
- 状态检查: 仅 Running 状态可创建检查点

参考: spec.md 检查点管理规范
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.value_objects import (
    CheckpointTriggerType,
    JobStatus,
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
    repository.get_latest_by_training_job_id = AsyncMock(return_value=None)
    repository.create = AsyncMock(
        side_effect=lambda cp: Checkpoint(
            id=1,
            training_job_id=cp.training_job_id,
            checkpoint_name=cp.checkpoint_name,
            storage_path=cp.storage_path,
            size_bytes=cp.size_bytes,
            checkpoint_type=cp.checkpoint_type,
            trigger_type=cp.trigger_type,
            epoch=cp.epoch,
            step=cp.step,
            checksum=cp.checksum,
            storage_tier=cp.storage_tier,
        )
    )
    repository.update = AsyncMock(side_effect=lambda cp: cp)
    repository.count_by_training_job_id = AsyncMock(return_value=0)
    repository.get_by_storage_tier = AsyncMock(return_value=[])
    return repository


@pytest.fixture
def mock_training_job_repository():
    """Mock ITrainingJobRepository"""
    from src.modules.training.domain.entities import TrainingJob

    repository = AsyncMock()

    # 创建 running 状态的训练任务
    running_job = MagicMock(spec=TrainingJob)
    running_job.id = 1
    running_job.job_name = "test-job-1"
    running_job.status = JobStatus.RUNNING
    running_job.checkpoint_interval = 30  # 每 30 分钟
    running_job.checkpoint_mount_path = "/mnt/checkpoints"

    repository.get_by_id = AsyncMock(return_value=running_job)
    repository.list_jobs = AsyncMock(return_value=([running_job], 1))
    return repository


@pytest.fixture
def mock_storage_service():
    """Mock IStorageService - 用于检查点存储操作"""
    service = AsyncMock()
    service.check_nvme_available = AsyncMock(return_value=True)
    service.check_fsx_available = AsyncMock(return_value=True)
    service.get_storage_path = AsyncMock(return_value="/mnt/nvme/checkpoints/cp-001")
    service.calculate_checksum = AsyncMock(return_value="abc123def456")
    service.get_checkpoint_size = AsyncMock(return_value=1024 * 1024 * 100)  # 100MB
    return service


@pytest.fixture
def checkpoint_service(mock_checkpoint_repository, mock_training_job_repository, mock_storage_service):
    """创建 CheckpointService 实例"""
    from src.modules.training.application.services.checkpoint_service import CheckpointService

    return CheckpointService(
        repository=mock_checkpoint_repository,
        training_job_repository=mock_training_job_repository,
        storage_service=mock_storage_service,
    )


# =============================================================================
# 测试 create_checkpoint - 统一入口
# =============================================================================


class TestCreateCheckpoint:
    """测试 create_checkpoint 统一入口方法"""

    @pytest.mark.asyncio
    async def test_create_scheduled_checkpoint_success(
        self, checkpoint_service, mock_checkpoint_repository, mock_training_job_repository
    ):
        """验证定期自动创建检查点 (SCHEDULED)"""
        # Arrange
        job_id = 1

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.SCHEDULED,
            checkpoint_name="epoch-5-step-1000",
        )

        # Assert
        assert result.training_job_id == job_id
        assert result.trigger_type == CheckpointTriggerType.SCHEDULED
        mock_checkpoint_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_checkpoint_on_training_interrupt(self, checkpoint_service, mock_checkpoint_repository):
        """验证训练中断时创建检查点 (INTERRUPT)"""
        # Arrange
        job_id = 1

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.INTERRUPT,
        )

        # Assert
        assert result.trigger_type == CheckpointTriggerType.INTERRUPT
        mock_checkpoint_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_checkpoint_on_node_failure(self, checkpoint_service, mock_checkpoint_repository):
        """验证节点故障时创建检查点 (NODE_FAILURE)"""
        # Arrange
        job_id = 1

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.NODE_FAILURE,
        )

        # Assert
        assert result.trigger_type == CheckpointTriggerType.NODE_FAILURE

    @pytest.mark.asyncio
    async def test_create_checkpoint_on_preemption(self, checkpoint_service, mock_checkpoint_repository):
        """验证资源抢占时创建检查点 (PREEMPTION)"""
        # Arrange
        job_id = 1

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.PREEMPTION,
        )

        # Assert
        assert result.trigger_type == CheckpointTriggerType.PREEMPTION

    @pytest.mark.asyncio
    async def test_create_manual_checkpoint_via_api(self, checkpoint_service, mock_checkpoint_repository):
        """验证用户手动触发检查点 (MANUAL)"""
        # Arrange
        job_id = 1
        checkpoint_name = "user-manual-checkpoint"

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.MANUAL,
            checkpoint_name=checkpoint_name,
        )

        # Assert
        assert result.trigger_type == CheckpointTriggerType.MANUAL
        assert result.checkpoint_name == checkpoint_name


# =============================================================================
# 测试存储策略
# =============================================================================


class TestStorageStrategy:
    """测试存储层选择策略"""

    @pytest.mark.asyncio
    async def test_checkpoint_saves_to_nvme_first(
        self, checkpoint_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证检查点优先保存到 NVMe (热存储)"""
        # Arrange: NVMe 可用
        mock_storage_service.check_nvme_available.return_value = True

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=1,
            trigger_type=CheckpointTriggerType.SCHEDULED,
        )

        # Assert: 存储层应为 NVME
        assert result.storage_tier == StorageTier.NVME
        mock_storage_service.check_nvme_available.assert_called()

    @pytest.mark.asyncio
    async def test_checkpoint_fallback_to_fsx_when_nvme_unavailable(
        self, checkpoint_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证 NVMe 不可用时回退到 FSx"""
        # Arrange: NVMe 不可用，FSx 可用
        mock_storage_service.check_nvme_available.return_value = False
        mock_storage_service.check_fsx_available.return_value = True
        mock_storage_service.get_storage_path.return_value = "/fsx/checkpoints/cp-001"

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=1,
            trigger_type=CheckpointTriggerType.SCHEDULED,
        )

        # Assert: 存储层应为 FSX
        assert result.storage_tier == StorageTier.FSX


# =============================================================================
# 测试元数据
# =============================================================================


class TestCheckpointMetadata:
    """测试检查点元数据"""

    @pytest.mark.asyncio
    async def test_checkpoint_metadata_includes_checksum(
        self, checkpoint_service, mock_storage_service, mock_checkpoint_repository
    ):
        """验证检查点包含 SHA-256 校验和"""
        # Arrange
        expected_checksum = "a1b2c3d4e5f6g7h8i9j0"
        mock_storage_service.calculate_checksum.return_value = expected_checksum

        # Act
        result = await checkpoint_service.create_checkpoint(
            job_id=1,
            trigger_type=CheckpointTriggerType.SCHEDULED,
        )

        # Assert
        assert result.checksum == expected_checksum
        mock_storage_service.calculate_checksum.assert_called()


# =============================================================================
# 测试查询功能
# =============================================================================


class TestCheckpointQueries:
    """测试检查点查询功能"""

    @pytest.mark.asyncio
    async def test_list_checkpoints_for_job(self, checkpoint_service, mock_checkpoint_repository):
        """验证查询任务的所有检查点"""
        # Arrange
        job_id = 1
        checkpoints = [
            Checkpoint(
                id=1,
                training_job_id=job_id,
                checkpoint_name="cp-1",
                storage_path="/path/1",
                size_bytes=100,
            ),
            Checkpoint(
                id=2,
                training_job_id=job_id,
                checkpoint_name="cp-2",
                storage_path="/path/2",
                size_bytes=200,
            ),
        ]
        mock_checkpoint_repository.get_by_training_job_id.return_value = checkpoints

        # Act
        result = await checkpoint_service.get_checkpoints_for_job(job_id)

        # Assert
        assert len(result) == 2
        mock_checkpoint_repository.get_by_training_job_id.assert_called_once_with(job_id)


# =============================================================================
# 测试状态检查
# =============================================================================


class TestJobStatusValidation:
    """测试任务状态验证"""

    @pytest.mark.asyncio
    async def test_only_running_jobs_can_create_checkpoint(self, checkpoint_service, mock_training_job_repository):
        """验证仅 Running 状态的任务可创建检查点"""
        from src.modules.training.domain.entities import TrainingJob

        # Arrange: 任务不是 Running 状态
        completed_job = MagicMock(spec=TrainingJob)
        completed_job.id = 2
        completed_job.status = JobStatus.COMPLETED
        mock_training_job_repository.get_by_id.return_value = completed_job

        # Act & Assert: 应抛出异常
        from src.modules.training.domain.exceptions import InvalidJobStateError

        with pytest.raises(InvalidJobStateError) as exc_info:
            await checkpoint_service.create_checkpoint(
                job_id=2,
                trigger_type=CheckpointTriggerType.SCHEDULED,
            )

        assert "RUNNING" in str(exc_info.value)


# =============================================================================
# 测试批量定期创建
# =============================================================================


class TestScheduledCheckpoints:
    """测试批量定期创建检查点"""

    @pytest.mark.asyncio
    async def test_create_scheduled_checkpoints_for_all_running_jobs(
        self, checkpoint_service, mock_training_job_repository, mock_checkpoint_repository
    ):
        """验证为所有 Running 状态的任务创建定期检查点"""
        from src.modules.training.domain.entities import TrainingJob

        # Arrange: 多个 running 任务
        running_jobs = []
        for i in range(3):
            job = MagicMock(spec=TrainingJob)
            job.id = i + 1
            job.job_name = f"test-job-{i+1}"
            job.status = JobStatus.RUNNING
            job.checkpoint_interval = 30
            job.checkpoint_mount_path = f"/mnt/checkpoints/{i+1}"
            running_jobs.append(job)

        mock_training_job_repository.list_jobs.return_value = (running_jobs, 3)

        # Act
        results = await checkpoint_service.create_scheduled_checkpoints()

        # Assert: 应为每个任务创建一个检查点
        assert len(results) == 3
        for result in results:
            assert result.trigger_type == CheckpointTriggerType.SCHEDULED


# =============================================================================
# 测试异常场景的检查点创建
# =============================================================================


class TestInterruptScenarios:
    """测试异常场景的检查点创建"""

    @pytest.mark.asyncio
    async def test_create_checkpoint_on_interrupt_returns_checkpoint(
        self, checkpoint_service, mock_checkpoint_repository
    ):
        """验证训练中断时能成功创建检查点并返回"""
        # Act
        result = await checkpoint_service.create_checkpoint_on_interrupt(job_id=1)

        # Assert
        assert result is not None
        assert result.trigger_type == CheckpointTriggerType.INTERRUPT

    @pytest.mark.asyncio
    async def test_create_checkpoint_on_node_failure_with_pod_name(
        self, checkpoint_service, mock_checkpoint_repository
    ):
        """验证节点故障时包含 pod 名称信息"""
        # Arrange
        pod_name = "training-job-1-worker-0"

        # Act
        result = await checkpoint_service.create_checkpoint_on_node_failure(
            job_id=1,
            pod_name=pod_name,
        )

        # Assert
        assert result is not None
        assert pod_name in result.checkpoint_name or result.metrics.get("failed_pod") == pod_name

    @pytest.mark.asyncio
    async def test_create_checkpoint_on_preemption_respects_timeout(
        self, checkpoint_service, mock_checkpoint_repository, mock_storage_service
    ):
        """验证抢占时遵守 5 分钟超时限制"""
        # Arrange
        timeout_seconds = 300  # 5 分钟

        # Act
        result = await checkpoint_service.create_checkpoint_on_preemption(
            job_id=1,
            timeout_seconds=timeout_seconds,
        )

        # Assert
        assert result is not None
        assert result.trigger_type == CheckpointTriggerType.PREEMPTION


# =============================================================================
# 测试边界情况
# =============================================================================


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_job_not_found_raises_error(self, checkpoint_service, mock_training_job_repository):
        """验证任务不存在时抛出错误"""
        # Arrange
        mock_training_job_repository.get_by_id.return_value = None

        # Act & Assert
        from src.modules.training.domain.exceptions import TrainingJobNotFoundError

        with pytest.raises(TrainingJobNotFoundError):
            await checkpoint_service.create_checkpoint(
                job_id=999,
                trigger_type=CheckpointTriggerType.SCHEDULED,
            )

    @pytest.mark.asyncio
    async def test_storage_failure_raises_error(self, checkpoint_service, mock_storage_service):
        """验证存储不可用时抛出错误"""
        # Arrange: 所有存储都不可用
        mock_storage_service.check_nvme_available.return_value = False
        mock_storage_service.check_fsx_available.return_value = False

        # Act & Assert
        from src.modules.training.domain.exceptions import CheckpointStorageError

        with pytest.raises(CheckpointStorageError):
            await checkpoint_service.create_checkpoint(
                job_id=1,
                trigger_type=CheckpointTriggerType.SCHEDULED,
            )
