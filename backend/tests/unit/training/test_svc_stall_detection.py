"""训练任务停滞检测服务单元测试 - TDD Red-Green-Refactor

T037c: 训练任务停滞检测服务
- 监控 Loss 指标变化率
- 停滞判定逻辑
- 告警通知机制

参考: spec.md FR-022 训练任务停滞检测机制
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

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


# === Test Class: 停滞检测核心逻辑 ===


class TestStallDetectionServiceCore:
    """测试 StallDetectionService 停滞检测核心逻辑"""

    @pytest.mark.asyncio
    async def test_detect_stall_when_loss_unchanged(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """Loss 指标 30 分钟无变化时检测为停滞"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # 30 分钟内 Loss 没有变化
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=0.5),
            MetricPoint(timestamp=now - timedelta(minutes=20), value=0.5),
            MetricPoint(timestamp=now - timedelta(minutes=10), value=0.5),
            MetricPoint(timestamp=now, value=0.5),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert
        assert result.is_stalled is True
        assert result.metric_name == "loss"
        assert result.change_rate == 0.0

    @pytest.mark.asyncio
    async def test_no_stall_when_loss_decreasing(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """Loss 正常下降时不判定为停滞"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Loss 从 1.0 下降到 0.5 (50% 变化)
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=1.0),
            MetricPoint(timestamp=now - timedelta(minutes=20), value=0.8),
            MetricPoint(timestamp=now - timedelta(minutes=10), value=0.6),
            MetricPoint(timestamp=now, value=0.5),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert
        assert result.is_stalled is False
        assert result.change_rate > 0.001  # 大于阈值

    @pytest.mark.asyncio
    async def test_stall_with_tiny_change(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """微小变化 (<0.1%) 也判定为停滞"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Loss 从 0.5 变为 0.50005 (0.01% 变化)
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=0.5),
            MetricPoint(timestamp=now, value=0.50005),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert
        assert result.is_stalled is True
        assert result.change_rate < 0.001  # 小于阈值


# === Test Class: 配置和指标选择 ===


class TestStallDetectionServiceConfig:
    """测试 StallDetectionService 配置和指标选择"""

    @pytest.mark.asyncio
    async def test_use_custom_primary_metric(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """用户指定主指标时使用该指标"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionConfig,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Accuracy 指标无变化
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=0.95),
            MetricPoint(timestamp=now, value=0.95),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )
        config = StallDetectionConfig(primary_metric="accuracy")

        # Act
        result = await service.check_job_stall(job, config=config)

        # Assert
        assert result.metric_name == "accuracy"
        # 验证调用了正确的指标名
        call_args = mock_metrics_service.get_metric_history.call_args
        assert call_args.kwargs["job_id"] == job.id
        assert call_args.kwargs["metric_name"] == "accuracy"

    @pytest.mark.asyncio
    async def test_skip_detection_when_disabled(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """禁用停滞检测时跳过检查"""
        from src.modules.training.application.services.stall_detection_service import (
            StallDetectionConfig,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        config = StallDetectionConfig(enabled=False)

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job, config=config)

        # Assert
        assert result.is_stalled is False
        assert result.skipped is True
        mock_metrics_service.get_metric_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_detection_window(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """自定义检测窗口生效"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionConfig,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=60), value=0.5),
            MetricPoint(timestamp=now, value=0.5),
        ]

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
    async def test_custom_change_rate_threshold(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """自定义变化率阈值生效"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionConfig,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # 0.5% 变化率
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=1.0),
            MetricPoint(timestamp=now, value=0.995),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # 默认阈值 0.1% (0.001) - 应该不算停滞
        result_default = await service.check_job_stall(job)
        assert result_default.is_stalled is False

        # 自定义阈值 1% (0.01) - 应该算停滞
        config = StallDetectionConfig(change_rate_threshold=0.01)
        result_custom = await service.check_job_stall(job, config=config)
        assert result_custom.is_stalled is True


# === Test Class: 指标回退选择 ===


class TestStallDetectionServiceMetricFallback:
    """测试指标回退选择逻辑"""

    @pytest.mark.asyncio
    async def test_fallback_to_accuracy_when_loss_unavailable(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """Loss 不可用时回退到 Accuracy"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Loss 返回空，Accuracy 有数据
        mock_metrics_service.get_metric_history.side_effect = [
            [],  # loss
            [  # accuracy
                MetricPoint(timestamp=now - timedelta(minutes=30), value=0.9),
                MetricPoint(timestamp=now, value=0.9),
            ],
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert
        assert result.metric_name == "accuracy"

    @pytest.mark.asyncio
    async def test_fallback_to_perplexity_when_both_unavailable(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """Loss 和 Accuracy 都不可用时回退到 Perplexity"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING)
        now = datetime.utcnow()

        # Loss 和 Accuracy 返回空，Perplexity 有数据
        mock_metrics_service.get_metric_history.side_effect = [
            [],  # loss
            [],  # accuracy
            [  # perplexity
                MetricPoint(timestamp=now - timedelta(minutes=30), value=10.0),
                MetricPoint(timestamp=now, value=10.0),
            ],
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        result = await service.check_job_stall(job)

        # Assert
        assert result.metric_name == "perplexity"

    @pytest.mark.asyncio
    async def test_no_stall_when_all_metrics_unavailable(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """所有指标都不可用时返回无法判定"""
        from src.modules.training.application.services.stall_detection_service import (
            StallDetectionService,
        )

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
        assert "no_metrics" in (result.skip_reason or "")


# === Test Class: 批量检测 ===


class TestStallDetectionServiceBatch:
    """测试批量停滞检测"""

    @pytest.mark.asyncio
    async def test_check_all_running_jobs(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
    ) -> None:
        """检查所有 Running 状态任务"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallDetectionService,
        )

        # Arrange
        job1 = create_test_job(job_id=1, job_name="job-001", status=JobStatus.RUNNING)
        job2 = create_test_job(job_id=2, job_name="job-002", status=JobStatus.RUNNING)

        # 模拟 list_jobs 返回两个 RUNNING 任务
        async def mock_list_jobs(
            owner_id=None, status=None, priority=None, **kwargs
        ):
            if status == JobStatus.RUNNING:
                return ([job1, job2], 2)
            return ([], 0)

        mock_training_job_repository.list_jobs = mock_list_jobs

        now = datetime.utcnow()
        # 两个任务都停滞
        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=0.5),
            MetricPoint(timestamp=now, value=0.5),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
        )

        # Act
        results = await service.check_all_running_jobs()

        # Assert
        assert len(results) == 2
        assert all(r.is_stalled for r in results)


# === Test Class: 告警功能 ===


class TestStallDetectionServiceAlert:
    """测试停滞告警功能"""

    @pytest.mark.asyncio
    async def test_send_alert_on_stall_detected(
        self,
        mock_training_job_repository: AsyncMock,
        mock_metrics_service: AsyncMock,
        mock_notification_service: AsyncMock,
    ) -> None:
        """检测到停滞时发送告警"""
        from src.modules.training.application.services.stall_detection_service import (
            MetricPoint,
            StallCheckResult,
            StallDetectionService,
        )

        # Arrange
        job = create_test_job(status=JobStatus.RUNNING, owner_id=100)
        now = datetime.utcnow()

        mock_metrics_service.get_metric_history.return_value = [
            MetricPoint(timestamp=now - timedelta(minutes=30), value=0.5),
            MetricPoint(timestamp=now, value=0.5),
        ]

        service = StallDetectionService(
            training_job_repository=mock_training_job_repository,
            metrics_service=mock_metrics_service,
            notification_service=mock_notification_service,
        )

        # Act
        result = await service.check_job_stall(job)
        if result.is_stalled:
            await service.send_stall_alert(job, result)

        # Assert
        mock_notification_service.send_alert.assert_called_once()
        call_args = mock_notification_service.send_alert.call_args

        # 验证告警内容
        alert = call_args[1] if call_args[1] else call_args[0][0]
        assert job.job_name in str(alert)
        assert job.owner_id == 100


# === Test Class: 变化率计算 ===


class TestStallDetectionServiceChangeRate:
    """测试变化率计算逻辑"""

    def test_calculate_change_rate_normal(self) -> None:
        """正常情况下的变化率计算"""
        from src.modules.training.application.services.stall_detection_service import (
            StallDetectionService,
        )

        # 从 1.0 下降到 0.5，变化率为 50%
        rate = StallDetectionService._calculate_change_rate([1.0, 0.75, 0.5])
        assert abs(rate - 0.5) < 0.001

    def test_calculate_change_rate_unchanged(self) -> None:
        """值未变化时变化率为 0"""
        from src.modules.training.application.services.stall_detection_service import (
            StallDetectionService,
        )

        rate = StallDetectionService._calculate_change_rate([0.5, 0.5, 0.5])
        assert rate == 0.0

    def test_calculate_change_rate_from_zero(self) -> None:
        """起始值为 0 时的特殊处理"""
        from src.modules.training.application.services.stall_detection_service import (
            StallDetectionService,
        )

        # 从 0 变为非 0，返回绝对值
        rate = StallDetectionService._calculate_change_rate([0.0, 0.5])
        assert rate == 0.5

    def test_calculate_change_rate_insufficient_data(self) -> None:
        """数据不足时返回高变化率（不判定为停滞）"""
        from src.modules.training.application.services.stall_detection_service import (
            StallDetectionService,
        )

        # 只有一个数据点
        rate = StallDetectionService._calculate_change_rate([0.5])
        assert rate == 1.0  # 返回高变化率

        # 空列表
        rate = StallDetectionService._calculate_change_rate([])
        assert rate == 1.0
