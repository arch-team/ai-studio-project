"""Auth Service Unit Tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.auth.application.services.auth_service import (
    AuthResult,
    AuthService,
    TokenPair,
)
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordExpiredError,
    TokenExpiredError,
)
from src.modules.auth.domain.value_objects import AuthType, UserRole, UserStatus
from src.shared.infrastructure.security.constants import MAX_FAILED_LOGIN_ATTEMPTS

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> User:
    """Create a mock user entity."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        display_name="Test User",
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE,
        auth_type=AuthType.LOCAL,
        password_hash="$2b$04$test_hash",
        password_expires_at=datetime.now(UTC) + timedelta(days=30),
        locked_until=None,
        failed_login_count=0,
    )


@pytest.fixture
def mock_locked_user() -> User:
    """Create a mock locked user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE,
        auth_type=AuthType.LOCAL,
        password_hash="$2b$04$test_hash",
        locked_until=datetime.now(UTC) + timedelta(minutes=30),
        failed_login_count=5,
    )


@pytest.fixture
def mock_expired_password_user() -> User:
    """Create a mock user with expired password."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE,
        auth_type=AuthType.LOCAL,
        password_hash="$2b$04$test_hash",
        password_expires_at=datetime.now(UTC) - timedelta(days=1),
    )


@pytest.fixture
def mock_sso_user() -> User:
    """Create a mock SSO user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE,
        auth_type=AuthType.SSO,
        iam_identity_id="sso-123",
    )


@pytest.fixture
def mock_inactive_user() -> User:
    """Create a mock inactive user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        role=UserRole.ENGINEER,
        status=UserStatus.INACTIVE,
        auth_type=AuthType.LOCAL,
        password_hash="$2b$04$test_hash",
    )


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Create a mock user repository."""
    return AsyncMock()


@pytest.fixture
def mock_login_attempt_repository() -> AsyncMock:
    """Create a mock login attempt repository."""
    return AsyncMock()


@pytest.fixture
def auth_service(
    mock_user_repository: AsyncMock,
    mock_login_attempt_repository: AsyncMock,
    mock_jwt_manager,
    fast_password_hasher,
) -> AuthService:
    """Create AuthService with mocked dependencies."""
    return AuthService(
        user_repository=mock_user_repository,
        login_attempt_repository=mock_login_attempt_repository,
        jwt_manager=mock_jwt_manager,
        password_hasher=fast_password_hasher,
    )


# =============================================================================
# Local Login Tests
# =============================================================================


class TestLocalLogin:
    """Tests for local login functionality."""

    @pytest.mark.asyncio
    async def test_local_login_success(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test successful local login."""
        mock_user_repository.get_by_username.return_value = mock_user
        mock_user_repository.update.return_value = mock_user

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            result = await auth_service.local_login(
                username="testuser",
                password="TestP@ssw0rd123!",
                ip_address="127.0.0.1",
                user_agent="test-agent",
            )

        assert isinstance(result, AuthResult)
        assert result.user_id == mock_user.id
        assert result.username == mock_user.username
        assert result.tokens is not None
        mock_user_repository.get_by_username.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_local_login_user_not_found(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test login with non-existent user."""
        mock_user_repository.get_by_username.return_value = None

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.local_login(
                username="nonexistent",
                password="password",
                ip_address="127.0.0.1",
            )

        assert "user_not_found" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_local_login_invalid_password(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test login with wrong password increments failure count."""
        mock_user_repository.get_by_username.return_value = mock_user
        mock_user_repository.update.return_value = mock_user

        with patch.object(auth_service._hasher, "verify_password", return_value=False):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.local_login(
                    username="testuser",
                    password="wrong_password",
                    ip_address="127.0.0.1",
                )

    @pytest.mark.asyncio
    async def test_local_login_account_locked(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_locked_user: User,
    ) -> None:
        """Test login with locked account."""
        mock_user_repository.get_by_username.return_value = mock_locked_user

        with pytest.raises(AccountLockedError) as exc_info:
            await auth_service.local_login(
                username="testuser",
                password="password",
                ip_address="127.0.0.1",
            )

        assert exc_info.value.locked_until is not None

    @pytest.mark.asyncio
    async def test_local_login_password_expired(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_expired_password_user: User,
    ) -> None:
        """Test login with expired password."""
        mock_user_repository.get_by_username.return_value = mock_expired_password_user

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            with pytest.raises(PasswordExpiredError):
                await auth_service.local_login(
                    username="testuser",
                    password="TestP@ssw0rd123!",
                    ip_address="127.0.0.1",
                )

    @pytest.mark.asyncio
    async def test_local_login_sso_account(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_sso_user: User,
    ) -> None:
        """Test local login with SSO account fails."""
        mock_user_repository.get_by_username.return_value = mock_sso_user

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.local_login(
                username="testuser",
                password="password",
                ip_address="127.0.0.1",
            )

        assert "sso" in str(exc_info.value).lower() or "local" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_local_login_inactive_account(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_inactive_user: User,
    ) -> None:
        """Test login with inactive account."""
        mock_user_repository.get_by_username.return_value = mock_inactive_user

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.local_login(
                username="testuser",
                password="password",
                ip_address="127.0.0.1",
            )

        assert "inactive" in str(exc_info.value).lower() or "active" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_local_login_5_failures_triggers_lock(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test that 5 failed attempts triggers account lock."""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            role=UserRole.ENGINEER,
            status=UserStatus.ACTIVE,
            auth_type=AuthType.LOCAL,
            password_hash="$2b$04$test_hash",
            failed_login_count=MAX_FAILED_LOGIN_ATTEMPTS - 1,  # 4 failures
        )
        mock_user_repository.get_by_username.return_value = user
        mock_user_repository.update.return_value = user

        with patch.object(auth_service._hasher, "verify_password", return_value=False):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.local_login(
                    username="testuser",
                    password="wrong",
                    ip_address="127.0.0.1",
                )

        # After 5th failure, locked_until should be set
        assert user.locked_until is not None

    @pytest.mark.asyncio
    async def test_local_login_success_resets_counter(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test successful login resets failure counter."""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            role=UserRole.ENGINEER,
            status=UserStatus.ACTIVE,
            auth_type=AuthType.LOCAL,
            password_hash="$2b$04$test_hash",
            password_expires_at=datetime.now(UTC) + timedelta(days=30),
            failed_login_count=3,
        )
        mock_user_repository.get_by_username.return_value = user
        mock_user_repository.update.return_value = user

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            await auth_service.local_login(
                username="testuser",
                password="TestP@ssw0rd123!",
                ip_address="127.0.0.1",
            )

        # Counter should be reset to 0
        assert user.failed_login_count == 0


# =============================================================================
# Token Refresh Tests
# =============================================================================


class TestRefreshAccessToken:
    """Tests for token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_access_token_valid(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test successful token refresh."""
        mock_user_repository.get_by_id.return_value = mock_user

        result = await auth_service.refresh_access_token("valid-refresh-token")

        assert isinstance(result, TokenPair)
        assert result.access_token is not None
        assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test refresh with invalid token."""
        auth_service._jwt.verify_token.side_effect = InvalidTokenError("Invalid")

        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token("invalid-token")

    @pytest.mark.asyncio
    async def test_refresh_access_token_expired(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test refresh with expired token."""
        auth_service._jwt.verify_token.side_effect = TokenExpiredError("Expired")

        with pytest.raises(TokenExpiredError):
            await auth_service.refresh_access_token("expired-token")


# =============================================================================
# Data Classes Tests
# =============================================================================


class TestAuthResultDataClass:
    """Tests for AuthResult dataclass."""

    def test_auth_result_creation(self) -> None:
        """Test AuthResult creation."""
        tokens = TokenPair(
            access_token="access",
            refresh_token="refresh",
            token_type="bearer",
            expires_in=1800,
        )
        result = AuthResult(
            user_id=1,
            username="test",
            email="test@example.com",
            role="engineer",
            tokens=tokens,
        )

        assert result.user_id == 1
        assert result.username == "test"
        assert result.tokens.access_token == "access"


class TestTokenPairDataClass:
    """Tests for TokenPair dataclass."""

    def test_token_pair_creation(self) -> None:
        """Test TokenPair creation."""
        pair = TokenPair(
            access_token="access-token",
            refresh_token="refresh-token",
            token_type="bearer",
            expires_in=1800,
        )

        assert pair.access_token == "access-token"
        assert pair.refresh_token == "refresh-token"
        assert pair.token_type == "bearer"
        assert pair.expires_in == 1800
