"""Monitoring module test fixtures."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_metric_repository() -> AsyncMock:
    """Mock IMetricRepository for testing monitoring services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_job_id = AsyncMock(return_value=[])
    repo.get_by_time_range = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.create_batch = AsyncMock()
    return repo


@pytest.fixture
def mock_alert_repository() -> AsyncMock:
    """Mock IAlertRepository for testing alert services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_active = AsyncMock(return_value=[])
    repo.get_by_severity = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.acknowledge = AsyncMock()
    return repo
