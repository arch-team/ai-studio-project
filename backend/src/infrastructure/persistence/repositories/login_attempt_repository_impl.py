"""LoginAttempt Repository Implementation - SQLAlchemy data access for login attempts."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.login_attempt import LoginAttempt
from src.domain.repositories.login_attempt_repository import ILoginAttemptRepository
from src.infrastructure.persistence.models.login_attempt_model import LoginAttemptModel


class LoginAttemptRepository(ILoginAttemptRepository):
    """SQLAlchemy implementation of LoginAttempt repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _model_to_entity(self, model: LoginAttemptModel) -> LoginAttempt:
        """Convert ORM model to domain entity."""
        return LoginAttempt(
            id=model.id,
            user_id=model.user_id,
            username=model.username,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            success=model.success,
            failure_reason=model.failure_reason,
            created_at=model.created_at,
        )

    def _entity_to_model(self, entity: LoginAttempt) -> LoginAttemptModel:
        """Convert domain entity to ORM model."""
        return LoginAttemptModel(
            id=entity.id if entity.id else None,
            user_id=entity.user_id,
            username=entity.username,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            success=entity.success,
            failure_reason=entity.failure_reason,
        )

    async def create(self, attempt: LoginAttempt) -> LoginAttempt:
        """Create a new login attempt record."""
        model = self._entity_to_model(attempt)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def get_recent_failures(
        self, username: str, limit: int = 5
    ) -> list[LoginAttempt]:
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
        return [self._model_to_entity(m) for m in models]


async def get_login_attempt_repository(
    session: AsyncSession,
) -> LoginAttemptRepository:
    """Factory function for dependency injection."""
    return LoginAttemptRepository(session)
