"""User Repository Implementation - SQLAlchemy data access for users."""

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.repository_base import EnhancedBaseRepository

from ...domain.entities import User
from ...domain.repositories import IUserRepository
from ...domain.value_objects import AuthType, UserRole, UserStatus
from ..models import UserModel


class UserRepositoryImpl(EnhancedBaseRepository[User, UserModel, int], IUserRepository):
    """SQLAlchemy implementation of User repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)

    def _to_entity(self, model: UserModel) -> User:
        """Convert ORM model to domain entity."""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            status=UserStatus(model.status.value),
            role=UserRole(model.role.value),
            display_name=model.display_name,
            iam_identity_id=model.iam_identity_id,
            iam_groups=model.iam_groups or [],
            resource_quota_id=model.resource_quota_id,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            auth_type=AuthType(model.auth_type.value),
            password_hash=model.password_hash,
            password_expires_at=model.password_expires_at,
            locked_until=model.locked_until,
            failed_login_count=model.failed_login_count,
        )

    def _to_model(self, entity: User) -> UserModel:
        """Convert domain entity to ORM model."""
        return UserModel(
            id=entity.id if entity.id else None,
            username=entity.username,
            email=entity.email,
            status=UserStatus(entity.status.value),
            role=UserRole(entity.role.value),
            display_name=entity.display_name,
            iam_identity_id=entity.iam_identity_id,
            iam_groups=entity.iam_groups,
            resource_quota_id=entity.resource_quota_id,
            last_login_at=entity.last_login_at,
            auth_type=AuthType(entity.auth_type.value),
            password_hash=entity.password_hash,
            password_expires_at=entity.password_expires_at,
            locked_until=entity.locked_until,
            failed_login_count=entity.failed_login_count,
        )

    def _update_model(self, model: UserModel, entity: User) -> None:
        """Update ORM model fields from entity."""
        model.username = entity.username
        model.email = entity.email
        model.status = UserStatus(entity.status.value)
        model.role = UserRole(entity.role.value)
        model.display_name = entity.display_name
        model.iam_identity_id = entity.iam_identity_id
        model.iam_groups = entity.iam_groups
        model.resource_quota_id = entity.resource_quota_id
        model.last_login_at = entity.last_login_at
        model.auth_type = AuthType(entity.auth_type.value)
        model.password_hash = entity.password_hash
        model.password_expires_at = entity.password_expires_at
        model.locked_until = entity.locked_until
        model.failed_login_count = entity.failed_login_count

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self._session.execute(select(UserModel).where(UserModel.username == username))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def exists_by_username(self, username: str) -> bool:
        """Check if a user with the given username exists."""
        return await self.exists_by("username", username)

    async def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        return await self.exists_by("email", email)

    async def get_by_iam_identity_id(self, iam_identity_id: str) -> User | None:
        """Get user by IAM identity ID (for SSO users)."""
        result = await self._session.execute(select(UserModel).where(UserModel.iam_identity_id == iam_identity_id))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 20,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[User]:
        """List users with pagination and filters."""
        stmt = select(UserModel)

        # Apply filters
        if role is not None:
            stmt = stmt.where(UserModel.role == role)
        if status is not None:
            stmt = stmt.where(UserModel.status == status)

        # Apply sorting
        sort_column = getattr(UserModel, sort_by, UserModel.created_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(asc(sort_column))
        else:
            stmt = stmt.order_by(desc(sort_column))

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count_users(
        self,
        role: UserRole | None = None,
        status: UserStatus | None = None,
    ) -> int:
        """Count users with optional filters."""
        stmt = select(func.count(UserModel.id))

        if role is not None:
            stmt = stmt.where(UserModel.role == role)
        if status is not None:
            stmt = stmt.where(UserModel.status == status)

        result = await self._session.execute(stmt)
        return result.scalar_one()
