"""Password Service - Password management operations."""

from datetime import timedelta

from src.shared.infrastructure.security import (
    PASSWORD_EXPIRY_DAYS,
    PASSWORD_HISTORY_COUNT,
    JWTManager,
    PasswordHasher,
    PasswordValidator,
    TokenType,
    get_jwt_manager,
    get_password_hasher,
    get_password_validator,
)
from src.shared.utils import utc_now

from ...domain.entities import PasswordHistory, User
from ...domain.exceptions import (
    InvalidCredentialsError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    UserNotFoundError,
)
from ...domain.repositories import IPasswordHistoryRepository, IUserRepository
from ...domain.value_objects import UserStatus


class PasswordService:
    """Service for password management operations."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_history_repository: IPasswordHistoryRepository,
        jwt_manager: JWTManager | None = None,
        password_hasher: PasswordHasher | None = None,
        password_validator: PasswordValidator | None = None,
    ):
        self._user_repo = user_repository
        self._password_history_repo = password_history_repository
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
            raise InvalidCredentialsError("Cannot change password for SSO account")

        if not user.password_hash or not self._hasher.verify_password(
            current_password, user.password_hash
        ):
            raise InvalidCredentialsError("Current password is incorrect")

        await self._validate_new_password(user_id, new_password)
        await self._update_user_password(user, new_password)

    async def request_password_reset(self, email: str) -> str | None:
        """Request password reset and return reset token."""
        user = await self._user_repo.get_by_email(email)
        if not user or not user.is_local_account():
            return None

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
            raise InvalidCredentialsError("Cannot reset password for SSO account")

        await self._validate_new_password(user_id, new_password)
        await self._update_user_password(user, new_password)

    async def _validate_new_password(self, user_id: int, new_password: str) -> None:
        """Validate password strength and check history."""
        violations = self._validator.validate_strength(new_password)
        if violations:
            raise PasswordTooWeakError(violations)

        password_history = await self._password_history_repo.get_recent(
            user_id, PASSWORD_HISTORY_COUNT
        )
        history_hashes = [h.password_hash for h in password_history]

        if not self._validator.check_password_history(
            new_password, history_hashes, self._hasher
        ):
            raise PasswordHistoryViolationError()

    async def _update_user_password(self, user: User, new_password: str) -> None:
        """Update user password and add to history."""
        new_hash = self._hasher.hash_password(new_password)
        user.update_password(
            password_hash=new_hash,
            expires_at=utc_now() + timedelta(days=PASSWORD_EXPIRY_DAYS),
        )
        await self._user_repo.update(user)

        # Add to password history
        history = PasswordHistory.create(
            user_id=user.id,
            password_hash=new_hash,
        )
        await self._password_history_repo.create(history)

        # Cleanup old password history entries
        await self._password_history_repo.cleanup_old_entries(
            user.id, PASSWORD_HISTORY_COUNT
        )

    async def _ensure_user_exists(self, user_id: int) -> User:
        """Get user by ID, raising error if not found."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user
