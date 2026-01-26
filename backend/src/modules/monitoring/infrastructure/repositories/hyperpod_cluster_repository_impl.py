"""HyperPodCluster Repository Implementation (T068)."""

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.base_repository import BaseRepository

from ...domain.entities import HyperPodCluster
from ...domain.repositories import IHyperPodClusterRepository
from ...domain.value_objects import ClusterStatus, HealthStatus
from ..models import HyperPodClusterModel


class HyperPodClusterRepositoryImpl(
    BaseRepository[HyperPodCluster, HyperPodClusterModel, int],
    IHyperPodClusterRepository,
):
    """SQLAlchemy implementation of HyperPodCluster repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, HyperPodClusterModel)

    def _to_entity(self, model: HyperPodClusterModel) -> HyperPodCluster:
        """Convert ORM model to domain entity."""
        return HyperPodCluster(
            id=model.id,
            cluster_name=model.cluster_name,
            cluster_arn=model.cluster_arn,
            region=model.region,
            vpc_id=model.vpc_id,
            instance_groups=model.instance_groups or [],
            total_nodes=model.total_nodes,
            available_nodes=model.available_nodes,
            total_cpu_cores=model.total_cpu_cores,
            total_gpu_count=model.total_gpu_count,
            total_memory_gb=model.total_memory_gb,
            status=ClusterStatus(model.status.value) if model.status else ClusterStatus.CREATING,
            health_status=(HealthStatus(model.health_status.value) if model.health_status else None),
            prometheus_endpoint=model.prometheus_endpoint,
            grafana_workspace_id=model.grafana_workspace_id,
            fsx_filesystem_id=model.fsx_filesystem_id,
            fsx_mount_point=model.fsx_mount_point,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_sync_at=model.last_sync_at,
        )

    def _to_model(self, entity: HyperPodCluster) -> HyperPodClusterModel:
        """Convert domain entity to ORM model."""
        return HyperPodClusterModel(
            id=entity.id if entity.id else None,
            cluster_name=entity.cluster_name,
            cluster_arn=entity.cluster_arn,
            region=entity.region,
            vpc_id=entity.vpc_id,
            instance_groups=entity.instance_groups,
            total_nodes=entity.total_nodes,
            available_nodes=entity.available_nodes,
            total_cpu_cores=entity.total_cpu_cores,
            total_gpu_count=entity.total_gpu_count,
            total_memory_gb=entity.total_memory_gb,
            status=ClusterStatus(entity.status.value),
            health_status=(HealthStatus(entity.health_status.value) if entity.health_status else None),
            prometheus_endpoint=entity.prometheus_endpoint,
            grafana_workspace_id=entity.grafana_workspace_id,
            fsx_filesystem_id=entity.fsx_filesystem_id,
            fsx_mount_point=entity.fsx_mount_point,
            last_sync_at=entity.last_sync_at,
        )

    def _update_model(self, model: HyperPodClusterModel, entity: HyperPodCluster) -> None:
        """Update ORM model fields from entity."""
        model.cluster_name = entity.cluster_name
        model.cluster_arn = entity.cluster_arn
        model.region = entity.region
        model.vpc_id = entity.vpc_id
        model.instance_groups = entity.instance_groups
        model.total_nodes = entity.total_nodes
        model.available_nodes = entity.available_nodes
        model.total_cpu_cores = entity.total_cpu_cores
        model.total_gpu_count = entity.total_gpu_count
        model.total_memory_gb = entity.total_memory_gb
        model.status = ClusterStatus(entity.status.value)
        model.health_status = HealthStatus(entity.health_status.value) if entity.health_status else None
        model.prometheus_endpoint = entity.prometheus_endpoint
        model.grafana_workspace_id = entity.grafana_workspace_id
        model.fsx_filesystem_id = entity.fsx_filesystem_id
        model.fsx_mount_point = entity.fsx_mount_point
        model.last_sync_at = entity.last_sync_at

    async def get_by_name(self, cluster_name: str) -> HyperPodCluster | None:
        """Get cluster by name."""
        result = await self._session.execute(
            select(HyperPodClusterModel).where(HyperPodClusterModel.cluster_name == cluster_name)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_arn(self, cluster_arn: str) -> HyperPodCluster | None:
        """Get cluster by ARN."""
        result = await self._session.execute(
            select(HyperPodClusterModel).where(HyperPodClusterModel.cluster_arn == cluster_arn)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def list_clusters(
        self,
        offset: int = 0,
        limit: int = 20,
        status: ClusterStatus | None = None,
    ) -> list[HyperPodCluster]:
        """List clusters with pagination and optional status filter."""
        stmt = select(HyperPodClusterModel)

        if status is not None:
            stmt = stmt.where(HyperPodClusterModel.status == status)

        stmt = stmt.order_by(desc(HyperPodClusterModel.created_at))
        stmt = stmt.offset(offset).limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count_clusters(
        self,
        status: ClusterStatus | None = None,
    ) -> int:
        """Count clusters with optional status filter."""
        stmt = select(func.count(HyperPodClusterModel.id))

        if status is not None:
            stmt = stmt.where(HyperPodClusterModel.status == status)

        result = await self._session.execute(stmt)
        return result.scalar_one()
