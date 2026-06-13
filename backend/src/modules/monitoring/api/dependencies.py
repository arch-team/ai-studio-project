"""Monitoring API dependencies - FastAPI dependency injection (T061)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db, get_settings

from ..application.interfaces import ISageMakerClusterClient
from ..application.services import ClusterHealthService, PrometheusService
from ..application.services.cluster_sync_service import ClusterSyncService
from ..domain.repositories import IHyperPodClusterRepository
from ..infrastructure.external import get_prometheus_client
from ..infrastructure.external.sagemaker_cluster_client import (
    get_sagemaker_cluster_client as _build_sagemaker_cluster_client,
)
from ..infrastructure.repositories import HyperPodClusterRepositoryImpl


# Repository dependencies
async def get_cluster_repository(
    session: AsyncSession = Depends(get_db),
) -> IHyperPodClusterRepository:
    """Get cluster repository instance."""
    return HyperPodClusterRepositoryImpl(session)


# External client dependencies
def get_sagemaker_cluster_client() -> ISageMakerClusterClient:
    """Get SageMaker cluster client singleton (lru_cache 工厂)."""
    return _build_sagemaker_cluster_client()


# Service dependencies
def get_prometheus_service() -> PrometheusService:
    """Get Prometheus service instance."""
    client = get_prometheus_client()
    return PrometheusService(client)


async def get_cluster_sync_service(
    cluster_repo: IHyperPodClusterRepository = Depends(get_cluster_repository),
    sagemaker_client: ISageMakerClusterClient = Depends(get_sagemaker_cluster_client),
) -> ClusterSyncService:
    """Get cluster read-through sync service instance."""
    settings = get_settings()
    return ClusterSyncService(
        cluster_repo,
        sagemaker_client,
        cluster_name=settings.hyperpod_cluster_name,
    )


async def get_cluster_health_service(
    cluster_repo: IHyperPodClusterRepository = Depends(get_cluster_repository),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> ClusterHealthService:
    """Get cluster health service instance."""
    return ClusterHealthService(cluster_repo, prometheus_service)
