"""Authentication and authorization fixtures."""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from pydantic import SecretStr

from tests.shared.constants import (
    TEST_ACCESS_TOKEN_EXPIRE_MINUTES,
    TEST_JWT_SECRET,
    TEST_PASSWORD_COST,
)

# =============================================================================
# JWT Manager Fixtures
# =============================================================================


@pytest.fixture
def jwt_secret_key() -> str:
    """Test secret key for JWT operations."""
    return TEST_JWT_SECRET


@pytest.fixture
def mock_settings(jwt_secret_key: str) -> MagicMock:
    """Mock settings with test secret key."""
    settings = MagicMock()
    settings.secret_key = SecretStr(jwt_secret_key)
    settings.access_token_expire_minutes = TEST_ACCESS_TOKEN_EXPIRE_MINUTES
    return settings


@pytest.fixture
def jwt_manager(mock_settings: MagicMock):
    """Real JWTManager instance for testing with mocked settings."""
    from src.shared.infrastructure.security.jwt import JWTManager

    with patch(
        "src.shared.infrastructure.security.jwt.get_settings",
        return_value=mock_settings,
    ):
        return JWTManager()


@pytest.fixture
def mock_jwt_manager():
    """Mock JWTManager for isolated unit tests."""
    from src.shared.infrastructure.security.jwt import JWTManager, TokenPayload, TokenType

    manager = Mock(spec=JWTManager)
    manager.create_access_token.return_value = "mock-access-token"
    manager.create_refresh_token.return_value = "mock-refresh-token"
    manager.create_password_reset_token.return_value = "mock-reset-token"
    manager.verify_token.return_value = TokenPayload(
        sub="1",
        username="testuser",
        email="test@example.com",
        role="engineer",
        exp=datetime.now(UTC) + timedelta(hours=1),
        iat=datetime.now(UTC),
        token_type=TokenType.ACCESS,
        jti="test-jti",
    )
    return manager


# =============================================================================
# Password Fixtures
# =============================================================================


@pytest.fixture
def password_hasher():
    """Real PasswordHasher instance for testing."""
    from src.shared.infrastructure.security.constants import PASSWORD_BCRYPT_COST
    from src.shared.infrastructure.security.password import PasswordHasher

    return PasswordHasher(cost_factor=PASSWORD_BCRYPT_COST)


@pytest.fixture
def fast_password_hasher():
    """Faster PasswordHasher for tests (lower cost factor)."""
    from src.shared.infrastructure.security.password import PasswordHasher

    return PasswordHasher(cost_factor=TEST_PASSWORD_COST)


@pytest.fixture
def password_validator():
    """PasswordValidator instance for testing."""
    from src.shared.infrastructure.security.password import PasswordValidator

    return PasswordValidator()


# =============================================================================
# User Data Fixtures
# =============================================================================


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    from src.modules.auth.domain.entities.user import UserRole, UserStatus

    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "display_name": "Test User",
        "role": UserRole.ENGINEER,
        "status": UserStatus.ACTIVE,
        "iam_identity_id": None,
        "iam_groups": None,
        "resource_quota_id": None,
        "last_login_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


@pytest.fixture
def admin_user_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Admin user data for testing."""
    from src.modules.auth.domain.entities.user import UserRole

    return {
        **sample_user_data,
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "display_name": "Admin User",
        "role": UserRole.ADMIN,
    }


@pytest.fixture
def project_manager_user_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Project manager user data for testing."""
    from src.modules.auth.domain.entities.user import UserRole

    return {
        **sample_user_data,
        "id": 2,
        "username": "manager",
        "email": "manager@example.com",
        "display_name": "Project Manager",
        "role": UserRole.PROJECT_MANAGER,
    }


@pytest.fixture
def engineer_user_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Engineer user data for testing."""
    from src.modules.auth.domain.entities.user import UserRole

    return {
        **sample_user_data,
        "id": 3,
        "username": "engineer",
        "email": "engineer@example.com",
        "display_name": "Engineer User",
        "role": UserRole.ENGINEER,
    }


@pytest.fixture
def viewer_user_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Viewer user data for testing."""
    from src.modules.auth.domain.entities.user import UserRole

    return {
        **sample_user_data,
        "id": 4,
        "username": "viewer",
        "email": "viewer@example.com",
        "display_name": "Viewer User",
        "role": UserRole.VIEWER,
    }


@pytest.fixture
def locked_user_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Locked user data for testing."""
    return {
        **sample_user_data,
        "id": 5,
        "username": "locked_user",
        "email": "locked@example.com",
        "display_name": "Locked User",
        "locked_until": datetime.now(UTC) + timedelta(minutes=30),
        "failed_login_count": 5,
    }


@pytest.fixture
def inactive_user_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Inactive user data for testing."""
    from src.modules.auth.domain.entities.user import UserStatus

    return {
        **sample_user_data,
        "id": 7,
        "username": "inactive_user",
        "email": "inactive@example.com",
        "display_name": "Inactive User",
        "status": UserStatus.INACTIVE,
    }


# =============================================================================
# Token Fixtures
# =============================================================================


@pytest.fixture
def sample_token_payload() -> dict[str, Any]:
    """Sample token payload data."""
    now = datetime.now(UTC)
    return {
        "sub": "1",
        "username": "testuser",
        "email": "test@example.com",
        "role": "engineer",
        "exp": now + timedelta(minutes=30),
        "iat": now,
        "token_type": "access",
        "jti": "unique-token-id",
    }


@pytest.fixture
def expired_token_payload(sample_token_payload: dict[str, Any]) -> dict[str, Any]:
    """Expired token payload data."""
    now = datetime.now(UTC)
    return {
        **sample_token_payload,
        "exp": now - timedelta(minutes=30),
        "iat": now - timedelta(hours=1),
    }
