"""Account Service - User account management operations."""

from datetime import timedelta

from src.core.security.constants import PASSWORD_EXPIRY_DAYS
from src.core.security.exceptions import AuthenticationError, PasswordTooWeakError
from src.core.security.password import (
    PasswordHasher,
    PasswordValidator,
    get_password_hasher,
    get_password_validator,
)
from src.core.utils import utc_now
from src.domain.entities.password_history import PasswordHistory
from src.domain.entities.user import User
from src.domain.repositories.password_history_repository import (
    IPasswordHistoryRepository,
)
from src.domain.repositories.user_repository import IUserRepository
from src.domain.value_objects import AuthType, UserRole, UserStatus


class AccountService:
    """Service for user account management operations."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_history_repository: IPasswordHistoryRepository,
        password_hasher: PasswordHasher | None = None,
        password_validator: PasswordValidator | None = None,
    ):
        self._user_repo = user_repository
        self._password_history_repo = password_history_repository
        self._hasher = password_hasher or get_password_hasher()
        self._validator = password_validator or get_password_validator()

    async def create_local_account(
        self,
        username: str,
        email: str,
        password: str,
        role: str,
        display_name: str | None = None,
    ) -> User:
        """Create a new local authentication account."""
        violations = self._validator.validate_strength(password)
        if violations:
            raise PasswordTooWeakError(violations)

        if await self._user_repo.exists_by_username(username):
            raise AuthenticationError("Username already exists")

        if await self._user_repo.exists_by_email(email):
            raise AuthenticationError("Email already exists")

        password_hash = self._hasher.hash_password(password)

        user = User(
            id=0,  # Will be set by repository
            username=username,
            email=email,
            display_name=display_name,
            auth_type=AuthType.LOCAL,
            status=UserStatus.ACTIVE,
            role=UserRole(role),
            password_hash=password_hash,
            password_expires_at=utc_now() + timedelta(days=PASSWORD_EXPIRY_DAYS),
        )
        created_user = await self._user_repo.create(user)

        # Add to password history
        history = PasswordHistory.create(
            user_id=created_user.id,
            password_hash=password_hash,
        )
        await self._password_history_repo.create(history)

        return created_user

    async def enable_account(self, user_id: int) -> None:
        """Enable a user account."""
        user = await self._ensure_user_exists(user_id)
        user.activate()
        user.reset_login_failures()
        await self._user_repo.update(user)

    async def disable_account(self, user_id: int) -> None:
        """Disable a user account."""
        user = await self._ensure_user_exists(user_id)
        user.status = UserStatus.INACTIVE
        await self._user_repo.update(user)

    async def unlock_account(self, user_id: int) -> None:
        """Unlock a locked user account."""
        user = await self._ensure_user_exists(user_id)
        user.reset_login_failures()
        await self._user_repo.update(user)

    async def _ensure_user_exists(self, user_id: int) -> User:
        """Get user by ID, raising error if not found."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        return user
