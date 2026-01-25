"""Common mock objects for testing."""

from typing import Generic, TypeVar
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.shared.constants import (
    TEST_ACCESS_TOKEN_EXPIRE_MINUTES,
    TEST_JWT_SECRET,
)

T = TypeVar("T")


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock application settings."""
    settings = MagicMock()
    settings.secret_key = TEST_JWT_SECRET
    settings.access_token_expire_minutes = TEST_ACCESS_TOKEN_EXPIRE_MINUTES
    settings.aws_region = "us-east-1"
    settings.s3_bucket_name = "test-bucket"
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    return settings


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Generic mock repository for testing services.

    Returns a mock that implements common repository methods.
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.exists = AsyncMock(return_value=False)
    return repo


class MockRepositoryFactory(Generic[T]):
    """Factory for creating typed mock repositories.

    Usage:
        factory = MockRepositoryFactory[User]()
        mock_repo = factory.create()
        mock_repo.get_by_id.return_value = sample_user
    """

    def create(self, entity: T | None = None) -> AsyncMock:
        """Create a mock repository with optional default entity."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=entity)
        repo.get_all = AsyncMock(return_value=[entity] if entity else [])
        repo.create = AsyncMock(return_value=entity)
        repo.update = AsyncMock(return_value=entity)
        repo.delete = AsyncMock(return_value=None)
        repo.exists = AsyncMock(return_value=entity is not None)
        return repo


@pytest.fixture
def mock_event_bus() -> MagicMock:
    """Mock event bus for testing event publishing."""
    bus = MagicMock()
    bus.publish = MagicMock()
    bus.publish_async = AsyncMock()
    bus.subscribe = MagicMock()
    return bus


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Mock HTTP client for external API calls."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client
