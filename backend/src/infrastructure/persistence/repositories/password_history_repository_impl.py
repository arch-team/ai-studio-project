"""PasswordHistory Repository Implementation - SQLAlchemy data access for password history."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.password_history import PasswordHistory
from src.domain.repositories.password_history_repository import (
    IPasswordHistoryRepository,
)
from src.infrastructure.persistence.models.password_history_model import (
    PasswordHistoryModel,
)


class PasswordHistoryRepository(IPasswordHistoryRepository):
    """SQLAlchemy implementation of PasswordHistory repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _model_to_entity(self, model: PasswordHistoryModel) -> PasswordHistory:
        """Convert ORM model to domain entity."""
        return PasswordHistory(
            id=model.id,
            user_id=model.user_id,
            password_hash=model.password_hash,
            created_at=model.created_at,
        )

    def _entity_to_model(self, entity: PasswordHistory) -> PasswordHistoryModel:
        """Convert domain entity to ORM model."""
        return PasswordHistoryModel(
            id=entity.id if entity.id else None,
            user_id=entity.user_id,
            password_hash=entity.password_hash,
        )

    async def create(self, history: PasswordHistory) -> PasswordHistory:
        """Create a new password history entry."""
        model = self._entity_to_model(history)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def get_recent(self, user_id: int, limit: int = 5) -> list[PasswordHistory]:
        """Get recent password history entries for a user."""
        result = await self._session.execute(
            select(PasswordHistoryModel)
            .where(PasswordHistoryModel.user_id == user_id)
            .order_by(PasswordHistoryModel.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def cleanup_old_entries(self, user_id: int, keep_count: int = 5) -> int:
        """Remove old password history entries, keeping only the most recent ones."""
        # First, get IDs of entries to keep
        keep_query = (
            select(PasswordHistoryModel.id)
            .where(PasswordHistoryModel.user_id == user_id)
            .order_by(PasswordHistoryModel.created_at.desc())
            .limit(keep_count)
        )
        keep_result = await self._session.execute(keep_query)
        keep_ids = [row[0] for row in keep_result.fetchall()]

        if not keep_ids:
            return 0

        # Delete entries not in the keep list
        delete_query = delete(PasswordHistoryModel).where(
            PasswordHistoryModel.user_id == user_id,
            PasswordHistoryModel.id.not_in(keep_ids),
        )
        result = await self._session.execute(delete_query)
        return result.rowcount


async def get_password_history_repository(
    session: AsyncSession,
) -> PasswordHistoryRepository:
    """Factory function for dependency injection."""
    return PasswordHistoryRepository(session)
