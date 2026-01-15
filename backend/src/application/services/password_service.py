"""Password Service - Password management operations."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.mixins import UserQueryMixin
from src.core.security.constants import PASSWORD_EXPIRY_DAYS, PASSWORD_HISTORY_COUNT
from src.core.security.exceptions import (
    AuthenticationError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
)
from src.core.security.jwt import JWTManager, TokenType, get_jwt_manager
from src.core.security.password import (
    PasswordHasher,
    PasswordValidator,
    get_password_hasher,
    get_password_validator,
)
from src.core.utils import utc_now
from src.infrastructure.persistence.models import PasswordHistoryModel, UserModel


class PasswordService(UserQueryMixin):
    """Service for password management operations."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_manager: JWTManager | None = None,
        password_hasher: PasswordHasher | None = None,
        password_validator: PasswordValidator | None = None,
    ):
        self._session = session
        self._jwt = jwt_manager or get_jwt_manager()
        self._hasher = password_hasher or get_password_hasher()
        self._validator = password_validator or get_password_validator()

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user password."""
        user = await self._ensure_user_exists(user_id)

        if not user.is_local_account():
            raise AuthenticationError("Cannot change password for SSO account")

        if not user.password_hash or not self._hasher.verify_password(
            current_password, user.password_hash
        ):
            raise AuthenticationError("Current password is incorrect")

        await self._validate_new_password(user_id, new_password)
        await self._update_user_password(user, new_password)
        await self._session.commit()

    async def request_password_reset(self, email: str) -> str | None:
        """Request password reset and return reset token."""
        user = await self._get_user_by_email(email)
        if not user or not user.is_local_account():
            return None

        from src.domain.value_objects import UserStatus

        if user.status != UserStatus.ACTIVE:
            return None

        return self._jwt.create_password_reset_token(user.id, user.email)

    async def confirm_password_reset(
        self,
        reset_token: str,
        new_password: str,
    ) -> None:
        """Confirm password reset with token."""
        payload = self._jwt.verify_token(reset_token, TokenType.PASSWORD_RESET)
        user_id = int(payload.sub)

        user = await self._ensure_user_exists(user_id)

        if not user.is_local_account():
            raise AuthenticationError("Cannot reset password for SSO account")

        await self._validate_new_password(user_id, new_password)
        await self._update_user_password(user, new_password)
        await self._session.commit()

    async def _validate_new_password(self, user_id: int, new_password: str) -> None:
        """Validate password strength and check history."""
        violations = self._validator.validate_strength(new_password)
        if violations:
            raise PasswordTooWeakError(violations)

        password_history = await self._get_password_history(user_id)
        history_hashes = [h.password_hash for h in password_history]

        if not self._validator.check_password_history(
            new_password, history_hashes, self._hasher
        ):
            raise PasswordHistoryViolationError()

    async def _update_user_password(self, user: UserModel, new_password: str) -> None:
        """Update user password and add to history."""
        new_hash = self._hasher.hash_password(new_password)
        user.password_hash = new_hash
        user.password_expires_at = utc_now() + timedelta(days=PASSWORD_EXPIRY_DAYS)
        user.failed_login_count = 0
        user.locked_until = None

        history = PasswordHistoryModel(
            user_id=user.id,
            password_hash=new_hash,
        )
        self._session.add(history)
        await self._cleanup_password_history(user.id)

    async def _get_password_history(self, user_id: int) -> list[PasswordHistoryModel]:
        """Get password history for user."""
        result = await self._session.execute(
            select(PasswordHistoryModel)
            .where(PasswordHistoryModel.user_id == user_id)
            .order_by(PasswordHistoryModel.created_at.desc())
            .limit(PASSWORD_HISTORY_COUNT)
        )
        return list(result.scalars().all())

    async def _cleanup_password_history(self, user_id: int) -> None:
        """Keep only the most recent PASSWORD_HISTORY_COUNT entries."""
        result = await self._session.execute(
            select(PasswordHistoryModel)
            .where(PasswordHistoryModel.user_id == user_id)
            .order_by(PasswordHistoryModel.created_at.desc())
        )
        history = list(result.scalars().all())

        if len(history) > PASSWORD_HISTORY_COUNT:
            for entry in history[PASSWORD_HISTORY_COUNT:]:
                await self._session.delete(entry)
