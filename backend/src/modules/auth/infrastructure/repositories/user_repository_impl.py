"""User Repository Implementation - SQLAlchemy data access for users."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities import User
from ...domain.repositories import IUserRepository
from ...domain.value_objects import AuthType, UserRole, UserStatus
from ..models import UserModel


class UserRepositoryImpl(IUserRepository):
    """SQLAlchemy implementation of User repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _model_to_entity(self, model: UserModel) -> User:
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

    def _entity_to_model(self, entity: User) -> UserModel:
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

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def create(self, user: User) -> User:
        """Create a new user."""
        model = self._entity_to_model(user)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def update(self, user: User) -> User:
        """Update an existing user."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"User with id {user.id} not found")

        # Update fields
        model.username = user.username
        model.email = user.email
        model.status = UserStatus(user.status.value)
        model.role = UserRole(user.role.value)
        model.display_name = user.display_name
        model.iam_identity_id = user.iam_identity_id
        model.iam_groups = user.iam_groups
        model.resource_quota_id = user.resource_quota_id
        model.last_login_at = user.last_login_at
        model.auth_type = AuthType(user.auth_type.value)
        model.password_hash = user.password_hash
        model.password_expires_at = user.password_expires_at
        model.locked_until = user.locked_until
        model.failed_login_count = user.failed_login_count

        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def exists_by_username(self, username: str) -> bool:
        """Check if a user with the given username exists."""
        result = await self._session.execute(
            select(func.count(UserModel.id)).where(UserModel.username == username)
        )
        count = result.scalar() or 0
        return count > 0

    async def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        result = await self._session.execute(
            select(func.count(UserModel.id)).where(UserModel.email == email)
        )
        count = result.scalar() or 0
        return count > 0

    async def get_by_iam_identity_id(self, iam_identity_id: str) -> User | None:
        """Get user by IAM identity ID (for SSO users)."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.iam_identity_id == iam_identity_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)
