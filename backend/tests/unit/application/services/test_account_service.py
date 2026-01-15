"""Account Service Unit Tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.services.account_service import AccountService
from src.core.security.exceptions import AuthenticationError, PasswordTooWeakError
from src.domain.value_objects import AuthType, UserRole, UserStatus


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.status = UserStatus.ACTIVE
    user.role = UserRole.ENGINEER
    user.locked_until = None
    user.failed_login_count = 0
    return user


@pytest.fixture
def account_service(mock_session, fast_password_hasher, password_validator):
    """Create AccountService with mocked dependencies."""
    return AccountService(
        session=mock_session,
        password_hasher=fast_password_hasher,
        password_validator=password_validator,
    )


class TestCreateLocalAccount:
    """Tests for local account creation."""

    @pytest.mark.asyncio
    async def test_create_local_account_success(
        self, account_service: AccountService, mock_session: AsyncMock
    ) -> None:
        """Test successful account creation."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await account_service.create_local_account(
            username="newuser",
            email="new@example.com",
            password="NewP@ssw0rd123!",
            role="engineer",
        )

        assert mock_session.add.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_create_local_account_weak_password(
        self, account_service: AccountService, mock_session: AsyncMock
    ) -> None:
        """Test account creation with weak password."""
        with pytest.raises(PasswordTooWeakError) as exc_info:
            await account_service.create_local_account(
                username="newuser",
                email="new@example.com",
                password="weak",
                role="engineer",
            )

        assert len(exc_info.value.violations) > 0

    @pytest.mark.asyncio
    async def test_create_local_account_duplicate_username(
        self, account_service: AccountService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test account creation with duplicate username."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuthenticationError) as exc_info:
            await account_service.create_local_account(
                username="testuser",
                email="new@example.com",
                password="NewP@ssw0rd123!",
                role="engineer",
            )

        assert "username" in str(exc_info.value).lower()


class TestAccountManagement:
    """Tests for account enable/disable/unlock."""

    @pytest.mark.asyncio
    async def test_enable_account(
        self, account_service: AccountService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test enabling a user account."""
        mock_user.status = UserStatus.INACTIVE
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        await account_service.enable_account(1)

        assert mock_user.status == UserStatus.ACTIVE
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_disable_account(
        self, account_service: AccountService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test disabling a user account."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        await account_service.disable_account(1)

        assert mock_user.status == UserStatus.INACTIVE
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_unlock_account(
        self, account_service: AccountService, mock_session: AsyncMock, mock_user
    ) -> None:
        """Test unlocking a locked account."""
        from datetime import datetime, timedelta, timezone

        mock_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        mock_user.failed_login_count = 5
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        await account_service.unlock_account(1)

        assert mock_user.locked_until is None
        assert mock_user.failed_login_count == 0
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_enable_nonexistent_account(
        self, account_service: AccountService, mock_session: AsyncMock
    ) -> None:
        """Test enabling nonexistent account raises error."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuthenticationError) as exc_info:
            await account_service.enable_account(999)

        assert "not found" in str(exc_info.value).lower()
