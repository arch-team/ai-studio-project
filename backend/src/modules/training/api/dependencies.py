"""Training API dependencies - Dependency injection for services."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.training.application.services import (
    CheckpointService,
    TrainingJobService,
)
from src.modules.training.infrastructure.hyperpod import HyperPodClient
from src.modules.training.infrastructure.repositories import (
    CheckpointRepository,
    TrainingJobRepository,
)
from src.shared.infrastructure import get_db, get_settings


@lru_cache(maxsize=1)
def get_hyperpod_client() -> HyperPodClient:
    """Singleton HyperPodClient instance."""
    settings = get_settings()
    return HyperPodClient(region=settings.aws_region)


async def get_training_job_service(
    session: AsyncSession = Depends(get_db),
) -> TrainingJobService:
    """Dependency for TrainingJobService."""
    settings = get_settings()
    repository = TrainingJobRepository(session)
    return TrainingJobService(
        repository=repository,
        hyperpod_client=get_hyperpod_client(),
        cluster_name=settings.hyperpod_cluster_name or "default-cluster",
    )


async def get_checkpoint_service(
    session: AsyncSession = Depends(get_db),
) -> CheckpointService:
    """Dependency for CheckpointService."""
    repository = CheckpointRepository(session)
    return CheckpointService(repository=repository)
