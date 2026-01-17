"""Billing module test fixtures."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_cost_record_repository() -> AsyncMock:
    """Mock ICostRecordRepository for testing billing services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_user_id = AsyncMock(return_value=[])
    repo.get_by_date_range = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.aggregate_by_user = AsyncMock(return_value={})
    repo.aggregate_by_resource_type = AsyncMock(return_value={})
    return repo
