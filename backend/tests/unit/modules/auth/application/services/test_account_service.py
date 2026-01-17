"""Account Service Unit Tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.modules.auth.application.services.account_service import AccountService
from src.shared.infrastructure.security import (
    InvalidCredentialsError,
    PasswordTooWeakError,
    UserNotFoundError,
)
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects import AuthType, UserRole, UserStatus


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
        locked_until=None,
        failed_login_count=0,
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
def account_service(
    mock_user_repository: AsyncMock,
    mock_password_history_repository: AsyncMock,
    fast_password_hasher,
    password_validator,
) -> AccountService:
    """Create AccountService with mocked dependencies."""
    return AccountService(
        user_repository=mock_user_repository,
        password_history_repository=mock_password_history_repository,
        password_hasher=fast_password_hasher,
        password_validator=password_validator,
    )


class TestCreateLocalAccount:
    """Tests for local account creation."""

    @pytest.mark.asyncio
    async def test_create_local_account_success(
        self,
        account_service: AccountService,
        mock_user_repository: AsyncMock,
        mock_password_history_repository: AsyncMock,
    ) -> None:
        """Test successful account creation."""
        mock_user_repository.exists_by_username.return_value = False
        mock_user_repository.exists_by_email.return_value = False

        created_user = User(
            id=1,
            username="newuser",
            email="new@example.com",
            role=UserRole.ENGINEER,
            status=UserStatus.ACTIVE,
            auth_type=AuthType.LOCAL,
        )
        mock_user_repository.create.return_value = created_user

        result = await account_service.create_local_account(
            username="newuser",
            email="new@example.com",
            password="NewP@ssw0rd123!",
            role="engineer",
        )

        assert result.username == "newuser"
        mock_user_repository.create.assert_called_once()
        mock_password_history_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_local_account_weak_password(
        self,
        account_service: AccountService,
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
        self,
        account_service: AccountService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test account creation with duplicate username."""
        mock_user_repository.exists_by_username.return_value = True

        with pytest.raises(InvalidCredentialsError) as exc_info:
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
        self,
        account_service: AccountService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test enabling a user account."""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            status=UserStatus.INACTIVE,
            role=UserRole.ENGINEER,
            auth_type=AuthType.LOCAL,
        )
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        await account_service.enable_account(1)

        assert user.status == UserStatus.ACTIVE
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_account(
        self,
        account_service: AccountService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """Test disabling a user account."""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.update.return_value = mock_user

        await account_service.disable_account(1)

        assert mock_user.status == UserStatus.INACTIVE
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlock_account(
        self,
        account_service: AccountService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test unlocking a locked account."""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            status=UserStatus.ACTIVE,
            role=UserRole.ENGINEER,
            auth_type=AuthType.LOCAL,
            locked_until=datetime.now(UTC) + timedelta(minutes=30),
            failed_login_count=5,
        )
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        await account_service.unlock_account(1)

        assert user.locked_until is None
        assert user.failed_login_count == 0
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_nonexistent_account(
        self,
        account_service: AccountService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """Test enabling nonexistent account raises error."""
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError) as exc_info:
            await account_service.enable_account(999)

        assert "not found" in str(exc_info.value).lower()
