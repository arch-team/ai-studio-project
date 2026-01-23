"""MLflow 集成测试 (T037a)

需要运行 MLflow 服务:
    docker run -p 5000:5000 ghcr.io/mlflow/mlflow:v2.10.0 mlflow server --host 0.0.0.0

或使用 SageMaker Managed MLflow。
"""

import os
from datetime import UTC, datetime, timedelta

import pytest

from src.modules.training.application.services.mlflow_service import (
    MLflowService,
    MLflowServiceError,
)


def mlflow_available() -> bool:
    """检查 MLflow 服务是否可用"""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    try:
        from mlflow.tracking import MlflowClient

        client = MlflowClient(tracking_uri=tracking_uri)
        client.search_experiments(max_results=1)
        return True
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.skipif(not mlflow_available(), reason="MLflow 服务不可用")
class TestMLflowIntegration:
    """MLflow 端到端集成测试"""

    @pytest.fixture
    def service(self) -> MLflowService:
        """创建真实的 MLflowService"""
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        return MLflowService(
            tracking_uri=tracking_uri,
            experiment_prefix="test-integration",
            timeout=30,
            max_retries=3,
        )

    @pytest.mark.asyncio
    async def test_health_check(self, service: MLflowService):
        """验证健康检查"""
        result = await service.check_health()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_metric_history_no_run(self, service: MLflowService):
        """验证查询不存在的任务返回空列表"""
        start_time = datetime.now(UTC) - timedelta(hours=1)
        end_time = datetime.now(UTC)

        result = await service.get_metric_history(
            job_id=999999,  # 不存在的任务
            metric_name="loss",
            start_time=start_time,
            end_time=end_time,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_experiment_not_found(self, service: MLflowService):
        """验证查询不存在的实验抛出异常"""
        with pytest.raises(MLflowServiceError) as exc_info:
            await service.get_experiment("nonexistent-experiment-12345")

        assert "not found" in str(exc_info.value).lower()


@pytest.mark.integration
class TestMLflowServiceUnavailable:
    """测试 MLflow 服务不可用时的行为"""

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_unavailable(self):
        """验证服务不可用时健康检查返回 False"""
        service = MLflowService(
            tracking_uri="http://nonexistent-host:5000",
            experiment_prefix="test",
            timeout=5,
            max_retries=1,
        )

        result = await service.check_health()
        assert result is False
