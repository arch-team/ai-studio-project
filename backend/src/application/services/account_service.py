"""Account Service - User account management operations."""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.mixins import UserQueryMixin
from src.core.security.constants import PASSWORD_EXPIRY_DAYS
from src.core.security.exceptions import AuthenticationError, PasswordTooWeakError
from src.core.security.password import (
    PasswordHasher,
    PasswordValidator,
    get_password_hasher,
    get_password_validator,
)
from src.core.utils import utc_now
from src.domain.value_objects import AuthType, UserRole, UserStatus
from src.infrastructure.persistence.models import PasswordHistoryModel, UserModel


class AccountService(UserQueryMixin):
    """Service for user account management operations."""

    def __init__(
        self,
        session: AsyncSession,
        password_hasher: PasswordHasher | None = None,
        password_validator: PasswordValidator | None = None,
    ):
        self._session = session
        self._hasher = password_hasher or get_password_hasher()
        self._validator = password_validator or get_password_validator()

    async def create_local_account(
        self,
        username: str,
        email: str,
        password: str,
        role: str,
        display_name: str | None = None,
    ) -> UserModel:
        """Create a new local authentication account."""
        violations = self._validator.validate_strength(password)
        if violations:
            raise PasswordTooWeakError(violations)

        existing = await self._get_user_by_username(username)
        if existing:
            raise AuthenticationError("Username already exists")

        existing_email = await self._get_user_by_email(email)
        if existing_email:
            raise AuthenticationError("Email already exists")

        password_hash = self._hasher.hash_password(password)

        user = UserModel(
            username=username,
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            password_expires_at=utc_now() + timedelta(days=PASSWORD_EXPIRY_DAYS),
            auth_type=AuthType.LOCAL,
            status=UserStatus.ACTIVE,
            role=UserRole(role),
        )
        self._session.add(user)
        await self._session.flush()

        history = PasswordHistoryModel(
            user_id=user.id,
            password_hash=password_hash,
        )
        self._session.add(history)
        await self._session.commit()

        return user

    async def enable_account(self, user_id: int) -> None:
        """Enable a user account."""
        user = await self._ensure_user_exists(user_id)
        user.status = UserStatus.ACTIVE
        user.locked_until = None
        user.failed_login_count = 0
        await self._session.commit()

    async def disable_account(self, user_id: int) -> None:
        """Disable a user account."""
        user = await self._ensure_user_exists(user_id)
        user.status = UserStatus.INACTIVE
        await self._session.commit()

    async def unlock_account(self, user_id: int) -> None:
        """Unlock a locked user account."""
        user = await self._ensure_user_exists(user_id)
        user.locked_until = None
        user.failed_login_count = 0
        await self._session.commit()
