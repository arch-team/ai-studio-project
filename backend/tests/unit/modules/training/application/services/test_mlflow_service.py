"""MLflowService 单元测试 (T037a)

测试覆盖:
- 核心功能: get_metric_history, get_experiment, list_runs
- 容错处理: MLflow 不可用、超时、重试
- 健康检查: check_health

参考: spec.md L890-979 MLflow 集成方案
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.modules.training.application.interfaces import MetricPoint

# =============================================================================
# 测试 Fixtures
# =============================================================================


@pytest.fixture
def mock_mlflow_client():
    """Mock MLflow MlflowClient"""
    with patch(
        "src.modules.training.application.services.mlflow_service.MlflowClient"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mlflow_service(mock_mlflow_client):
    """创建 MLflowService 实例"""
    from src.modules.training.application.services.mlflow_service import MLflowService

    return MLflowService(
        tracking_uri="http://mlflow.test:5000",
        experiment_prefix="ai-training-platform",
        timeout=30,
        max_retries=3,
    )


# =============================================================================
# 测试 get_metric_history
# =============================================================================


class TestMLflowServiceGetMetricHistory:
    """测试 get_metric_history 方法"""

    @pytest.mark.asyncio
    async def test_returns_metric_points_for_valid_job(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证能正确返回指标数据点"""
        # Arrange: Mock MLflow run 和 metric history
        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"
        mock_mlflow_client.search_runs.return_value = [mock_run]

        mock_metric = MagicMock()
        mock_metric.timestamp = 1704067200000  # 2024-01-01 00:00:00 UTC in ms
        mock_metric.value = 0.5
        mock_mlflow_client.get_metric_history.return_value = [mock_metric]

        # Act
        start_time = datetime(2024, 1, 1, tzinfo=UTC)
        end_time = datetime(2024, 1, 2, tzinfo=UTC)
        result = await mlflow_service.get_metric_history(
            job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], MetricPoint)
        assert result[0].value == 0.5

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_metrics(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证无指标时返回空列表"""
        # Arrange: Run 存在但无指标
        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"
        mock_mlflow_client.search_runs.return_value = [mock_run]
        mock_mlflow_client.get_metric_history.return_value = []

        # Act
        start_time = datetime(2024, 1, 1, tzinfo=UTC)
        end_time = datetime(2024, 1, 2, tzinfo=UTC)
        result = await mlflow_service.get_metric_history(
            job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_run_found(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证无对应 run 时返回空列表"""
        # Arrange: 没有找到 run
        mock_mlflow_client.search_runs.return_value = []

        # Act
        start_time = datetime(2024, 1, 1, tzinfo=UTC)
        end_time = datetime(2024, 1, 2, tzinfo=UTC)
        result = await mlflow_service.get_metric_history(
            job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_filters_by_time_range(self, mlflow_service, mock_mlflow_client):
        """验证时间范围过滤正确"""
        # Arrange: 返回多个时间点的数据
        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"
        mock_mlflow_client.search_runs.return_value = [mock_run]

        # 三个数据点，只有中间的在时间范围内
        mock_metrics = [
            MagicMock(timestamp=1704067200000, value=0.1),  # 2024-01-01 00:00 UTC
            MagicMock(timestamp=1704110400000, value=0.2),  # 2024-01-01 12:00 UTC
            MagicMock(timestamp=1704153600000, value=0.3),  # 2024-01-02 00:00 UTC
        ]
        mock_mlflow_client.get_metric_history.return_value = mock_metrics

        # Act: 只查询 2024-01-01 06:00 到 2024-01-01 18:00 的数据
        start_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=UTC)
        result = await mlflow_service.get_metric_history(
            job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert: 只返回时间范围内的数据
        assert len(result) == 1
        assert result[0].value == 0.2

    @pytest.mark.asyncio
    async def test_maps_job_id_to_mlflow_run_id(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证 job_id 到 MLflow run_id 的映射"""
        # Arrange
        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"
        mock_mlflow_client.search_runs.return_value = [mock_run]
        mock_mlflow_client.get_metric_history.return_value = []

        # Act
        start_time = datetime(2024, 1, 1, tzinfo=UTC)
        end_time = datetime(2024, 1, 2, tzinfo=UTC)
        await mlflow_service.get_metric_history(
            job_id=42, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert: 验证 search_runs 使用了正确的过滤条件
        mock_mlflow_client.search_runs.assert_called_once()
        call_args = mock_mlflow_client.search_runs.call_args
        # 检查过滤条件包含 job_id
        assert "tags.job_id" in str(call_args) or "filter_string" in str(call_args)


# =============================================================================
# 测试 get_experiment
# =============================================================================


class TestMLflowServiceExperiment:
    """测试实验相关方法"""

    @pytest.mark.asyncio
    async def test_get_experiment_by_name_success(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证按名称获取实验"""
        # Arrange
        mock_experiment = MagicMock()
        mock_experiment.experiment_id = "exp-123"
        mock_experiment.name = "ai-training-platform/test"
        mock_mlflow_client.get_experiment_by_name.return_value = mock_experiment

        # Act
        result = await mlflow_service.get_experiment("test")

        # Assert
        assert result["experiment_id"] == "exp-123"
        assert "test" in result["name"]

    @pytest.mark.asyncio
    async def test_get_experiment_not_found(self, mlflow_service, mock_mlflow_client):
        """验证实验不存在时抛出异常"""
        # Arrange
        mock_mlflow_client.get_experiment_by_name.return_value = None

        # Act & Assert
        from src.modules.training.application.services.mlflow_service import (
            MLflowServiceError,
        )

        with pytest.raises(MLflowServiceError) as exc_info:
            await mlflow_service.get_experiment("nonexistent")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_runs_success(self, mlflow_service, mock_mlflow_client):
        """验证列出实验下的运行"""
        # Arrange
        mock_run1 = MagicMock()
        mock_run1.info.run_id = "run-1"
        mock_run2 = MagicMock()
        mock_run2.info.run_id = "run-2"
        mock_mlflow_client.search_runs.return_value = [mock_run1, mock_run2]

        # Act
        result = await mlflow_service.list_runs(experiment_id="exp-123")

        # Assert
        assert len(result) == 2


# =============================================================================
# 测试容错处理
# =============================================================================


class TestMLflowServiceErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_raises_service_error_when_mlflow_unavailable(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证 MLflow 不可用时抛出 MLflowServiceError"""
        # Arrange: 模拟 MLflow 连接失败
        from mlflow.exceptions import MlflowException

        mock_mlflow_client.search_runs.side_effect = MlflowException(
            "Connection refused"
        )

        # Act & Assert
        from src.modules.training.application.services.mlflow_service import (
            MLflowServiceError,
        )

        with pytest.raises(MLflowServiceError) as exc_info:
            start_time = datetime(2024, 1, 1, tzinfo=UTC)
            end_time = datetime(2024, 1, 2, tzinfo=UTC)
            await mlflow_service.get_metric_history(
                job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
            )

        assert (
            "unavailable" in str(exc_info.value).lower()
            or "connection" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self, mlflow_service, mock_mlflow_client):
        """验证瞬时错误时重试"""
        # Arrange: 前两次失败，第三次成功
        from mlflow.exceptions import MlflowException

        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"

        mock_mlflow_client.search_runs.side_effect = [
            MlflowException("Timeout"),
            MlflowException("Timeout"),
            [mock_run],
        ]
        mock_mlflow_client.get_metric_history.return_value = []

        # Act
        start_time = datetime(2024, 1, 1, tzinfo=UTC)
        end_time = datetime(2024, 1, 2, tzinfo=UTC)
        result = await mlflow_service.get_metric_history(
            job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert: 重试后成功
        assert result == []
        assert mock_mlflow_client.search_runs.call_count == 3

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_available(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证健康检查返回正确状态 (可用)"""
        # Arrange
        mock_mlflow_client.search_experiments.return_value = []

        # Act
        result = await mlflow_service.check_health()

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_unavailable(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证健康检查返回正确状态 (不可用)"""
        # Arrange
        from mlflow.exceptions import MlflowException

        mock_mlflow_client.search_experiments.side_effect = MlflowException(
            "Connection refused"
        )

        # Act
        result = await mlflow_service.check_health()

        # Assert
        assert result is False


# =============================================================================
# 测试边界情况
# =============================================================================


class TestMLflowServiceEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_handles_multiple_runs_for_same_job(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证同一 job_id 有多个 run 时只取最新的"""
        # Arrange: 返回多个 run，第一个应该是最新的
        mock_run_old = MagicMock()
        mock_run_old.info.run_id = "run-old"
        mock_run_old.info.start_time = 1000

        mock_run_new = MagicMock()
        mock_run_new.info.run_id = "run-new"
        mock_run_new.info.start_time = 2000

        # search_runs 返回最新的在前
        mock_mlflow_client.search_runs.return_value = [mock_run_new, mock_run_old]

        mock_metric = MagicMock()
        mock_metric.timestamp = 1704067200000
        mock_metric.value = 0.5
        mock_mlflow_client.get_metric_history.return_value = [mock_metric]

        # Act
        start_time = datetime(2024, 1, 1, tzinfo=UTC)
        end_time = datetime(2024, 1, 2, tzinfo=UTC)
        await mlflow_service.get_metric_history(
            job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert: 使用最新的 run
        mock_mlflow_client.get_metric_history.assert_called_with("run-new", "loss")

    @pytest.mark.asyncio
    async def test_sorts_metric_points_by_timestamp(
        self, mlflow_service, mock_mlflow_client
    ):
        """验证返回的指标点按时间升序排列"""
        # Arrange
        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"
        mock_mlflow_client.search_runs.return_value = [mock_run]

        # 乱序返回
        mock_metrics = [
            MagicMock(timestamp=1704110400000, value=0.2),  # 中间
            MagicMock(timestamp=1704067200000, value=0.1),  # 最早
            MagicMock(timestamp=1704153600000, value=0.3),  # 最晚
        ]
        mock_mlflow_client.get_metric_history.return_value = mock_metrics

        # Act
        start_time = datetime(2024, 1, 1, tzinfo=UTC)
        end_time = datetime(2024, 1, 3, tzinfo=UTC)
        result = await mlflow_service.get_metric_history(
            job_id=1, metric_name="loss", start_time=start_time, end_time=end_time
        )

        # Assert: 按时间升序
        assert len(result) == 3
        assert result[0].value == 0.1
        assert result[1].value == 0.2
        assert result[2].value == 0.3
