"""Training API dependencies - Dependency injection for services."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.quotas.infrastructure import QuotaCheckerImpl, ResourceQuotaRepository
from src.modules.training.application.interfaces import IMetricsService
from src.modules.training.application.services import (
    CheckpointService,
    JobTemplateService,
    MLflowService,
    TrainingJobService,
)
from src.modules.training.infrastructure.hyperpod import HyperPodClient
from src.modules.training.infrastructure.repositories import (
    CheckpointRepository,
    JobTemplateRepository,
    TrainingJobRepository,
)
from src.shared.domain.interfaces import IQuotaChecker
from src.shared.infrastructure import get_db, get_settings


@lru_cache(maxsize=1)
def get_hyperpod_client() -> HyperPodClient:
    """Singleton HyperPodClient instance."""
    settings = get_settings()
    return HyperPodClient(region=settings.aws_region)


async def get_quota_checker(
    session: AsyncSession = Depends(get_db),
) -> IQuotaChecker:
    """Dependency for IQuotaChecker (CE-01-05)."""
    quota_repository = ResourceQuotaRepository(session)
    return QuotaCheckerImpl(quota_repository)


async def get_training_job_service(
    session: AsyncSession = Depends(get_db),
) -> TrainingJobService:
    """Dependency for TrainingJobService."""
    settings = get_settings()
    repository = TrainingJobRepository(session)
    checkpoint_repository = CheckpointRepository(session)
    quota_repository = ResourceQuotaRepository(session)
    quota_checker = QuotaCheckerImpl(quota_repository)
    return TrainingJobService(
        repository=repository,
        hyperpod_client=get_hyperpod_client(),
        cluster_name=settings.hyperpod_cluster_name or "default-cluster",
        checkpoint_repository=checkpoint_repository,
        quota_checker=quota_checker,
    )


async def get_checkpoint_service(
    session: AsyncSession = Depends(get_db),
) -> CheckpointService:
    """Dependency for CheckpointService."""
    repository = CheckpointRepository(session)
    return CheckpointService(repository=repository)


async def get_job_template_service(
    session: AsyncSession = Depends(get_db),
) -> JobTemplateService:
    """Dependency for JobTemplateService."""
    repository = JobTemplateRepository(session)
    return JobTemplateService(repository=repository)


@lru_cache(maxsize=1)
def get_mlflow_service() -> IMetricsService:
    """Singleton MLflowService instance (T037a)."""
    settings = get_settings()
    return MLflowService(
        tracking_uri=settings.mlflow_tracking_uri,
        experiment_prefix=settings.mlflow_experiment_prefix,
        timeout=settings.mlflow_request_timeout,
        max_retries=settings.mlflow_max_retries,
    )
