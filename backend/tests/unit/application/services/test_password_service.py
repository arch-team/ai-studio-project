"""Password Service Unit Tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.application.services.password_service import PasswordService
from src.core.security.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    PasswordTooWeakError,
    TokenExpiredError,
)
from src.domain.entities.user import User
from src.domain.value_objects import AuthType, UserRole, UserStatus


@pytest.fixture
def mock_user() -> User:
    """Create a mock user entity."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        status=UserStatus.ACTIVE,
        role=UserRole.ENGINEER,
        auth_type=AuthType.LOCAL,
        password_hash="$2b$04$test_hash",
        password_expires_at=datetime.now(UTC) + timedelta(days=30),
        locked_until=None,
        failed_login_count=0,
    )


@pytest.fixture
def mock_sso_user() -> User:
    """Create a mock SSO user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        status=UserStatus.ACTIVE,
        role=UserRole.ENGINEER,
        auth_type=AuthType.SSO,
        iam_identity_id="sso-123",
    )


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Create a mock user repository."""
    return AsyncMock()


@pytest.fixture
def mock_password_history_repository() -> AsyncMock:
    """Create a mock password history repository."""
    return AsyncMock()


@pytest.fixture
def password_service(
    mock_user_repository: AsyncMock,
    mock_password_history_repository: AsyncMock,
    mock_jwt_manager,
    fast_password_hasher,
    password_validator,
) -> PasswordService:
    """Create PasswordService with mocked dependencies."""
    return PasswordService(
        user_repository=mock_user_repository,
        password_history_repository=mock_password_history_repository,
        jwt_manager=mock_jwt_manager,
        password_hasher=fast_password_hasher,
        password_validator=password_validator,
    )


class TestChangePassword:
    """Tests for change password functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self,
        password_service: PasswordService,
        mock_user_repository: AsyncMock,
        mock_password_history_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test successful password change."""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.update.return_value = mock_user
        mock_password_history_repository.get_recent.return_value = []
        mock_password_history_repository.cleanup_old_entries.return_value = 0

        with patch.object(
            password_service._hasher, "verify_password", return_value=True
        ):
            await password_service.change_password(
                user_id=1,
                current_password="OldP@ssw0rd123!",
                new_password="NewP@ssw0rd456!",
            )

        mock_user_repository.update.assert_called_once()
        mock_password_history_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self,
        password_service: PasswordService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test change password with wrong current password."""
        mock_user_repository.get_by_id.return_value = mock_user

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
        self,
        password_service: PasswordService,
        mock_user_repository: AsyncMock,
        mock_password_history_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test change password with weak new password."""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_password_history_repository.get_recent.return_value = []

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
        self,
        password_service: PasswordService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test password reset request for existing user."""
        mock_user_repository.get_by_email.return_value = mock_user

        token = await password_service.request_password_reset("test@example.com")

        assert token is not None

    @pytest.mark.asyncio
    async def test_request_password_reset_not_exists(
        self,
        password_service: PasswordService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test password reset request for non-existent user."""
        mock_user_repository.get_by_email.return_value = None

        token = await password_service.request_password_reset("nonexistent@example.com")

        assert token is None

    @pytest.mark.asyncio
    async def test_request_password_reset_sso_user(
        self,
        password_service: PasswordService,
        mock_user_repository: AsyncMock,
        mock_sso_user: User,
    ) -> None:
        """Test password reset request for SSO user returns None."""
        mock_user_repository.get_by_email.return_value = mock_sso_user

        token = await password_service.request_password_reset("test@example.com")

        assert token is None

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(
        self,
        password_service: PasswordService,
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
        self,
        password_service: PasswordService,
    ) -> None:
        """Test password reset confirm with expired token."""
        password_service._jwt.verify_token.side_effect = TokenExpiredError("Expired")

        with pytest.raises(TokenExpiredError):
            await password_service.confirm_password_reset(
                reset_token="expired-token",
                new_password="NewP@ssw0rd456!",
            )
