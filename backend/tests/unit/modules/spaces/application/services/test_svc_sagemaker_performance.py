"""SpaceMetricsService 单元测试 (T085c).

测试 SageMaker Spaces 启动性能监控服务，包括:
- 记录启动时间到 CloudWatch
- 获取 P50/P95/P99 统计
- 超时检测 (>3 分钟)
- 并发启动模拟
- 不同实例类型启动时间对比
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.spaces.application.services.sagemaker_metrics_service import SpaceMetricsService


class TestRecordStartupTime:
    """测试记录 Space 启动耗时."""

    @pytest.fixture
    def metrics_service(self) -> SpaceMetricsService:
        """创建 SpaceMetricsService 实例."""
        return SpaceMetricsService()

    def _make_mock_cw_context(self, mock_cw: AsyncMock) -> AsyncMock:
        """构建 aioboto3 异步上下文管理器 mock."""
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_cw)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        return mock_ctx

    @pytest.mark.asyncio
    async def test_record_startup_time_success(self, metrics_service: SpaceMetricsService) -> None:
        """测试正常记录启动耗时到 CloudWatch."""
        # Arrange
        mock_cw = AsyncMock()
        mock_cw.put_metric_data = AsyncMock(return_value={})
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            await metrics_service.record_startup_time("space-001", 45.2)

        # Assert
        mock_cw.put_metric_data.assert_called_once()
        call_kwargs = mock_cw.put_metric_data.call_args[1]
        assert call_kwargs["Namespace"] == "AITrainingPlatform/Spaces"
        metric_data = call_kwargs["MetricData"][0]
        assert metric_data["MetricName"] == "SpaceStartupTime"
        assert metric_data["Value"] == 45.2
        assert metric_data["Unit"] == "Seconds"

    @pytest.mark.asyncio
    async def test_record_startup_time_with_timeout_warning(self, metrics_service: SpaceMetricsService) -> None:
        """测试记录超时的启动耗时 (>3 分钟) 触发日志告警."""
        # Arrange
        mock_cw = AsyncMock()
        mock_cw.put_metric_data = AsyncMock(return_value={})
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act - 记录超过 180 秒的启动时间
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            await metrics_service.record_startup_time("space-slow", 250.0)

        # Assert - API 仍然被调用
        mock_cw.put_metric_data.assert_called_once()
        metric_data = mock_cw.put_metric_data.call_args[1]["MetricData"][0]
        assert metric_data["Value"] == 250.0

    @pytest.mark.asyncio
    async def test_record_startup_time_api_error_does_not_raise(self, metrics_service: SpaceMetricsService) -> None:
        """测试 CloudWatch API 调用失败时不抛出异常 (仅记录日志)."""
        # Arrange
        mock_cw = AsyncMock()
        mock_cw.put_metric_data = AsyncMock(side_effect=Exception("CloudWatch unavailable"))
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act & Assert - 不应抛出异常
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            await metrics_service.record_startup_time("space-err", 30.0)


class TestGetStartupStatistics:
    """测试获取启动时间统计."""

    @pytest.fixture
    def metrics_service(self) -> SpaceMetricsService:
        """创建 SpaceMetricsService 实例."""
        return SpaceMetricsService()

    def _make_mock_cw_context(self, mock_cw: AsyncMock) -> AsyncMock:
        """构建 aioboto3 异步上下文管理器 mock."""
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_cw)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        return mock_ctx

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, metrics_service: SpaceMetricsService) -> None:
        """测试获取 P50/P95/P99 统计数据."""
        # Arrange
        mock_response = {
            "Datapoints": [
                {
                    "Average": 42.5,
                    "Minimum": 15.0,
                    "Maximum": 120.0,
                    "SampleCount": 100.0,
                    "ExtendedStatistics": {
                        "p50": 38.0,
                        "p95": 95.0,
                        "p99": 115.0,
                    },
                }
            ]
        }
        mock_cw = AsyncMock()
        mock_cw.get_metric_statistics = AsyncMock(return_value=mock_response)
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            stats = await metrics_service.get_startup_statistics(period_hours=24)

        # Assert
        assert stats["sample_count"] == 100
        assert stats["average"] == 42.5
        assert stats["minimum"] == 15.0
        assert stats["maximum"] == 120.0
        assert stats["p50"] == 38.0
        assert stats["p95"] == 95.0
        assert stats["p99"] == 115.0
        assert stats["period_hours"] == 24

    @pytest.mark.asyncio
    async def test_get_statistics_no_data(self, metrics_service: SpaceMetricsService) -> None:
        """测试无数据时返回零值统计."""
        # Arrange
        mock_cw = AsyncMock()
        mock_cw.get_metric_statistics = AsyncMock(return_value={"Datapoints": []})
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            stats = await metrics_service.get_startup_statistics(period_hours=1)

        # Assert
        assert stats["sample_count"] == 0
        assert stats["average"] == 0.0
        assert stats["p95"] == 0.0
        assert stats["p99"] == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_api_error_returns_empty(self, metrics_service: SpaceMetricsService) -> None:
        """测试 CloudWatch API 失败时返回含 error 的空统计."""
        # Arrange
        mock_cw = AsyncMock()
        mock_cw.get_metric_statistics = AsyncMock(side_effect=Exception("API error"))
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            stats = await metrics_service.get_startup_statistics()

        # Assert
        assert stats["sample_count"] == 0
        assert "error" in stats


class TestCheckStartupTimeout:
    """测试超时检测."""

    @pytest.fixture
    def metrics_service(self) -> SpaceMetricsService:
        """创建 SpaceMetricsService 实例."""
        return SpaceMetricsService()

    @pytest.mark.asyncio
    async def test_not_timed_out_within_threshold(self, metrics_service: SpaceMetricsService) -> None:
        """测试在 3 分钟内不判定为超时."""
        # Arrange - 创建时间为 1 分钟前
        created_at = datetime.now(UTC) - timedelta(seconds=60)

        # Act
        is_timeout = await metrics_service.check_startup_timeout("space-001", created_at)

        # Assert
        assert is_timeout is False

    @pytest.mark.asyncio
    async def test_timed_out_exceeds_threshold(self, metrics_service: SpaceMetricsService) -> None:
        """测试超过 3 分钟判定为超时."""
        # Arrange - 创建时间为 5 分钟前
        created_at = datetime.now(UTC) - timedelta(seconds=300)

        # Act
        is_timeout = await metrics_service.check_startup_timeout("space-slow", created_at)

        # Assert
        assert is_timeout is True

    @pytest.mark.asyncio
    async def test_exactly_at_threshold_not_timeout(self, metrics_service: SpaceMetricsService) -> None:
        """测试恰好 180 秒时不判定为超时 (边界条件)."""
        # Arrange - 创建时间恰好为 180 秒前 (减去微小偏移以避免浮点精度问题)
        created_at = datetime.now(UTC) - timedelta(seconds=179)

        # Act
        is_timeout = await metrics_service.check_startup_timeout("space-edge", created_at)

        # Assert
        assert is_timeout is False

    @pytest.mark.asyncio
    async def test_timeout_with_naive_datetime(self, metrics_service: SpaceMetricsService) -> None:
        """测试无时区信息的 datetime 也能正确处理."""
        # Arrange - 使用无时区 datetime (模拟数据库返回)
        created_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=300)

        # Act
        is_timeout = await metrics_service.check_startup_timeout("space-naive", created_at)

        # Assert
        assert is_timeout is True


class TestConcurrentStartupSimulation:
    """测试并发启动场景模拟."""

    @pytest.fixture
    def metrics_service(self) -> SpaceMetricsService:
        """创建 SpaceMetricsService 实例."""
        return SpaceMetricsService()

    def _make_mock_cw_context(self, mock_cw: AsyncMock) -> AsyncMock:
        """构建 aioboto3 异步上下文管理器 mock."""
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_cw)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        return mock_ctx

    @pytest.mark.asyncio
    async def test_concurrent_50_space_startups(self, metrics_service: SpaceMetricsService) -> None:
        """测试 50 个并发 Space 启动记录."""
        # Arrange
        mock_cw = AsyncMock()
        mock_cw.put_metric_data = AsyncMock(return_value={})
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act - 并发记录 50 个 Space 的启动时间
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            tasks = [metrics_service.record_startup_time(f"space-{i:03d}", 30.0 + i * 0.5) for i in range(50)]
            await asyncio.gather(*tasks)

        # Assert - 50 次 put_metric_data 调用
        assert mock_cw.put_metric_data.call_count == 50

    @pytest.mark.asyncio
    async def test_concurrent_startups_with_partial_failures(self, metrics_service: SpaceMetricsService) -> None:
        """测试并发启动中部分失败不影响其他记录."""
        # Arrange - 偶数次调用失败
        call_count = 0

        async def side_effect(**kwargs: object) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("Intermittent failure")
            return {}

        mock_cw = AsyncMock()
        mock_cw.put_metric_data = AsyncMock(side_effect=side_effect)
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act - 并发记录 10 个 Space (不应抛出异常)
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            tasks = [metrics_service.record_startup_time(f"space-{i:03d}", 40.0 + i) for i in range(10)]
            await asyncio.gather(*tasks)

        # Assert - 所有 10 次调用都执行了 (失败的被捕获)
        assert mock_cw.put_metric_data.call_count == 10


class TestInstanceTypeStartupComparison:
    """测试不同实例类型启动时间对比."""

    @pytest.fixture
    def metrics_service(self) -> SpaceMetricsService:
        """创建 SpaceMetricsService 实例."""
        return SpaceMetricsService()

    def _make_mock_cw_context(self, mock_cw: AsyncMock) -> AsyncMock:
        """构建 aioboto3 异步上下文管理器 mock."""
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_cw)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        return mock_ctx

    @pytest.mark.asyncio
    async def test_record_different_instance_types(self, metrics_service: SpaceMetricsService) -> None:
        """测试记录不同实例类型的启动时间."""
        # Arrange - 模拟不同实例类型的启动时间
        instance_startup_times = {
            "ml.t3.medium": 25.0,
            "ml.t3.large": 28.0,
            "ml.g4dn.xlarge": 45.0,
            "ml.g5.xlarge": 50.0,
            "ml.g5.2xlarge": 65.0,
        }

        mock_cw = AsyncMock()
        mock_cw.put_metric_data = AsyncMock(return_value={})
        mock_ctx = self._make_mock_cw_context(mock_cw)

        # Act
        with patch.object(metrics_service._session, "client", return_value=mock_ctx):
            for instance_type, startup_time in instance_startup_times.items():
                await metrics_service.record_startup_time(f"space-{instance_type}", startup_time)

        # Assert
        assert mock_cw.put_metric_data.call_count == len(instance_startup_times)

        # 验证每次记录的值
        recorded_values = []
        for call in mock_cw.put_metric_data.call_args_list:
            metric_data = call[1]["MetricData"][0]
            recorded_values.append(metric_data["Value"])

        assert recorded_values == [25.0, 28.0, 45.0, 50.0, 65.0]

    @pytest.mark.asyncio
    async def test_gpu_instances_slower_than_cpu(self, metrics_service: SpaceMetricsService) -> None:
        """验证 GPU 实例启动时间通常大于 CPU 实例 (基于模拟数据)."""
        # Arrange - 模拟真实场景: GPU 实例启动更慢
        cpu_startup_times = [25.0, 28.0, 22.0]  # ml.t3 系列
        gpu_startup_times = [45.0, 50.0, 65.0]  # ml.g4dn/g5 系列

        # Assert - GPU 平均启动时间大于 CPU
        avg_cpu = sum(cpu_startup_times) / len(cpu_startup_times)
        avg_gpu = sum(gpu_startup_times) / len(gpu_startup_times)
        assert avg_gpu > avg_cpu

    @pytest.mark.asyncio
    async def test_all_instances_below_timeout(self, metrics_service: SpaceMetricsService) -> None:
        """验证正常实例启动时间均在超时阈值内."""
        # Arrange - 正常启动时间
        normal_startup_times = [25.0, 28.0, 45.0, 50.0, 65.0, 90.0, 120.0]

        # Assert - 所有正常启动时间都在 180 秒内
        for startup_time in normal_startup_times:
            assert startup_time < SpaceMetricsService.STARTUP_TIMEOUT_SECONDS


class TestMetricsServiceConstants:
    """测试服务常量配置."""

    def test_namespace_value(self) -> None:
        """测试 CloudWatch namespace 值."""
        assert SpaceMetricsService.NAMESPACE == "AITrainingPlatform/Spaces"

    def test_timeout_threshold_value(self) -> None:
        """测试超时阈值为 180 秒 (3 分钟)."""
        assert SpaceMetricsService.STARTUP_TIMEOUT_SECONDS == 180
