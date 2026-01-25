"""Monitoring API dependencies - FastAPI dependency injection (T061)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db

from ..application.services import ClusterHealthService, PrometheusService
from ..domain.repositories import IHyperPodClusterRepository
from ..infrastructure.external import get_prometheus_client
from ..infrastructure.repositories import HyperPodClusterRepositoryImpl


# Repository dependencies
async def get_cluster_repository(
    session: AsyncSession = Depends(get_db),
) -> IHyperPodClusterRepository:
    """Get cluster repository instance."""
    return HyperPodClusterRepositoryImpl(session)


# Service dependencies
def get_prometheus_service() -> PrometheusService:
    """Get Prometheus service instance."""
    client = get_prometheus_client()
    return PrometheusService(client)


async def get_cluster_health_service(
    cluster_repo: IHyperPodClusterRepository = Depends(get_cluster_repository),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> ClusterHealthService:
    """Get cluster health service instance."""
    return ClusterHealthService(cluster_repo, prometheus_service)
