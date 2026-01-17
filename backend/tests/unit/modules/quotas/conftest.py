"""Quotas module test fixtures."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_resource_quota_repository() -> AsyncMock:
    """Mock IResourceQuotaRepository for testing quota services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_user_id = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_resource_limit_config_repository() -> AsyncMock:
    """Mock IResourceLimitConfigRepository for testing."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_name = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo
