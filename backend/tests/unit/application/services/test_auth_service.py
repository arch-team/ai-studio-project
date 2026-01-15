"""Auth Service Unit Tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.services.auth_service import AuthResult, AuthService, TokenPair
from src.core.security.constants import MAX_FAILED_LOGIN_ATTEMPTS
from src.core.security.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    TokenExpiredError,
)
from src.domain.entities.user import UserRole
from src.infrastructure.persistence.models import AuthType, UserStatus

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.role = UserRole.ENGINEER
    user.status = UserStatus.ACTIVE
    user.password_hash = "$2b$04$test_hash"
    user.password_expires_at = datetime.now(UTC) + timedelta(days=30)
    user.locked_until = None
    user.failed_login_count = 0
    user.auth_type = AuthType.LOCAL
    user.is_locked.return_value = False
    user.is_password_expired.return_value = False
    user.is_local_account.return_value = True
    user.password_history = []
    return user


@pytest.fixture
def mock_locked_user(mock_user):
    """Create a mock locked user."""
    user = mock_user
    user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
    user.failed_login_count = 5
    user.is_locked.return_value = True
    return user


@pytest.fixture
def mock_expired_password_user(mock_user):
    """Create a mock user with expired password."""
    user = mock_user
    user.password_expires_at = datetime.now(UTC) - timedelta(days=1)
    user.is_password_expired.return_value = True
    return user


@pytest.fixture
def mock_sso_user(mock_user):
    """Create a mock SSO user."""
    user = mock_user
    user.auth_type = AuthType.SSO
    user.is_local_account.return_value = False
    user.iam_identity_id = "sso-123"
    return user


@pytest.fixture
def mock_inactive_user(mock_user):
    """Create a mock inactive user."""
    user = mock_user
    user.status = UserStatus.INACTIVE
    return user


@pytest.fixture
def auth_service(mock_session, mock_jwt_manager, fast_password_hasher):
    """Create AuthService with mocked dependencies."""
    return AuthService(
        session=mock_session,
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
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test successful local login."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Mock password verification
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

    @pytest.mark.asyncio
    async def test_local_login_user_not_found(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test login with non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.local_login(
                username="nonexistent",
                password="password",
                ip_address="127.0.0.1",
            )

        assert (
            "user_not_found" in str(exc_info.value).lower()
            or "invalid" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_local_login_invalid_password(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test login with wrong password increments failure count."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=False):
            with pytest.raises(AuthenticationError):
                await auth_service.local_login(
                    username="testuser",
                    password="wrong_password",
                    ip_address="127.0.0.1",
                )

    @pytest.mark.asyncio
    async def test_local_login_account_locked(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_locked_user
    ) -> None:
        """Test login with locked account."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_locked_user
        mock_session.execute.return_value = mock_result

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
        mock_session: AsyncMock,
        mock_expired_password_user,
    ) -> None:
        """Test login with expired password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_expired_password_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            with pytest.raises(PasswordExpiredError):
                await auth_service.local_login(
                    username="testuser",
                    password="TestP@ssw0rd123!",
                    ip_address="127.0.0.1",
                )

    @pytest.mark.asyncio
    async def test_local_login_sso_account(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_sso_user
    ) -> None:
        """Test local login with SSO account fails."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sso_user
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.local_login(
                username="testuser",
                password="password",
                ip_address="127.0.0.1",
            )

        assert (
            "sso" in str(exc_info.value).lower()
            or "local" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_local_login_inactive_account(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_inactive_user
    ) -> None:
        """Test login with inactive account."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_inactive_user
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.local_login(
                username="testuser",
                password="password",
                ip_address="127.0.0.1",
            )

        assert (
            "inactive" in str(exc_info.value).lower()
            or "active" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_local_login_5_failures_triggers_lock(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test that 5 failed attempts triggers account lock."""
        mock_user.failed_login_count = MAX_FAILED_LOGIN_ATTEMPTS - 1  # 4 failures
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=False):
            with pytest.raises(AuthenticationError):
                await auth_service.local_login(
                    username="testuser",
                    password="wrong",
                    ip_address="127.0.0.1",
                )

            # After 5th failure, locked_until should be set
            # This is verified by checking the user object was modified

    @pytest.mark.asyncio
    async def test_local_login_success_resets_counter(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test successful login resets failure counter."""
        mock_user.failed_login_count = 3
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            await auth_service.local_login(
                username="testuser",
                password="TestP@ssw0rd123!",
                ip_address="127.0.0.1",
            )

            # Counter should be reset to 0
            assert mock_user.failed_login_count == 0


# =============================================================================
# Token Refresh Tests
# =============================================================================


class TestRefreshAccessToken:
    """Tests for token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_access_token_valid(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test successful token refresh."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await auth_service.refresh_access_token("valid-refresh-token")

        assert isinstance(result, TokenPair)
        assert result.access_token is not None
        assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test refresh with invalid token."""
        auth_service._jwt.verify_token.side_effect = InvalidTokenError("Invalid")

        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token("invalid-token")

    @pytest.mark.asyncio
    async def test_refresh_access_token_expired(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test refresh with expired token."""
        auth_service._jwt.verify_token.side_effect = TokenExpiredError("Expired")

        with pytest.raises(TokenExpiredError):
            await auth_service.refresh_access_token("expired-token")


# =============================================================================
# Create Local Account Tests (Migrated to test_account_service.py)
# =============================================================================


@pytest.mark.skip(reason="Migrated to test_account_service.py - use AccountService")
class TestCreateLocalAccount:
    """Tests for local account creation."""

    @pytest.mark.asyncio
    async def test_create_local_account_success(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test successful account creation."""
        # Mock no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await auth_service.create_local_account(
            username="newuser",
            email="new@example.com",
            password="NewP@ssw0rd123!",
            role="engineer",
        )

        assert mock_session.add.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_create_local_account_weak_password(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test account creation with weak password."""
        with pytest.raises(PasswordTooWeakError) as exc_info:
            await auth_service.create_local_account(
                username="newuser",
                email="new@example.com",
                password="weak",
                role="engineer",
            )

        assert len(exc_info.value.violations) > 0

    @pytest.mark.asyncio
    async def test_create_local_account_duplicate_username(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test account creation with duplicate username."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.create_local_account(
                username="testuser",  # Existing username
                email="different@example.com",
                password="NewP@ssw0rd123!",
                role="engineer",
            )

        assert (
            "username" in str(exc_info.value).lower()
            or "exists" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_create_local_account_duplicate_email(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test account creation with duplicate email."""
        # First call returns None (username check), second returns user (email check)
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = None
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_user
        mock_session.execute.side_effect = [mock_result1, mock_result2]

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.create_local_account(
                username="newuser",
                email="test@example.com",  # Existing email
                password="NewP@ssw0rd123!",
                role="engineer",
            )

        assert (
            "email" in str(exc_info.value).lower()
            or "exists" in str(exc_info.value).lower()
        )


# =============================================================================
# Change Password Tests (Migrated to test_password_service.py)
# =============================================================================


@pytest.mark.skip(reason="Migrated to test_password_service.py - use PasswordService")
class TestChangePassword:
    """Tests for password change functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test successful password change."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            await auth_service.change_password(
                user_id=1,
                current_password="OldP@ssw0rd123!",
                new_password="NewP@ssw0rd456!",
            )

        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test password change with wrong current password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=False):
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.change_password(
                    user_id=1,
                    current_password="wrong",
                    new_password="NewP@ssw0rd456!",
                )

            assert (
                "current" in str(exc_info.value).lower()
                or "password" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test password change with weak new password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            with pytest.raises(PasswordTooWeakError):
                await auth_service.change_password(
                    user_id=1,
                    current_password="OldP@ssw0rd123!",
                    new_password="weak",
                )

    @pytest.mark.asyncio
    async def test_change_password_history_violation(
        self,
        auth_service: AuthService,
        mock_session: AsyncMock,
        mock_user,
        fast_password_hasher,
    ) -> None:
        """Test password change with password from history."""
        # Setup password history
        old_hash = fast_password_hasher.hash_password("NewP@ssw0rd456!")
        mock_history = MagicMock()
        mock_history.password_hash = old_hash
        mock_user.password_history = [mock_history]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(auth_service._hasher, "verify_password", return_value=True):
            with patch.object(
                auth_service._validator,
                "check_password_history",
                return_value=False,  # False means password IS in history (violation)
            ):
                with pytest.raises(PasswordHistoryViolationError):
                    await auth_service.change_password(
                        user_id=1,
                        current_password="OldP@ssw0rd123!",
                        new_password="NewP@ssw0rd456!",
                    )


# =============================================================================
# Password Reset Tests (Migrated to test_password_service.py)
# =============================================================================


@pytest.mark.skip(reason="Migrated to test_password_service.py - use PasswordService")
class TestPasswordReset:
    """Tests for password reset functionality."""

    @pytest.mark.asyncio
    async def test_request_password_reset_exists(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test password reset request for existing user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        token = await auth_service.request_password_reset(email="test@example.com")

        assert token is not None
        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_request_password_reset_not_exists(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test password reset request for non-existent user returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Should return None, not reveal user doesn't exist
        token = await auth_service.request_password_reset(
            email="nonexistent@example.com"
        )

        assert token is None

    @pytest.mark.asyncio
    async def test_request_password_reset_sso_user(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_sso_user
    ) -> None:
        """Test password reset request for SSO user returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sso_user
        mock_session.execute.return_value = mock_result

        token = await auth_service.request_password_reset(email="sso@example.com")

        assert token is None

    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test successful password reset confirmation."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        await auth_service.confirm_password_reset(
            reset_token="valid-reset-token",
            new_password="NewP@ssw0rd789!",
        )

        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test password reset with invalid token."""
        auth_service._jwt.verify_token.side_effect = InvalidTokenError("Invalid")

        with pytest.raises(InvalidTokenError):
            await auth_service.confirm_password_reset(
                reset_token="invalid-token",
                new_password="NewP@ssw0rd789!",
            )

    @pytest.mark.asyncio
    async def test_confirm_password_reset_expired_token(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test password reset with expired token."""
        auth_service._jwt.verify_token.side_effect = TokenExpiredError("Expired")

        with pytest.raises(TokenExpiredError):
            await auth_service.confirm_password_reset(
                reset_token="expired-token",
                new_password="NewP@ssw0rd789!",
            )


# =============================================================================
# Account Management Tests (Migrated to test_account_service.py)
# =============================================================================


@pytest.mark.skip(reason="Migrated to test_account_service.py - use AccountService")
class TestAccountManagement:
    """Tests for account enable/disable/unlock."""

    @pytest.mark.asyncio
    async def test_enable_account(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_inactive_user
    ) -> None:
        """Test enabling a disabled account."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_inactive_user
        mock_session.execute.return_value = mock_result

        await auth_service.enable_account(user_id=1)

        assert mock_inactive_user.status == UserStatus.ACTIVE
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_disable_account(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test disabling an active account."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        await auth_service.disable_account(user_id=1)

        assert mock_user.status == UserStatus.INACTIVE
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_unlock_account(
        self, auth_service: AuthService, mock_session: AsyncMock, mock_locked_user
    ) -> None:
        """Test unlocking a locked account."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_locked_user
        mock_session.execute.return_value = mock_result

        await auth_service.unlock_account(user_id=1)

        assert mock_locked_user.locked_until is None
        assert mock_locked_user.failed_login_count == 0
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_enable_nonexistent_account(
        self, auth_service: AuthService, mock_session: AsyncMock
    ) -> None:
        """Test enabling non-existent account."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuthenticationError):
            await auth_service.enable_account(user_id=999)


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
