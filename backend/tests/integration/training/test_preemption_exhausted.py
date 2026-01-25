"""抢占连续失败转 Failed 状态集成测试 (T037d)

测试场景:
1. 模拟训练任务被连续抢占 3 次，验证状态转为 Failed
2. 验证 preemption_count 计数器正确累加
3. 验证失败分类 failureCategory = "PreemptionExhausted"
4. 验证自动停止重新排队
5. 验证告警通知发送

依赖: TrainingSyncService (T037)
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.training.application.services.training_sync_service import (
    MAX_PREEMPTION_COUNT,
    TrainingSyncService,
)
from src.modules.training.domain.entities.training_job import TrainingJob
from src.modules.training.domain.value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
)

# === Fixtures ===


def create_test_job(
    job_id: int = 1,
    job_name: str = "test-training-job-001",
    status: JobStatus = JobStatus.RUNNING,
    preemption_count: int = 0,
    owner_id: int = 100,
) -> TrainingJob:
    """创建测试用 TrainingJob 实体"""
    return TrainingJob(
        id=job_id,
        job_name=job_name,
        owner_id=owner_id,
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


@pytest.fixture
def mock_training_job_repository() -> AsyncMock:
    """Mock ITrainingJobRepository"""
    repo = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_hyperpod_client() -> AsyncMock:
    """Mock IHyperPodClient"""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_notification_service() -> AsyncMock:
    """Mock 通知服务（用于告警测试）"""
    service = AsyncMock()
    service.send_alert = AsyncMock()
    return service


# === Test Class: 抢占连续失败场景 ===


@pytest.mark.integration
class TestPreemptionExhausted:
    """抢占连续失败转 Failed 状态集成测试

    验证 FR-004 连续抢占失败机制
    """

    @pytest.mark.asyncio
    async def test_job_fails_after_three_preemptions(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景1: 连续3次抢占后任务转 Failed

        模拟训练任务从 Running 状态经历 3 次抢占，
        验证最终状态为 FAILED，preemption_count = 3
        """
        # Arrange: 创建 Running 状态任务
        job = create_test_job(status=JobStatus.RUNNING, preemption_count=0)

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act: 模拟 3 次抢占
        for i in range(MAX_PREEMPTION_COUNT):
            # 重置 mock
            mock_hyperpod_client.get_training_job_status.return_value = {
                "job_name": job.job_name,
                "status": "Preempted",
            }

            # 执行同步
            await service.sync_job(job)

            # 验证中间状态
            if i < MAX_PREEMPTION_COUNT - 1:
                # 前 2 次抢占：状态应为 PREEMPTED
                assert job.preemption_count == i + 1
                # 重置状态为 RUNNING 以模拟重新调度
                job.status = JobStatus.RUNNING

        # Assert: 第 3 次抢占后应为 FAILED
        assert job.status == JobStatus.FAILED
        assert job.preemption_count == MAX_PREEMPTION_COUNT
        assert job.failure_reason == "PreemptionExhausted"

    @pytest.mark.asyncio
    async def test_preemption_count_increments_correctly(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景2: 验证 preemption_count 计数器正确累加

        每次抢占事件发生时，preemption_count 应 +1
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING, preemption_count=0)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act & Assert: 每次同步后验证计数器
        await service.sync_job(job)
        assert job.preemption_count == 1

        # 重置状态继续测试
        job.status = JobStatus.RUNNING
        await service.sync_job(job)
        assert job.preemption_count == 2

        # 第三次达到上限
        job.status = JobStatus.RUNNING
        await service.sync_job(job)
        assert job.preemption_count == 3

    @pytest.mark.asyncio
    async def test_failure_category_is_preemption_exhausted(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景3: 验证失败分类 failure_reason = 'PreemptionExhausted'

        当连续抢占次数达到上限时，failure_reason 应正确设置
        """
        # Arrange: 任务已被抢占 2 次
        job = create_test_job(status=JobStatus.RUNNING, preemption_count=2)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act: 第 3 次抢占
        await service.sync_job(job)

        # Assert
        assert job.status == JobStatus.FAILED
        assert job.failure_reason == "PreemptionExhausted"
        assert job.error_message is not None
        assert "连续抢占次数超限" in job.error_message
        assert f"{MAX_PREEMPTION_COUNT}" in job.error_message

    @pytest.mark.asyncio
    async def test_stops_requeue_after_exhausted(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景4: 验证自动停止重新排队

        当 failure_reason = 'PreemptionExhausted' 时，
        任务应处于终态 (FAILED)，不应再被同步服务处理
        """
        # Arrange: 创建已达抢占上限的任务
        job = create_test_job(status=JobStatus.RUNNING, preemption_count=2)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act: 触发第 3 次抢占
        await service.sync_job(job)

        # Assert: 任务应为终态
        assert job.status == JobStatus.FAILED
        assert job.is_terminal()

        # 验证终态任务不能再转换
        assert not job.can_transition_to(JobStatus.RUNNING)
        assert not job.can_transition_to(JobStatus.PREEMPTED)
        assert not job.can_transition_to(JobStatus.SUBMITTED)

    @pytest.mark.asyncio
    async def test_preemption_below_limit_allows_requeue(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景4b: 抢占次数未达上限时允许重新排队

        当 preemption_count < MAX_PREEMPTION_COUNT 时，
        任务应处于 PREEMPTED 状态，可以转换为 RUNNING
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING, preemption_count=1)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_job(job)

        # Assert: 任务应为 PREEMPTED（非终态）
        assert job.status == JobStatus.PREEMPTED
        assert job.preemption_count == 2
        assert not job.is_terminal()

        # 验证可以重新排队
        assert job.can_transition_to(JobStatus.RUNNING)
        assert job.can_resume()


# === Test Class: 告警通知场景 ===


@pytest.mark.integration
class TestPreemptionExhaustedAlert:
    """抢占失败告警通知测试

    验证 FR-004 告警通知功能
    注意: 当前实现中，告警功能尚未完全实现，这些测试标记为预留
    """

    @pytest.mark.skip(reason="告警服务尚未实现")
    @pytest.mark.asyncio
    async def test_alert_sent_on_preemption_exhausted(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        mock_notification_service: AsyncMock,
    ) -> None:
        """场景5: 验证告警通知发送

        当任务因连续抢占失败时，应发送告警通知给：
        - 任务所有者
        - 平台管理员
        """
        # TODO: 实现告警服务集成后完善此测试
        pass

    @pytest.mark.skip(reason="告警服务尚未实现")
    @pytest.mark.asyncio
    async def test_alert_includes_job_details(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        mock_notification_service: AsyncMock,
    ) -> None:
        """场景5b: 验证告警内容包含任务详情

        告警应包含：
        - 任务名称
        - 所有者信息
        - 抢占次数
        - 失败原因
        """
        # TODO: 实现告警服务集成后完善此测试
        pass


# === Test Class: 边界条件 ===


@pytest.mark.integration
class TestPreemptionEdgeCases:
    """抢占处理边界条件测试"""

    @pytest.mark.asyncio
    async def test_preemption_count_persisted_after_update(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """验证 preemption_count 在更新后正确持久化

        每次抢占后，update 方法应被调用以持久化状态
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING, preemption_count=0)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_job(job)

        # Assert: update 被调用，且传入的 job 有正确的 preemption_count
        mock_training_job_repository.update.assert_called_once()
        updated_job = mock_training_job_repository.update.call_args[0][0]
        assert updated_job.preemption_count == 1

    @pytest.mark.asyncio
    async def test_max_preemption_count_is_configurable_constant(self) -> None:
        """验证 MAX_PREEMPTION_COUNT 是可配置的常量

        确保系统使用配置的抢占上限而非硬编码值
        """
        assert MAX_PREEMPTION_COUNT == 3  # 当前配置值
        assert MAX_PREEMPTION_COUNT > 0  # 必须为正数

    @pytest.mark.asyncio
    async def test_preemption_from_different_running_states(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """验证从不同状态接收抢占事件

        PREEMPTED 状态也应该能接收抢占事件（如果重新调度后又被抢占）
        """
        # Arrange: 任务已在 PREEMPTED 状态（模拟刚被抢占）
        job = create_test_job(status=JobStatus.PREEMPTED, preemption_count=1)

        # 注意：PREEMPTED → PREEMPTED 不是有效转换
        # 应该先转换为 RUNNING，然后再被抢占
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        # Act
        await service.sync_job(job)

        # Assert: 状态相同，应该跳过（不是错误）
        # PREEMPTED → PREEMPTED 不会触发更新
        mock_training_job_repository.update.assert_not_called()
