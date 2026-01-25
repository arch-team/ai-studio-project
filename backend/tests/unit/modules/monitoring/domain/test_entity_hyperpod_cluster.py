"""Tests for HyperPodCluster domain entity."""

import pytest

from src.modules.monitoring.domain.entities import HyperPodCluster
from src.modules.monitoring.domain.value_objects import ClusterStatus, HealthStatus
from src.shared.domain import InvalidStateTransitionError


class TestHyperPodClusterCreation:
    """HyperPodCluster 实体创建测试."""

    def test_create_with_required_fields(self) -> None:
        """使用必填字段创建集群."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test-cluster",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[{"name": "worker", "count": 2}],
            total_nodes=2,
        )
        assert cluster.id == 1
        assert cluster.cluster_name == "test-cluster"
        assert cluster.region == "us-east-1"
        assert cluster.total_nodes == 2

    def test_default_status_is_creating(self) -> None:
        """默认状态为 creating."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
        )
        assert cluster.status == ClusterStatus.CREATING

    def test_default_available_nodes_is_zero(self) -> None:
        """默认可用节点数为 0."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=10,
        )
        assert cluster.available_nodes == 0

    def test_default_health_status_is_none(self) -> None:
        """默认健康状态为 None (未知)."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
        )
        assert cluster.health_status is None

    def test_create_with_all_optional_fields(self) -> None:
        """使用所有可选字段创建集群."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="full-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/full",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[{"name": "gpu", "count": 4, "instance_type": "ml.p4d.24xlarge"}],
            total_nodes=4,
            available_nodes=4,
            total_cpu_cores=384,
            total_gpu_count=32,
            total_memory_gb=1536,
            status=ClusterStatus.ACTIVE,
            health_status=HealthStatus.HEALTHY,
            fsx_filesystem_id="fs-12345678",
            fsx_mount_point="/fsx",
            prometheus_endpoint="http://prometheus:9090",
            grafana_workspace_id="g-12345678",
        )
        assert cluster.total_cpu_cores == 384
        assert cluster.total_gpu_count == 32
        assert cluster.total_memory_gb == 1536
        assert cluster.status == ClusterStatus.ACTIVE
        assert cluster.health_status == HealthStatus.HEALTHY
        assert cluster.fsx_filesystem_id == "fs-12345678"


class TestHyperPodClusterStateTransitions:
    """状态转换测试."""

    @pytest.fixture
    def creating_cluster(self) -> HyperPodCluster:
        """创建中的集群 fixture."""
        return HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=2,
            status=ClusterStatus.CREATING,
        )

    @pytest.fixture
    def active_cluster(self) -> HyperPodCluster:
        """活跃集群 fixture."""
        return HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=2,
            status=ClusterStatus.ACTIVE,
        )

    def test_can_transition_to_active_from_creating(self, creating_cluster: HyperPodCluster) -> None:
        """从 creating 可转换到 active."""
        assert creating_cluster.can_transition_to(ClusterStatus.ACTIVE) is True

    def test_cannot_transition_to_creating_from_active(self, active_cluster: HyperPodCluster) -> None:
        """从 active 不能转换到 creating."""
        assert active_cluster.can_transition_to(ClusterStatus.CREATING) is False

    def test_transition_to_valid_status_succeeds(self, creating_cluster: HyperPodCluster) -> None:
        """有效状态转换成功."""
        creating_cluster.transition_to(ClusterStatus.ACTIVE)
        assert creating_cluster.status == ClusterStatus.ACTIVE

    def test_transition_to_invalid_status_raises_error(self, active_cluster: HyperPodCluster) -> None:
        """无效状态转换抛出异常."""
        with pytest.raises(InvalidStateTransitionError):
            active_cluster.transition_to(ClusterStatus.CREATING)

    def test_transition_updates_timestamp(self, creating_cluster: HyperPodCluster) -> None:
        """状态转换更新 updated_at."""
        old_updated_at = creating_cluster.updated_at
        creating_cluster.transition_to(ClusterStatus.ACTIVE)
        assert creating_cluster.updated_at > old_updated_at

    def test_activate_method(self, creating_cluster: HyperPodCluster) -> None:
        """activate() 方法测试."""
        creating_cluster.activate()
        assert creating_cluster.status == ClusterStatus.ACTIVE

    def test_fail_method(self, creating_cluster: HyperPodCluster) -> None:
        """fail() 方法测试."""
        creating_cluster.fail()
        assert creating_cluster.status == ClusterStatus.FAILED


class TestHyperPodClusterUtilizationMethods:
    """资源利用率方法测试."""

    def test_node_utilization_calculation(self) -> None:
        """节点利用率计算."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=10,
            available_nodes=7,
        )
        # (10 - 7) / 10 = 0.3 = 30%
        assert cluster.node_utilization == 0.3

    def test_node_utilization_zero_when_no_total(self) -> None:
        """总节点为 0 时利用率为 0."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            available_nodes=0,
        )
        assert cluster.node_utilization == 0.0

    def test_node_utilization_full(self) -> None:
        """节点全部使用时利用率为 100%."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=10,
            available_nodes=0,
        )
        assert cluster.node_utilization == 1.0

    def test_used_nodes_property(self) -> None:
        """已用节点数属性."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=10,
            available_nodes=7,
        )
        assert cluster.used_nodes == 3


class TestHyperPodClusterHealthChecks:
    """健康检查方法测试."""

    def test_is_healthy_returns_true(self) -> None:
        """健康状态检查返回 True."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            health_status=HealthStatus.HEALTHY,
        )
        assert cluster.is_healthy() is True

    def test_is_healthy_returns_false_when_degraded(self) -> None:
        """降级时健康检查返回 False."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            health_status=HealthStatus.DEGRADED,
        )
        assert cluster.is_healthy() is False

    def test_is_healthy_returns_false_when_unknown(self) -> None:
        """未知状态时健康检查返回 False."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            health_status=None,
        )
        assert cluster.is_healthy() is False

    def test_is_active_returns_true(self) -> None:
        """活跃状态检查返回 True."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            status=ClusterStatus.ACTIVE,
        )
        assert cluster.is_active() is True

    def test_is_active_returns_false_when_creating(self) -> None:
        """创建中时活跃检查返回 False."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            status=ClusterStatus.CREATING,
        )
        assert cluster.is_active() is False

    def test_is_failed_returns_true(self) -> None:
        """失败状态检查返回 True."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            status=ClusterStatus.FAILED,
        )
        assert cluster.is_failed() is True


class TestHyperPodClusterSyncMethods:
    """同步方法测试."""

    def test_mark_synced_updates_last_sync_at(self) -> None:
        """mark_synced() 更新 last_sync_at."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
        )
        assert cluster.last_sync_at is None
        cluster.mark_synced()
        assert cluster.last_sync_at is not None

    def test_update_resources_method(self) -> None:
        """update_resources() 方法测试."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
            available_nodes=0,
        )
        cluster.update_resources(
            total_nodes=8,
            available_nodes=6,
            total_cpu_cores=192,
            total_gpu_count=16,
            total_memory_gb=768,
        )
        assert cluster.total_nodes == 8
        assert cluster.available_nodes == 6
        assert cluster.total_cpu_cores == 192
        assert cluster.total_gpu_count == 16
        assert cluster.total_memory_gb == 768

    def test_update_health_method(self) -> None:
        """update_health() 方法测试."""
        cluster = HyperPodCluster(
            id=1,
            cluster_name="test-cluster",
            cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test",
            region="us-east-1",
            vpc_id="vpc-12345678",
            instance_groups=[],
            total_nodes=0,
        )
        cluster.update_health(HealthStatus.DEGRADED)
        assert cluster.health_status == HealthStatus.DEGRADED
