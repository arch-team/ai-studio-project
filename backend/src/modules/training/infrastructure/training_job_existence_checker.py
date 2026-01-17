"""TrainingJob Existence Checker - Implementation of cross-module interface."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.training.infrastructure.models import TrainingJobModel
from src.shared.domain.interfaces import IEntityExistenceChecker


class TrainingJobExistenceChecker(IEntityExistenceChecker):
    """Checker for validating TrainingJob existence from other modules."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def exists(self, entity_id: int) -> bool:
        """Check if a training job with the given ID exists."""
        stmt = select(TrainingJobModel.id).where(TrainingJobModel.id == entity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_entity_type(self) -> str:
        """Return the entity type name."""
        return "TrainingJob"
