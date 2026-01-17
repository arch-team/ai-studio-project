"""Model API dependencies - Dependency injection for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.models.application.services import ModelService
from src.modules.models.infrastructure.repositories import ModelRepository
from src.modules.training.infrastructure import TrainingJobExistenceChecker
from src.shared.infrastructure.database import get_db


async def get_model_service(
    session: AsyncSession = Depends(get_db),
) -> ModelService:
    """Dependency for ModelService."""
    model_repository = ModelRepository(session)
    training_job_checker = TrainingJobExistenceChecker(session)
    # Note: checkpoint_checker would be added when checkpoint validation is needed
    return ModelService(
        model_repository=model_repository,
        training_job_checker=training_job_checker,
        checkpoint_checker=None,
    )
