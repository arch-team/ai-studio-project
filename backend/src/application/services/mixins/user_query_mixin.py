"""User query mixin - Shared user lookup methods for authentication services."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import UserModel


class UserQueryMixin:
    """Mixin providing common user query methods.

    Classes using this mixin must have a `_session: AsyncSession` attribute.
    """

    _session: AsyncSession

    async def _get_user_by_username(self, username: str) -> UserModel | None:
        """Get user by username."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_email(self, email: str) -> UserModel | None:
        """Get user by email."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: int) -> UserModel | None:
        """Get user by ID."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _ensure_user_exists(self, user_id: int) -> UserModel:
        """Get user by ID, raising error if not found."""
        from src.core.security.exceptions import AuthenticationError

        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        return user
