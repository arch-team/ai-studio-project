"""Account Service - User account management operations."""

from datetime import timedelta

from src.shared.infrastructure.security import (
    PASSWORD_EXPIRY_DAYS,
    PasswordHasher,
    PasswordValidator,
    get_password_hasher,
    get_password_validator,
)
from src.shared.utils import utc_now

from ...domain.entities import PasswordHistory, User
from ...domain.exceptions import (
    InvalidCredentialsError,
    PasswordTooWeakError,
    UserNotFoundError,
)
from ...domain.repositories import IPasswordHistoryRepository, IUserRepository
from ...domain.value_objects import AuthType, UserRole, UserStatus


class AccountService:
    """Service for user account management operations."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_history_repository: IPasswordHistoryRepository,
        password_hasher: PasswordHasher | None = None,
        password_validator: PasswordValidator | None = None,
    ):
        self._user_repository = user_repository
        self._password_history_repository = password_history_repository
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

        if await self._user_repository.exists_by_username(username):
            raise InvalidCredentialsError("Username already exists")

        if await self._user_repository.exists_by_email(email):
            raise InvalidCredentialsError("Email already exists")

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
        created_user = await self._user_repository.create(user)

        # Add to password history
        assert created_user.id is not None, "Created user must have ID"
        history = PasswordHistory.create(
            user_id=created_user.id,
            password_hash=password_hash,
        )
        await self._password_history_repository.create(history)

        return created_user

    async def enable_account(self, user_id: int) -> None:
        """Enable a user account."""
        user = await self._ensure_user_exists(user_id)
        user.activate()
        user.reset_login_failures()
        await self._user_repository.update(user)

    async def disable_account(self, user_id: int) -> None:
        """Disable a user account."""
        user = await self._ensure_user_exists(user_id)
        user.status = UserStatus.INACTIVE
        await self._user_repository.update(user)

    async def unlock_account(self, user_id: int) -> None:
        """Unlock a locked user account."""
        user = await self._ensure_user_exists(user_id)
        user.reset_login_failures()
        await self._user_repository.update(user)

    async def get_or_create_sso_user(
        self,
        iam_identity_id: str,
        username: str,
        email: str,
        display_name: str | None = None,
        groups: list[str] | None = None,
        role: str = "engineer",
    ) -> User:
        """Get or create an SSO user by IAM identity ID.

        If user exists, updates their groups and role.
        If user doesn't exist, creates a new SSO user.
        """
        existing_user = await self._user_repository.get_by_iam_identity_id(iam_identity_id)

        if existing_user:
            # Update existing user's groups and role
            existing_user.iam_groups = groups or []
            existing_user.role = UserRole(role)
            return await self._user_repository.update(existing_user)

        # Create new SSO user
        user = User(
            id=0,  # Will be set by repository
            username=username,
            email=email,
            display_name=display_name,
            iam_identity_id=iam_identity_id,
            iam_groups=groups or [],
            auth_type=AuthType.SSO,
            status=UserStatus.ACTIVE,
            role=UserRole(role),
        )
        return await self._user_repository.create(user)

    async def _ensure_user_exists(self, user_id: int) -> User:
        """Get user by ID, raising error if not found."""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user
