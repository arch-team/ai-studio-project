"""停滞检测机制集成测试 (T037e)

测试场景:
1. 模拟 Loss 指标 30 分钟内变化率 <0.1%，验证停滞告警触发
2. 验证用户指定主指标 (Accuracy) 时的检测逻辑
3. 验证禁用停滞检测配置生效
4. 验证告警通知发送
5. 验证主指标选择逻辑 (Loss → Accuracy → Perplexity)

依赖: StallDetectionService (T037c)
参考: spec.md FR-022 训练任务停滞检测机制
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.training.application.interfaces import Alert, MetricPoint
from src.modules.training.application.services.stall_detection_service import (
    StallDetectionConfig,
    StallDetectionService,
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
    owner_id: int = 100,
    latest_loss: Decimal | None = Decimal("0.5"),
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
        latest_loss=latest_loss,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def create_stalled_metric_history(now: datetime, value: float = 0.5, window_minutes: int = 30) -> list[MetricPoint]:
    """创建停滞指标历史（值保持不变）"""
    return [
        MetricPoint(timestamp=now - timedelta(minutes=window_minutes), value=value),
        MetricPoint(timestamp=now - timedelta(minutes=window_minutes * 2 // 3), value=value),
        MetricPoint(timestamp=now - timedelta(minutes=window_minutes // 3), value=value),
        MetricPoint(timestamp=now, value=value),
    ]


def create_healthy_metric_history(
    now: datetime, start_value: float = 1.0, end_value: float = 0.5, window_minutes: int = 30
) -> list[MetricPoint]:
    """创建健康指标历史（值正常变化）"""
    step = (start_value - end_value) / 3
    return [
        MetricPoint(timestamp=now - timedelta(minutes=window_minutes), value=start_value),
        MetricPoint(timestamp=now - timedelta(minutes=window_minutes * 2 // 3), value=start_value - step),
        MetricPoint(timestamp=now - timedelta(minutes=window_minutes // 3), value=start_value - 2 * step),
        MetricPoint(timestamp=now, value=end_value),
    ]


@pytest.fixture
def mock_training_job_repository() -> AsyncMock:
    """Mock ITrainingJobRepository"""
    repo = AsyncMock()
    repo.list_jobs = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_metrics_service() -> AsyncMock:
    """Mock IMetricsService"""
    service = AsyncMock()
    service.get_metric_history = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_notification_service() -> AsyncMock:
    """Mock INotificationService"""
    service = AsyncMock()
    service.send_alert = AsyncMock()
    return service


# === Test Class: 停滞检测机制场景 ===


@pytest.mark.integration
class TestStallDetection:
    """停滞检测机制集成测试

    验证 FR-022 停滞检测功能
    """

    @pytest.mark.asyncio
    async def test_stall_alert_triggered_on_unchanged_loss(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
        mock_notification_service: AsyncMock,
    ) -> None:
        """场景1: Loss 30分钟无变化触发告警

        模拟 Loss 指标在 30 分钟内变化率 <0.1%，
        验证系统正确检测到停滞并触发告警。
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING, owner_id=100)
        now = datetime.utcnow()

        # 30分钟内 Loss 保持 0.5 不变
        mock_metrics_service.get_metric_history.return_value = create_stalled_metric_history(
            now, value=0.5, window_minutes=30
        )

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
            notification_service=mock_notification_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert: 检测到停滞
        assert result.is_stalled is True
        assert result.metric_name == "loss"
        assert result.change_rate == 0.0
        assert result.detection_window_minutes == 30

        # 发送告警
        await service.send_stall_alert(job, result)
        mock_notification_service.send_alert.assert_called_once()

        # 验证告警内容
        alert_call = mock_notification_service.send_alert.call_args
        alert: Alert = alert_call[0][0]
        assert job.job_name in alert.title
        assert job.owner_id in alert.recipient_ids
        assert alert.severity == "warning"

    @pytest.mark.asyncio
    async def test_custom_primary_metric_accuracy(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """场景2: 用户指定 Accuracy 作为主指标

        当用户配置 primary_metric='accuracy' 时，
        应该使用 Accuracy 指标进行停滞检测。
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Accuracy 保持 0.95 不变
        mock_metrics_service.get_metric_history.return_value = create_stalled_metric_history(
            now, value=0.95, window_minutes=30
        )

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )
        config = StallDetectionConfig(primary_metric="accuracy")

        # Act
        result = await service.check_job_stall(job, config=config)

        # Assert
        assert result.is_stalled is True
        assert result.metric_name == "accuracy"
        assert result.change_rate == 0.0

        # 验证调用了正确的指标
        call_kwargs = mock_metrics_service.get_metric_history.call_args.kwargs
        assert call_kwargs["metric_name"] == "accuracy"

    @pytest.mark.asyncio
    async def test_disabled_stall_detection(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """场景3: 禁用停滞检测配置生效

        当 enabled=False 时，应该跳过停滞检测。
        适用于 GAN/RL 等训练模式。
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )
        config = StallDetectionConfig(enabled=False)

        # Act
        result = await service.check_job_stall(job, config=config)

        # Assert
        assert result.is_stalled is False
        assert result.skipped is True
        assert result.skip_reason == "disabled"

        # 验证没有调用指标服务
        mock_metrics_service.get_metric_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_alert_recipients(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
        mock_notification_service: AsyncMock,
    ) -> None:
        """场景4: 告警发送给正确的接收者

        告警应该发送给任务所有者。
        """
        # Arrange
        owner_id = 123
        job = create_test_job(status=JobStatus.RUNNING, owner_id=owner_id)
        now = datetime.utcnow()

        mock_metrics_service.get_metric_history.return_value = create_stalled_metric_history(
            now, value=0.5, window_minutes=30
        )

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
            notification_service=mock_notification_service,
        )

        # Act
        result = await service.check_job_stall(job)
        await service.send_stall_alert(job, result)

        # Assert
        alert_call = mock_notification_service.send_alert.call_args
        alert: Alert = alert_call[0][0]
        assert owner_id in alert.recipient_ids
        assert alert.metadata is not None
        assert alert.metadata["job_id"] == job.id
        assert alert.metadata["job_name"] == job.job_name

    @pytest.mark.asyncio
    async def test_metric_fallback_selection(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """场景5: Loss → Accuracy → Perplexity 自动选择

        当 Loss 不可用时，自动回退到 Accuracy，
        如果 Accuracy 也不可用，则回退到 Perplexity。
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Loss 不可用，Accuracy 有数据
        mock_metrics_service.get_metric_history.side_effect = [
            [],  # loss - 无数据
            create_stalled_metric_history(now, value=0.9, window_minutes=30),  # accuracy
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert: 使用了 Accuracy
        assert result.metric_name == "accuracy"
        assert result.is_stalled is True

    @pytest.mark.asyncio
    async def test_metric_fallback_to_perplexity(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """场景5b: Loss 和 Accuracy 都不可用时回退到 Perplexity"""
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Loss 和 Accuracy 不可用，Perplexity 有数据
        mock_metrics_service.get_metric_history.side_effect = [
            [],  # loss - 无数据
            [],  # accuracy - 无数据
            create_stalled_metric_history(now, value=10.0, window_minutes=30),  # perplexity
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert: 使用了 Perplexity
        assert result.metric_name == "perplexity"
        assert result.is_stalled is True


# === Test Class: 健康任务场景 ===


@pytest.mark.integration
class TestHealthyTraining:
    """健康训练任务场景（不应触发停滞告警）"""

    @pytest.mark.asyncio
    async def test_no_alert_when_loss_decreasing(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
        mock_notification_service: AsyncMock,
    ) -> None:
        """Loss 正常下降时不触发告警"""
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Loss 从 1.0 下降到 0.5 (50% 变化)
        mock_metrics_service.get_metric_history.return_value = create_healthy_metric_history(
            now, start_value=1.0, end_value=0.5
        )

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
            notification_service=mock_notification_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert
        assert result.is_stalled is False
        assert result.change_rate > 0.001  # 大于阈值

    @pytest.mark.asyncio
    async def test_no_alert_when_accuracy_improving(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """Accuracy 正常提升时不触发告警"""
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Accuracy 从 0.7 提升到 0.9 (约 29% 变化)
        mock_metrics_service.get_metric_history.return_value = create_healthy_metric_history(
            now, start_value=0.7, end_value=0.9
        )

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )
        config = StallDetectionConfig(primary_metric="accuracy")

        # Act
        result = await service.check_job_stall(job, config=config)

        # Assert
        assert result.is_stalled is False


# === Test Class: 配置验证 ===


@pytest.mark.integration
class TestStallDetectionConfig:
    """停滞检测配置验证"""

    @pytest.mark.asyncio
    async def test_custom_window_60_minutes(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """自定义 60 分钟检测窗口"""
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        mock_metrics_service.get_metric_history.return_value = create_stalled_metric_history(
            now, value=0.5, window_minutes=60
        )

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )
        config = StallDetectionConfig(detection_window_minutes=60)

        # Act
        result = await service.check_job_stall(job, config=config)

        # Assert
        assert result.detection_window_minutes == 60

    @pytest.mark.asyncio
    async def test_custom_threshold_1_percent(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """自定义 1% 变化率阈值

        当变化率阈值设为 1% 时，0.5% 的变化应该被判定为停滞。
        """
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # 0.5% 变化 (从 1.0 到 0.995)
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=1.0),
            MetricPoint(timestamp=now, value=0.995),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # 默认阈值 (0.1%) - 不应停滞
        result_default = await service.check_job_stall(job)
        assert result_default.is_stalled is False

        # 自定义阈值 1% - 应该停滞
        config = StallDetectionConfig(change_rate_threshold=0.01)
        result_custom = await service.check_job_stall(job, config=config)
        assert result_custom.is_stalled is True


# === Test Class: 边界条件 ===


@pytest.mark.integration
class TestStallDetectionEdgeCases:
    """停滞检测边界条件"""

    @pytest.mark.asyncio
    async def test_no_metrics_available(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """所有指标都不可用时跳过检测"""
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)

        # 所有指标返回空
        mock_metrics_service.get_metric_history.return_value = []

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert
        assert result.is_stalled is False
        assert result.skipped is True
        assert "no_metrics" in result.skip_reason

    @pytest.mark.asyncio
    async def test_insufficient_data_points(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """数据点不足时不判定为停滞"""
        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # 只有一个数据点
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now, value=0.5),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert: 数据不足，不应判定为停滞
        assert result.is_stalled is False
        # change_rate 应该返回高值 (1.0) 表示数据不足

    @pytest.mark.asyncio
    async def test_batch_check_multiple_jobs(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """批量检查多个任务"""
        # Arrange
        job1 = create_test_job(job_id=1, job_name="job-001", status=JobStatus.RUNNING)
        job2 = create_test_job(job_id=2, job_name="job-002", status=JobStatus.RUNNING)
        job3 = create_test_job(job_id=3, job_name="job-003", status=JobStatus.RUNNING)
        now = datetime.utcnow()

        async def mock_list_jobs(status=None, **kwargs):
            if status == JobStatus.RUNNING:
                return ([job1, job2, job3], 3)
            return ([], 0)

        mock_training_job_repository.list_jobs = mock_list_jobs

        # job1 停滞，job2 健康，job3 无数据
        mock_metrics_service.get_metric_history.side_effect = [
            create_stalled_metric_history(now, value=0.5),  # job1
            create_healthy_metric_history(now, 1.0, 0.5),  # job2
            [],  # job3
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        results = await service.check_all_running_jobs()

        # Assert
        assert len(results) == 3
        stalled_jobs = [r for r in results if r.is_stalled]
        healthy_jobs = [r for r in results if not r.is_stalled and not r.skipped]
        skipped_jobs = [r for r in results if r.skipped]

        assert len(stalled_jobs) == 1
        assert len(healthy_jobs) == 1
        assert len(skipped_jobs) == 1
