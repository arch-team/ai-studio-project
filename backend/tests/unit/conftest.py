"""Unit Test Configuration - Shared fixtures for unit tests."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.core.security.constants import PASSWORD_BCRYPT_COST
from src.core.security.jwt import JWTManager, TokenPayload, TokenType
from src.core.security.password import PasswordHasher, PasswordValidator
from src.domain.entities.user import UserRole, UserStatus


# =============================================================================
# JWT Manager Fixtures
# =============================================================================


@pytest.fixture
def jwt_secret_key() -> str:
    """Test secret key for JWT operations."""
    return "test-secret-key-for-jwt-signing-at-least-32-chars"


@pytest.fixture
def mock_settings(jwt_secret_key: str) -> MagicMock:
    """Mock settings with test secret key."""
    settings = MagicMock()
    settings.secret_key = jwt_secret_key
    settings.access_token_expire_minutes = 30
    return settings


@pytest.fixture
def jwt_manager(mock_settings: MagicMock) -> JWTManager:
    """Real JWTManager instance for testing with mocked settings."""
    with patch("src.core.security.jwt.get_settings", return_value=mock_settings):
        return JWTManager()


@pytest.fixture
def mock_jwt_manager() -> Mock:
    """Mock JWTManager for isolated unit tests."""
    manager = Mock(spec=JWTManager)
    manager.create_access_token.return_value = "mock-access-token"
    manager.create_refresh_token.return_value = "mock-refresh-token"
    manager.create_password_reset_token.return_value = "mock-reset-token"
    manager.verify_token.return_value = TokenPayload(
        sub="1",
        username="testuser",
        email="test@example.com",
        role="engineer",
        exp=datetime.now(timezone.utc) + timedelta(hours=1),
        iat=datetime.now(timezone.utc),
        token_type=TokenType.ACCESS,
        jti="test-jti",
    )
    manager.get_user_id_from_token.return_value = 1
    return manager


# =============================================================================
# Password Fixtures
# =============================================================================


@pytest.fixture
def password_hasher() -> PasswordHasher:
    """Real PasswordHasher instance for testing."""
    return PasswordHasher(cost_factor=PASSWORD_BCRYPT_COST)


@pytest.fixture
def fast_password_hasher() -> PasswordHasher:
    """Faster PasswordHasher for tests (lower cost factor)."""
    return PasswordHasher(cost_factor=4)


@pytest.fixture
def password_validator() -> PasswordValidator:
    """PasswordValidator instance for testing."""
    return PasswordValidator()


@pytest.fixture
def valid_passwords() -> List[str]:
    """List of valid passwords meeting all requirements."""
    return [
        "P@ssw0rd123!",
        "Secure!Pass123",
        "C0mplex#Pass99",
        "Test@User1234",
        "Admin$ecure99",
    ]


@pytest.fixture
def invalid_passwords() -> Dict[str, str]:
    """Dictionary of invalid passwords with their violation type."""
    return {
        "too_short": "Short1!",
        "no_lowercase": "NOLOWERCASE1!@#",
        "no_uppercase": "nouppercase1!@#",
        "no_digit": "NoDigitHere!@#Ab",
        "no_special": "NoSpecial123ABC",
        "only_lowercase": "onlylowercase",
        "only_numbers": "123456789012",
    }


# =============================================================================
# User Fixtures
# =============================================================================


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
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
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def admin_user_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Admin user data for testing."""
    return {
        **sample_user_data,
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "display_name": "Admin User",
        "role": UserRole.ADMIN,
    }


@pytest.fixture
def project_manager_user_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Project manager user data for testing."""
    return {
        **sample_user_data,
        "id": 2,
        "username": "manager",
        "email": "manager@example.com",
        "display_name": "Project Manager",
        "role": UserRole.PROJECT_MANAGER,
    }


@pytest.fixture
def engineer_user_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Engineer user data for testing."""
    return {
        **sample_user_data,
        "id": 3,
        "username": "engineer",
        "email": "engineer@example.com",
        "display_name": "Engineer User",
        "role": UserRole.ENGINEER,
    }


@pytest.fixture
def viewer_user_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Viewer user data for testing."""
    return {
        **sample_user_data,
        "id": 4,
        "username": "viewer",
        "email": "viewer@example.com",
        "display_name": "Viewer User",
        "role": UserRole.VIEWER,
    }


@pytest.fixture
def locked_user_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Locked user data for testing."""
    return {
        **sample_user_data,
        "id": 5,
        "username": "locked_user",
        "email": "locked@example.com",
        "display_name": "Locked User",
        "locked_until": datetime.now(timezone.utc) + timedelta(minutes=30),
        "failed_login_count": 5,
    }


@pytest.fixture
def expired_password_user_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """User with expired password for testing."""
    return {
        **sample_user_data,
        "id": 6,
        "username": "expired_user",
        "email": "expired@example.com",
        "display_name": "Expired Password User",
        "password_expires_at": datetime.now(timezone.utc) - timedelta(days=1),
    }


@pytest.fixture
def inactive_user_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Inactive user data for testing."""
    return {
        **sample_user_data,
        "id": 7,
        "username": "inactive_user",
        "email": "inactive@example.com",
        "display_name": "Inactive User",
        "status": UserStatus.INACTIVE,
    }


# =============================================================================
# Mock Database Session
# =============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock AsyncSession for database operations."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


# =============================================================================
# Token Fixtures
# =============================================================================


@pytest.fixture
def sample_token_payload() -> Dict[str, Any]:
    """Sample token payload data."""
    now = datetime.now(timezone.utc)
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
def expired_token_payload(sample_token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Expired token payload data."""
    now = datetime.now(timezone.utc)
    return {
        **sample_token_payload,
        "exp": now - timedelta(minutes=30),
        "iat": now - timedelta(hours=1),
    }
