"""HyperPodCluster domain entity."""

from datetime import datetime

from pydantic import Field

from src.shared.domain import PydanticEntity
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.utils import utc_now

from ..value_objects import CLUSTER_STATUS_TRANSITIONS, ClusterStatus, HealthStatus


class HyperPodCluster(PydanticEntity):
    """HyperPod 集群域实体.

    表示 AWS SageMaker HyperPod 集群的业务模型。
    此实体是 HyperPod API 的本地缓存，源真实来自 HyperPod/K8s API。
    """

    # === 必填字段 ===
    cluster_name: str = Field(min_length=1, max_length=255)
    cluster_arn: str
    region: str
    vpc_id: str
    instance_groups: list[dict] = Field(default_factory=list)
    total_nodes: int

    # === 可选字段 ===
    available_nodes: int = 0
    total_cpu_cores: int | None = None
    total_gpu_count: int | None = None
    total_memory_gb: int | None = None

    # === 状态字段 ===
    status: ClusterStatus = ClusterStatus.CREATING
    health_status: HealthStatus | None = None

    # === FSx 集成 ===
    fsx_filesystem_id: str | None = None
    fsx_mount_point: str | None = None

    # === 监控集成 ===
    prometheus_endpoint: str | None = None
    grafana_workspace_id: str | None = None

    # === 时间戳 ===
    last_sync_at: datetime | None = None

    # ========== 状态转换方法 ==========

    def can_transition_to(self, new_status: ClusterStatus) -> bool:
        """检查是否可以转换到新状态."""
        valid_transitions = CLUSTER_STATUS_TRANSITIONS.get(self.status, set())
        return new_status in valid_transitions

    def transition_to(self, new_status: ClusterStatus) -> None:
        """转换到新状态."""
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                entity_type="HyperPodCluster",
                current_state=self.status.value,
                target_state=new_status.value,
            )
        self.status = new_status
        self.touch()

    def activate(self) -> None:
        """激活集群 (creating/updating → active)."""
        self.transition_to(ClusterStatus.ACTIVE)

    def fail(self) -> None:
        """标记集群失败."""
        self.transition_to(ClusterStatus.FAILED)

    def start_update(self) -> None:
        """开始更新集群 (active → updating)."""
        self.transition_to(ClusterStatus.UPDATING)

    def start_delete(self) -> None:
        """开始删除集群 (active → deleting)."""
        self.transition_to(ClusterStatus.DELETING)

    # ========== 资源利用率属性 ==========

    @property
    def used_nodes(self) -> int:
        """已用节点数."""
        return self.total_nodes - self.available_nodes

    @property
    def node_utilization(self) -> float:
        """节点利用率 (0.0 - 1.0)."""
        if self.total_nodes == 0:
            return 0.0
        return self.used_nodes / self.total_nodes

    # ========== 状态检查方法 ==========

    def is_active(self) -> bool:
        """检查集群是否活跃."""
        return self.status == ClusterStatus.ACTIVE

    def is_healthy(self) -> bool:
        """检查集群是否健康."""
        return self.health_status == HealthStatus.HEALTHY

    def is_failed(self) -> bool:
        """检查集群是否失败."""
        return self.status == ClusterStatus.FAILED

    def is_creating(self) -> bool:
        """检查集群是否创建中."""
        return self.status == ClusterStatus.CREATING

    # ========== 同步方法 ==========

    def mark_synced(self) -> None:
        """标记已同步."""
        self.last_sync_at = utc_now()
        self.touch()

    def update_resources(
        self,
        total_nodes: int,
        available_nodes: int,
        total_cpu_cores: int | None = None,
        total_gpu_count: int | None = None,
        total_memory_gb: int | None = None,
    ) -> None:
        """更新资源信息."""
        self.total_nodes = total_nodes
        self.available_nodes = available_nodes
        self.total_cpu_cores = total_cpu_cores
        self.total_gpu_count = total_gpu_count
        self.total_memory_gb = total_memory_gb
        self.touch()

    def update_health(self, health_status: HealthStatus) -> None:
        """更新健康状态."""
        self.health_status = health_status
        self.touch()
