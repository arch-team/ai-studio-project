"""LoginAttempt Repository Implementation - SQLAlchemy data access for login attempts."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import LoginAttempt
from ...domain.repositories import ILoginAttemptRepository
from ..models import LoginAttemptModel


class LoginAttemptRepositoryImpl(PydanticRepository[LoginAttempt, LoginAttemptModel, int], ILoginAttemptRepository):
    """SQLAlchemy implementation of LoginAttempt repository."""

    _entity_class = LoginAttempt
    _updatable_fields: list[str] = []  # Immutable after creation

    def __init__(self, session: AsyncSession):
        super().__init__(session, LoginAttemptModel)

    # ========== ILoginAttemptRepository 接口方法 ==========

    async def add(self, attempt: LoginAttempt) -> LoginAttempt:
        """Create a new login attempt record."""
        model = self._to_model(attempt)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_recent_failures(self, username: str, limit: int = 5) -> list[LoginAttempt]:
        """Get recent failed login attempts for a username."""
        result = await self._session.execute(
            select(LoginAttemptModel)
            .where(
                LoginAttemptModel.username == username,
                LoginAttemptModel.success == False,  # noqa: E712
            )
            .order_by(LoginAttemptModel.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
