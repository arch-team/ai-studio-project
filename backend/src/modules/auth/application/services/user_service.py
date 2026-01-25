"""User Service - User management operations (CRUD)."""

from src.shared.domain.exceptions import DuplicateEntityError
from src.shared.utils import utc_now

from ...domain.entities import User
from ...domain.exceptions import UserNotFoundError
from ...domain.repositories import IUserRepository
from ...domain.value_objects import AuthType, UserRole, UserStatus


class UserService:
    """Service for user management operations."""

    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        """List users with pagination and filters.

        Returns:
            Tuple of (users, total_count)
        """
        offset = (page - 1) * page_size
        users = await self._user_repository.list_users(
            offset=offset,
            limit=page_size,
            role=role,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = await self._user_repository.count_users(role=role, status=status)
        return users, total

    async def get_user(self, user_id: int) -> User:
        """Get user by ID."""
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    async def create_user(
        self,
        username: str,
        email: str,
        role: str,
        display_name: str | None = None,
        resource_quota_id: int | None = None,
    ) -> User:
        """Create a new SSO user (without password).

        For local accounts with password, use AccountService.create_local_account.
        """
        # Check for existing username
        if await self._user_repository.exists_by_username(username):
            raise DuplicateEntityError(entity_type="User", identifier=username)

        # Check for existing email
        if await self._user_repository.exists_by_email(email):
            raise DuplicateEntityError(entity_type="User", identifier=email)

        user = User(
            id=0,  # Will be set by repository
            username=username,
            email=email,
            display_name=display_name,
            auth_type=AuthType.SSO,
            status=UserStatus.ACTIVE,
            role=UserRole(role),
            resource_quota_id=resource_quota_id,
        )
        return await self._user_repository.create(user)

    async def update_user(
        self,
        user_id: int,
        role: str | None = None,
        status: str | None = None,
        display_name: str | None = None,
        resource_quota_id: int | None = None,
    ) -> User:
        """Update user attributes."""
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if role is not None:
            user.role = UserRole(role)

        if status is not None:
            user.status = UserStatus(status)

        if display_name is not None:
            user.display_name = display_name

        if resource_quota_id is not None:
            user.resource_quota_id = resource_quota_id

        user.updated_at = utc_now()
        return await self._user_repository.update(user)
