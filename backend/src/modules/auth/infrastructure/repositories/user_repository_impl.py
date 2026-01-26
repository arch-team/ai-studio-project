"""User Repository Implementation - SQLAlchemy data access for users."""

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import User
from ...domain.repositories import IUserRepository
from ...domain.value_objects import UserRole, UserStatus
from ..models import UserModel


class UserRepositoryImpl(PydanticRepository[User, UserModel, int], IUserRepository):
    """SQLAlchemy implementation of User repository.

    使用 PydanticRepository 自动处理 Entity ↔ Model 转换。
    无需手写 _to_entity, _to_model, _update_model。
    """

    _entity_class = User
    _updatable_fields = [
        "username",
        "email",
        "status",
        "role",
        "display_name",
        "iam_identity_id",
        "iam_groups",
        "resource_quota_id",
        "last_login_at",
        "auth_type",
        "password_hash",
        "password_expires_at",
        "locked_until",
        "failed_login_count",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)

    # ========== IUserRepository 接口方法 ==========

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self._session.execute(select(UserModel).where(UserModel.username == username))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

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
        return self._to_entity(model) if model else None

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
