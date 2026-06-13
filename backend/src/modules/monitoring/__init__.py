"""Monitoring module - Cluster monitoring and alerting for AI training platform.

提供 HyperPod 集群健康检查、状态同步和 Prometheus (AMP) 指标查询能力。

注意: 本模块有两个 router（`monitoring` 前缀与无前缀的 `/clusters*`），
由 `src/router.py` 直接从对应 api 子模块聚合，故顶层包不导出 `router`。
"""

from .application.services import ClusterHealthService, PrometheusService
from .application.services.cluster_sync_service import ClusterSyncService
from .domain.entities import HyperPodCluster
from .domain.repositories import IHyperPodClusterRepository
from .domain.value_objects import ClusterStatus, HealthStatus

__all__ = [
    # Services
    "PrometheusService",
    "ClusterHealthService",
    "ClusterSyncService",
    # Entities
    "HyperPodCluster",
    # Value Objects
    "ClusterStatus",
    "HealthStatus",
    # Repositories (interface)
    "IHyperPodClusterRepository",
]
