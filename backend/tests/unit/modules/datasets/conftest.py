"""Datasets module test fixtures."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_dataset_repository() -> AsyncMock:
    """Mock IDatasetRepository for testing dataset services."""
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
def mock_dataset_version_repository() -> AsyncMock:
    """Mock IDatasetVersionRepository for testing."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_dataset_id = AsyncMock(return_value=[])
    repo.get_latest_by_dataset_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_s3_client() -> AsyncMock:
    """Mock S3Client for testing dataset storage."""
    client = AsyncMock()
    client.upload_file = AsyncMock()
    client.download_file = AsyncMock()
    client.delete_file = AsyncMock()
    client.generate_presigned_url = AsyncMock(return_value="https://example.com/presigned")
    return client
