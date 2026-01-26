"""HyperPodCluster Repository Implementation (T068)."""

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import HyperPodCluster
from ...domain.repositories import IHyperPodClusterRepository
from ...domain.value_objects import ClusterStatus
from ..models import HyperPodClusterModel


class HyperPodClusterRepositoryImpl(
    PydanticRepository[HyperPodCluster, HyperPodClusterModel, int],
    IHyperPodClusterRepository,
):
    """SQLAlchemy implementation of HyperPodCluster repository."""

    _entity_class = HyperPodCluster
    _updatable_fields = [
        "cluster_name",
        "cluster_arn",
        "region",
        "vpc_id",
        "instance_groups",
        "total_nodes",
        "available_nodes",
        "total_cpu_cores",
        "total_gpu_count",
        "total_memory_gb",
        "status",
        "health_status",
        "prometheus_endpoint",
        "grafana_workspace_id",
        "fsx_filesystem_id",
        "fsx_mount_point",
        "last_sync_at",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, HyperPodClusterModel)

    # ========== IHyperPodClusterRepository 接口方法 ==========

    async def get_by_name(self, cluster_name: str) -> HyperPodCluster | None:
        """Get cluster by name."""
        result = await self._session.execute(
            select(HyperPodClusterModel).where(HyperPodClusterModel.cluster_name == cluster_name)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_arn(self, cluster_arn: str) -> HyperPodCluster | None:
        """Get cluster by ARN."""
        result = await self._session.execute(
            select(HyperPodClusterModel).where(HyperPodClusterModel.cluster_arn == cluster_arn)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

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
