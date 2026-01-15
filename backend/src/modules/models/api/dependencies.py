"""Model API dependencies - Dependency injection for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database import get_db
from src.modules.models.application.services import ModelService
from src.modules.models.infrastructure.repositories import ModelRepository
from src.modules.training.infrastructure.repositories import TrainingJobRepository


async def get_model_service(
    session: AsyncSession = Depends(get_db),
) -> ModelService:
    """Dependency for ModelService."""
    model_repository = ModelRepository(session)
    training_job_repository = TrainingJobRepository(session)
    # Note: checkpoint_repository would be added when checkpoint service is implemented
    return ModelService(
        model_repository=model_repository,
        training_job_repository=training_job_repository,
        checkpoint_repository=None,
    )
