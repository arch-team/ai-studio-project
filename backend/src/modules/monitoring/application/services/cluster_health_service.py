"""集群健康检查服务 (T068).

提供集群健康状态检查、状态同步和定时任务入口。
"""

from dataclasses import dataclass
from datetime import datetime

from src.shared.domain.exceptions import EntityNotFoundError
from src.shared.utils import utc_now

from ...domain.repositories import IHyperPodClusterRepository
from ...domain.value_objects import HealthStatus
from .prometheus_service import PrometheusService


@dataclass
class HealthCheckResult:
    """健康检查结果."""

    cluster_id: int
    cluster_name: str
    status: HealthStatus
    storage_alerts: list
    network_alerts: list
    checked_at: datetime


class ClusterHealthService:
    """集群健康检查服务.

    负责检查集群健康状态、同步状态到数据库、作为定时任务入口。
    """

    def __init__(
        self,
        cluster_repository: IHyperPodClusterRepository,
        prometheus_service: PrometheusService,
    ):
        self._cluster_repository = cluster_repository
        self._prometheus_service = prometheus_service

    async def check_health(self, cluster_id: int) -> HealthCheckResult:
        """检查集群健康状态.

        Args:
            cluster_id: 集群 ID

        Returns:
            健康检查结果

        Raises:
            EntityNotFoundError: 集群不存在
        """
        cluster = await self._cluster_repository.get_by_id(cluster_id)
        if cluster is None:
            raise EntityNotFoundError(entity_type="HyperPodCluster", entity_id=str(cluster_id))

        # 检查存储告警
        storage_alerts = await self._prometheus_service.check_storage_alerts()

        # 检查网络告警
        network_alerts = await self._prometheus_service.check_network_alerts()

        # 判断健康状态
        health_status = self._determine_health_status(storage_alerts, network_alerts)

        assert cluster.id is not None, "Cluster must have ID"
        return HealthCheckResult(
            cluster_id=cluster.id,
            cluster_name=cluster.cluster_name,
            status=health_status,
            storage_alerts=storage_alerts,
            network_alerts=network_alerts,
            checked_at=utc_now(),
        )

    async def sync_cluster_status(self, cluster_id: int) -> None:
        """同步集群健康状态到数据库.

        Args:
            cluster_id: 集群 ID

        Raises:
            EntityNotFoundError: 集群不存在
        """
        # check_health 内部已验证集群存在性，无需重复查询
        health_result = await self.check_health(cluster_id)

        # 重新获取集群实体来更新状态（check_health 不持有可变引用）
        cluster = await self._cluster_repository.get_by_id(cluster_id)
        if cluster is None:
            raise EntityNotFoundError(entity_type="HyperPodCluster", entity_id=str(cluster_id))

        cluster.update_health(health_result.status)
        await self._cluster_repository.update(cluster)

    async def run_health_check_task(self) -> list[HealthCheckResult]:
        """定时任务入口 - 检查所有活跃集群.

        Returns:
            所有集群的健康检查结果列表
        """
        from ...domain.value_objects import ClusterStatus

        # 获取所有活跃集群
        clusters = await self._cluster_repository.list_clusters(
            status=ClusterStatus.ACTIVE,
            limit=100,
        )

        results: list[HealthCheckResult] = []
        for cluster in clusters:
            if cluster.id is None:
                continue
            try:
                result = await self.check_health(cluster.id)
                # 同步状态
                cluster.update_health(result.status)
                await self._cluster_repository.update(cluster)
                results.append(result)
            except Exception:
                # 记录错误但继续检查其他集群
                continue

        return results

    def _determine_health_status(
        self,
        storage_alerts: list,
        network_alerts: list,
    ) -> HealthStatus:
        """根据告警判断健康状态."""
        all_alerts = storage_alerts + network_alerts

        if not all_alerts:
            return HealthStatus.HEALTHY

        # critical 或 high 级别告警视为不健康
        severities = {getattr(a, "severity", "") for a in all_alerts}
        if severities & {"critical", "high"}:
            return HealthStatus.UNHEALTHY

        return HealthStatus.DEGRADED
