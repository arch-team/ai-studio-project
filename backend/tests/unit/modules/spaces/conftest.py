"""Spaces module test fixtures."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_space_repository() -> AsyncMock:
    """Mock ISpaceRepository for testing space services."""
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
def mock_sagemaker_spaces_client() -> AsyncMock:
    """Mock SageMakerSpacesClient for testing."""
    client = AsyncMock()
    client.create_space = AsyncMock()
    client.delete_space = AsyncMock()
    client.get_space_status = AsyncMock()
    client.start_space = AsyncMock()
    client.stop_space = AsyncMock()
    return client
