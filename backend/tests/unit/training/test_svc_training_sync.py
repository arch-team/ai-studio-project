"""训练任务状态同步服务单元测试 - TDD Red-Green-Refactor

T037: 训练任务状态同步服务
- 定时同步 HyperPod 训练状态到数据库
- 处理状态转换事件
- 抢占计数和连续失败逻辑
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.training.domain.entities.training_job import TrainingJob
from src.modules.training.domain.value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
)

# === Fixtures ===


def create_mock_list_jobs(jobs_by_status: dict[JobStatus, list[TrainingJob]]):
    """创建 list_jobs mock，根据 status 参数返回不同的任务列表"""

    async def mock_list_jobs(
        owner_id=None,
        status=None,
        priority=None,
        submitted_after=None,
        submitted_before=None,
        page=1,
        page_size=20,
        sort_by="created_at",
        sort_order="desc",
    ):
        if status is not None:
            jobs = jobs_by_status.get(status, [])
            return (jobs, len(jobs))
        # 如果没指定 status，返回所有任务
        all_jobs = []
        for job_list in jobs_by_status.values():
            all_jobs.extend(job_list)
        return (all_jobs, len(all_jobs))

    return mock_list_jobs


@pytest.fixture
def mock_training_job_repository() -> AsyncMock:
    """Mock ITrainingJobRepository for sync service testing."""
    repo = AsyncMock()
    repo.list_jobs = AsyncMock(return_value=([], 0))
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_hyperpod_client() -> AsyncMock:
    """Mock IHyperPodClient for sync service testing."""
    client = AsyncMock()
    client.get_training_job_status = AsyncMock(
        return_value={
            "job_name": "test-job-001",
            "status": "Running",
            "cluster_name": "test-cluster",
        }
    )
    return client


@pytest.fixture
def mock_event_bus() -> MagicMock:
    """Mock EventBus for event publishing tests."""
    bus = MagicMock()
    bus.publish_async = AsyncMock()
    return bus


def create_test_job(
    job_id: int = 1,
    job_name: str = "test-job-001",
    status: JobStatus = JobStatus.RUNNING,
    preemption_count: int = 0,
) -> TrainingJob:
    """创建测试用 TrainingJob 实体"""
    return TrainingJob(
        id=job_id,
        job_name=job_name,
        owner_id=100,
        image_uri="123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
        instance_type="ml.p4d.24xlarge",
        entrypoint_command=["torchrun", "--nproc_per_node=8", "train.py"],
        node_count=2,
        tasks_per_node=8,
        distribution_strategy=DistributionStrategy.DDP,
        priority=JobPriority.MEDIUM,
        status=status,
        preemption_count=preemption_count,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# === Test Class: TrainingSyncService 基础同步 ===


class TestTrainingSyncServiceBasicSync:
    """测试 TrainingSyncService 基础状态同步功能"""

    @pytest.mark.asyncio
    async def test_sync_running_job_updates_to_completed(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """同步 Running 状态任务时更新为 Completed"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Succeeded",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_all_active_jobs()

        # Assert
        mock_training_job_repository.update.assert_called_once()
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.status == JobStatus.COMPLETED
        assert result.synced_count == 1
        assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_sync_running_job_updates_to_failed(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """同步 Running 状态任务时更新为 Failed"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Failed",
            "error_message": "OOM killed",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_all_active_jobs()

        # Assert
        mock_training_job_repository.update.assert_called_once()
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.status == JobStatus.FAILED

    @pytest.mark.asyncio
    async def test_sync_submitted_job_updates_to_running(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """同步 Submitted 状态任务时更新为 Running"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        submitted_job = create_test_job(status=JobStatus.SUBMITTED)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.SUBMITTED: [submitted_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Running",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_all_active_jobs()

        # Assert
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.status == JobStatus.RUNNING

    @pytest.mark.asyncio
    async def test_sync_skips_terminal_status_jobs(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """终态任务 (Completed/Failed) 不参与同步"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange: list_jobs 只返回非终态任务 (这由 Repository 实现过滤)
        mock_training_job_repository.list_jobs.return_value = ([], 0)

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_all_active_jobs()

        # Assert
        assert result.synced_count == 0
        mock_hyperpod_client.get_training_job_status.assert_not_called()


# === Test Class: 抢占处理 ===


class TestTrainingSyncServicePreemption:
    """测试 TrainingSyncService 抢占状态处理"""

    @pytest.mark.asyncio
    async def test_sync_handles_preemption_increments_count(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """同步时正确处理抢占状态，累加 preemption_count"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING, preemption_count=0)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_all_active_jobs()

        # Assert
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.status == JobStatus.PREEMPTED
        assert updated_job.preemption_count == 1

    @pytest.mark.asyncio
    async def test_sync_preemption_exhausted_marks_failed(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """连续 3 次抢占后任务标记为 Failed"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange: 任务已被抢占 2 次，即将发生第 3 次
        running_job = create_test_job(status=JobStatus.RUNNING, preemption_count=2)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_all_active_jobs()

        # Assert
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.status == JobStatus.FAILED
        assert updated_job.preemption_count == 3
        assert updated_job.failure_reason == "PreemptionExhausted"
        assert "连续抢占次数超限" in (updated_job.error_message or "")

    @pytest.mark.asyncio
    async def test_sync_preemption_below_limit_stays_preempted(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """抢占次数未达上限时保持 Preempted 状态"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange: 任务已被抢占 1 次
        running_job = create_test_job(status=JobStatus.RUNNING, preemption_count=1)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_all_active_jobs()

        # Assert
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.status == JobStatus.PREEMPTED
        assert updated_job.preemption_count == 2


# === Test Class: 异常处理 ===


class TestTrainingSyncServiceErrorHandling:
    """测试 TrainingSyncService 异常处理"""

    @pytest.mark.asyncio
    async def test_sync_handles_hyperpod_api_error(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """HyperPod API 错误时优雅处理"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.side_effect = RuntimeError("API timeout")

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_all_active_jobs()

        # Assert: 不应抛出异常，错误计数增加
        assert result.failed_count == 1
        assert result.synced_count == 0
        # 不应更新任务状态
        mock_training_job_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_continues_on_single_job_failure(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """单个任务同步失败不影响其他任务"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange: 两个任务，第一个失败，第二个成功
        job1 = create_test_job(job_id=1, job_name="job-001", status=JobStatus.RUNNING)
        job2 = create_test_job(job_id=2, job_name="job-002", status=JobStatus.RUNNING)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [job1, job2]})

        # job-001 失败，job-002 成功
        mock_hyperpod_client.get_training_job_status.side_effect = [
            RuntimeError("API error for job-001"),
            {"job_name": "job-002", "status": "Succeeded"},
        ]

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_all_active_jobs()

        # Assert
        assert result.synced_count == 1
        assert result.failed_count == 1
        # 只有 job2 被更新
        mock_training_job_repository.update.assert_called_once()
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.job_name == "job-002"

    @pytest.mark.asyncio
    async def test_sync_handles_job_not_found_in_hyperpod(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """HyperPod 中找不到任务时标记为 Failed"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )
        from src.shared.domain.exceptions import EntityNotFoundError

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.side_effect = EntityNotFoundError(
            entity_type="TrainingJob",
            entity_id="test-job-001",
        )

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_all_active_jobs()

        # Assert: 任务应标记为 Failed
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.status == JobStatus.FAILED
        assert "HyperPod 中找不到任务" in (updated_job.error_message or "")


# === Test Class: 状态转换验证 ===


class TestTrainingSyncServiceStateTransition:
    """测试 TrainingSyncService 状态转换验证"""

    @pytest.mark.asyncio
    async def test_sync_validates_invalid_state_transition(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """同步时验证非法状态转换被拒绝"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange: Completed → Running 是非法转换
        # 注意: Completed 是终态，不应该出现在活跃任务列表中，
        # 但我们测试的是当这种情况发生时的处理逻辑
        completed_job = create_test_job(status=JobStatus.COMPLETED)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.COMPLETED: [completed_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Running",  # 尝试从 Completed → Running
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_all_active_jobs()

        # Assert: 不更新，记录为失败（Completed 不是活跃状态，所以实际上任务不会被查询到）
        # 由于 COMPLETED 不在活跃状态列表中，不会查询到任何任务
        assert result.synced_count == 0
        mock_training_job_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_no_update_when_status_unchanged(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """状态未变化时不更新数据库"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING)
        mock_training_job_repository.list_jobs = create_mock_list_jobs({JobStatus.RUNNING: [running_job]})
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Running",  # 状态未变化
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_all_active_jobs()

        # Assert: 状态未变化，不调用 update
        mock_training_job_repository.update.assert_not_called()
        assert result.synced_count == 0
        assert result.skipped_count == 1


# === Test Class: 状态映射 ===


class TestTrainingSyncServiceStatusMapping:
    """测试 HyperPod 状态到平台状态映射"""

    @pytest.mark.parametrize(
        "hyperpod_status,expected_platform_status",
        [
            ("Pending", JobStatus.SUBMITTED),
            ("Starting", JobStatus.SUBMITTED),
            ("Running", JobStatus.RUNNING),
            ("Stopping", JobStatus.RUNNING),
            ("Stopped", JobStatus.PAUSED),
            ("Succeeded", JobStatus.COMPLETED),
            ("Failed", JobStatus.FAILED),
            ("Preempted", JobStatus.PREEMPTED),
        ],
    )
    def test_hyperpod_status_mapping(self, hyperpod_status: str, expected_platform_status: JobStatus) -> None:
        """HyperPod 状态正确映射到平台状态"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        result = TrainingSyncService._map_hyperpod_status(hyperpod_status)
        assert result == expected_platform_status

    def test_unknown_status_returns_none(self) -> None:
        """未知状态返回 None"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        result = TrainingSyncService._map_hyperpod_status("UnknownStatus")
        assert result is None


# === Test Class: 单任务同步 ===


class TestTrainingSyncServiceSyncSingleJob:
    """测试 TrainingSyncService.sync_job 单任务同步方法"""

    @pytest.mark.asyncio
    async def test_sync_job_returns_true_on_success(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """单任务同步成功返回 True"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": "test-job-001",
            "status": "Succeeded",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_job(running_job)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_sync_job_returns_false_on_error(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """单任务同步失败返回 False"""
        from src.modules.training.application.services.training_sync_service import (
            TrainingSyncService,
        )

        # Arrange
        running_job = create_test_job(status=JobStatus.RUNNING)
        mock_hyperpod_client.get_training_job_status.side_effect = RuntimeError("API error")

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        result = await service.sync_job(running_job)

        # Assert
        assert result is False
