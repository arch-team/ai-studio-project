"""Auth module test fixtures."""

from unittest.mock import AsyncMock

import pytest

from src.modules.auth.domain.entities.user import User, UserRole, UserStatus


@pytest.fixture
def sample_user() -> User:
    """Create a sample User entity for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        display_name="Test User",
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
def admin_user() -> User:
    """Create an admin User entity for testing."""
    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        password_hash="hashed_password",
        display_name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Mock IUserRepository for testing auth services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_username = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.exists_by_username = AsyncMock(return_value=False)
    repo.exists_by_email = AsyncMock(return_value=False)
    return repo


@pytest.fixture
def mock_login_attempt_repository() -> AsyncMock:
    """Mock ILoginAttemptRepository for testing auth services."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_recent_attempts = AsyncMock(return_value=[])
    repo.count_failed_attempts = AsyncMock(return_value=0)
    return repo
