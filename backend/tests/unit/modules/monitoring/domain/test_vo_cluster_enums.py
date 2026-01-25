"""Tests for monitoring domain value objects (cluster enums)."""

from src.modules.monitoring.domain.value_objects import (
    CLUSTER_STATUS_TRANSITIONS,
    ClusterStatus,
    HealthStatus,
)


class TestClusterStatusEnum:
    """ClusterStatus 枚举测试."""

    def test_all_statuses_defined(self) -> None:
        """验证所有必需状态已定义."""
        expected_statuses = {"CREATING", "ACTIVE", "UPDATING", "DELETING", "FAILED"}
        actual_statuses = {s.name for s in ClusterStatus}
        assert actual_statuses == expected_statuses

    def test_status_values_match_database(self) -> None:
        """验证枚举值与数据库 ENUM 一致 (小写)."""
        assert ClusterStatus.CREATING.value == "creating"
        assert ClusterStatus.ACTIVE.value == "active"
        assert ClusterStatus.UPDATING.value == "updating"
        assert ClusterStatus.DELETING.value == "deleting"
        assert ClusterStatus.FAILED.value == "failed"

    def test_status_from_value(self) -> None:
        """验证可从字符串值创建枚举."""
        assert ClusterStatus("creating") == ClusterStatus.CREATING
        assert ClusterStatus("active") == ClusterStatus.ACTIVE


class TestHealthStatusEnum:
    """HealthStatus 枚举测试."""

    def test_all_health_statuses_defined(self) -> None:
        """验证所有健康状态已定义."""
        expected_statuses = {"HEALTHY", "DEGRADED", "UNHEALTHY"}
        actual_statuses = {s.name for s in HealthStatus}
        assert actual_statuses == expected_statuses

    def test_health_status_values_match_database(self) -> None:
        """验证枚举值与数据库 ENUM 一致 (小写)."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_status_from_value(self) -> None:
        """验证可从字符串值创建枚举."""
        assert HealthStatus("healthy") == HealthStatus.HEALTHY
        assert HealthStatus("degraded") == HealthStatus.DEGRADED


class TestClusterStatusTransitions:
    """状态转换规则测试."""

    def test_creating_can_transition_to_active(self) -> None:
        """creating → active 是有效转换."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.CREATING]
        assert ClusterStatus.ACTIVE in valid_targets

    def test_creating_can_transition_to_failed(self) -> None:
        """creating → failed 是有效转换."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.CREATING]
        assert ClusterStatus.FAILED in valid_targets

    def test_active_can_transition_to_updating(self) -> None:
        """active → updating 是有效转换."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.ACTIVE]
        assert ClusterStatus.UPDATING in valid_targets

    def test_active_can_transition_to_deleting(self) -> None:
        """active → deleting 是有效转换."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.ACTIVE]
        assert ClusterStatus.DELETING in valid_targets

    def test_active_cannot_transition_to_creating(self) -> None:
        """active → creating 是无效转换."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.ACTIVE]
        assert ClusterStatus.CREATING not in valid_targets

    def test_updating_can_transition_to_active(self) -> None:
        """updating → active 是有效转换."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.UPDATING]
        assert ClusterStatus.ACTIVE in valid_targets

    def test_updating_can_transition_to_failed(self) -> None:
        """updating → failed 是有效转换."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.UPDATING]
        assert ClusterStatus.FAILED in valid_targets

    def test_deleting_can_only_transition_to_failed(self) -> None:
        """deleting 只能转换到 failed (删除成功后记录移除)."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.DELETING]
        assert valid_targets == {ClusterStatus.FAILED}

    def test_failed_can_retry_by_transitioning_to_creating(self) -> None:
        """failed → creating 是有效转换 (重试)."""
        valid_targets = CLUSTER_STATUS_TRANSITIONS[ClusterStatus.FAILED]
        assert ClusterStatus.CREATING in valid_targets

    def test_all_statuses_have_transitions_defined(self) -> None:
        """验证所有状态都定义了转换规则."""
        for status in ClusterStatus:
            assert status in CLUSTER_STATUS_TRANSITIONS, f"{status} 缺少转换规则"
