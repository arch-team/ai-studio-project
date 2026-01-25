"""Models module test fixtures."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_model_repository() -> AsyncMock:
    """Mock IModelRepository for testing model services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_name = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_owner = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_model_version_repository() -> AsyncMock:
    """Mock IModelVersionRepository for testing."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_model_id = AsyncMock(return_value=[])
    repo.get_latest_by_model_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo
