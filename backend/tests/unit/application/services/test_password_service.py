"""Password Service Unit Tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.services.password_service import PasswordService
from src.core.security.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    PasswordTooWeakError,
    TokenExpiredError,
)
from src.domain.value_objects import AuthType, UserStatus


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.status = UserStatus.ACTIVE
    user.password_hash = "$2b$04$test_hash"
    user.password_expires_at = datetime.now(UTC) + timedelta(days=30)
    user.locked_until = None
    user.failed_login_count = 0
    user.auth_type = AuthType.LOCAL
    user.is_local_account.return_value = True
    return user


@pytest.fixture
def mock_sso_user(mock_user):
    """Create a mock SSO user."""
    user = mock_user
    user.auth_type = AuthType.SSO
    user.is_local_account.return_value = False
    return user


@pytest.fixture
def password_service(
    mock_session, mock_jwt_manager, fast_password_hasher, password_validator
):
    """Create PasswordService with mocked dependencies."""
    return PasswordService(
        session=mock_session,
        jwt_manager=mock_jwt_manager,
        password_hasher=fast_password_hasher,
        password_validator=password_validator,
    )


class TestChangePassword:
    """Tests for change password functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, password_service: PasswordService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test successful password change."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Mock empty password history
        mock_history_result = MagicMock()
        mock_history_result.scalars.return_value.all.return_value = []

        def execute_side_effect(stmt):
            # Return user for first query, empty history for second
            if "PasswordHistoryModel" in str(stmt):
                return mock_history_result
            return mock_result

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)

        with patch.object(
            password_service._hasher, "verify_password", return_value=True
        ):
            await password_service.change_password(
                user_id=1,
                current_password="OldP@ssw0rd123!",
                new_password="NewP@ssw0rd456!",
            )

        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, password_service: PasswordService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test change password with wrong current password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(
            password_service._hasher, "verify_password", return_value=False
        ):
            with pytest.raises(AuthenticationError) as exc_info:
                await password_service.change_password(
                    user_id=1,
                    current_password="WrongPassword",
                    new_password="NewP@ssw0rd456!",
                )

        assert "incorrect" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(
        self, password_service: PasswordService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test change password with weak new password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with patch.object(
            password_service._hasher, "verify_password", return_value=True
        ):
            with pytest.raises(PasswordTooWeakError):
                await password_service.change_password(
                    user_id=1,
                    current_password="OldP@ssw0rd123!",
                    new_password="weak",
                )


class TestPasswordReset:
    """Tests for password reset functionality."""

    @pytest.mark.asyncio
    async def test_request_password_reset_exists(
        self, password_service: PasswordService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test password reset request for existing user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        token = await password_service.request_password_reset("test@example.com")

        assert token is not None

    @pytest.mark.asyncio
    async def test_request_password_reset_not_exists(
        self, password_service: PasswordService, mock_session: AsyncMock
    ) -> None:
        """Test password reset request for non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        token = await password_service.request_password_reset("nonexistent@example.com")

        assert token is None

    @pytest.mark.asyncio
    async def test_request_password_reset_sso_user(
        self, password_service: PasswordService, mock_session: AsyncMock, mock_sso_user
    ) -> None:
        """Test password reset request for SSO user returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sso_user
        mock_session.execute.return_value = mock_result

        token = await password_service.request_password_reset("test@example.com")

        assert token is None

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(
        self, password_service: PasswordService, mock_session: AsyncMock
    ) -> None:
        """Test password reset confirm with invalid token."""
        password_service._jwt.verify_token.side_effect = InvalidTokenError("Invalid")

        with pytest.raises(InvalidTokenError):
            await password_service.confirm_password_reset(
                reset_token="invalid-token",
                new_password="NewP@ssw0rd456!",
            )

    @pytest.mark.asyncio
    async def test_confirm_password_reset_expired_token(
        self, password_service: PasswordService, mock_session: AsyncMock
    ) -> None:
        """Test password reset confirm with expired token."""
        password_service._jwt.verify_token.side_effect = TokenExpiredError("Expired")

        with pytest.raises(TokenExpiredError):
            await password_service.confirm_password_reset(
                reset_token="expired-token",
                new_password="NewP@ssw0rd456!",
            )
