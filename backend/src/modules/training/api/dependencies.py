"""Training API dependencies - Dependency injection for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db, get_settings
from src.modules.training.infrastructure.hyperpod import HyperPodClient
from src.modules.training.application.services import CheckpointService, TrainingJobService
from src.modules.training.infrastructure.repositories import (
    CheckpointRepository,
    TrainingJobRepository,
)


async def get_training_job_service(
    session: AsyncSession = Depends(get_db),
) -> TrainingJobService:
    """Dependency for TrainingJobService."""
    settings = get_settings()
    repository = TrainingJobRepository(session)
    hyperpod_client = HyperPodClient(region=settings.aws_region)
    return TrainingJobService(
        repository=repository,
        hyperpod_client=hyperpod_client,
        cluster_name=settings.hyperpod_cluster_name or "default-cluster",
    )


async def get_checkpoint_service(
    session: AsyncSession = Depends(get_db),
) -> CheckpointService:
    """Dependency for CheckpointService."""
    repository = CheckpointRepository(session)
    return CheckpointService(repository=repository)
