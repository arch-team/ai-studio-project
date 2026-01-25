"""HyperPod cluster status and health enums."""

from enum import Enum


class ClusterStatus(Enum):
    """HyperPod 集群状态."""

    CREATING = "creating"
    ACTIVE = "active"
    UPDATING = "updating"
    DELETING = "deleting"
    FAILED = "failed"


class HealthStatus(Enum):
    """集群健康状态."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# 状态转换规则
CLUSTER_STATUS_TRANSITIONS: dict[ClusterStatus, set[ClusterStatus]] = {
    ClusterStatus.CREATING: {ClusterStatus.ACTIVE, ClusterStatus.FAILED},
    ClusterStatus.ACTIVE: {ClusterStatus.UPDATING, ClusterStatus.DELETING},
    ClusterStatus.UPDATING: {ClusterStatus.ACTIVE, ClusterStatus.FAILED},
    ClusterStatus.DELETING: {ClusterStatus.FAILED},  # 删除成功后记录移除
    ClusterStatus.FAILED: {ClusterStatus.CREATING},  # 可重试
}
