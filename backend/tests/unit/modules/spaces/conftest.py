"""Fixtures for spaces module unit tests."""

from unittest.mock import AsyncMock

import pytest

from src.modules.spaces.application.services.sagemaker_metrics_service import SpaceMetricsService


@pytest.fixture
def mock_cw_client() -> AsyncMock:
    """创建 Mock CloudWatch 客户端."""
    client = AsyncMock()
    client.put_metric_data = AsyncMock(return_value={})
    client.get_metric_statistics = AsyncMock(return_value={"Datapoints": []})
    return client


@pytest.fixture
def metrics_service() -> SpaceMetricsService:
    """创建 SpaceMetricsService 实例."""
    return SpaceMetricsService()
