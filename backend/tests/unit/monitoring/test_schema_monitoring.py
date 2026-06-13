"""监控页响应 Schema 测试（对齐前端 TS 契约）.

真源: frontend/src/features/monitoring/types/index.ts
覆盖: ClusterSummary/ClusterDetail/NodeSummary、ResourceUtilization、
      MetricSeries、Alert 及其分页列表响应。

可空性测试关键: 前端将 health_status/total_gpu_count/last_sync_at 等标记为可空，
后端 schema 必须允许 None，否则真实 describe-cluster 缺字段时 500。
"""

import pytest


class TestClusterSummaryResponse:
    """ClusterSummaryResponse 字段与可空性."""

    def test_cluster_summary_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import ClusterSummaryResponse

        fields = ClusterSummaryResponse.model_fields
        for f in [
            "id",
            "cluster_name",
            "cluster_arn",
            "region",
            "status",
            "health_status",
            "total_nodes",
            "available_nodes",
            "total_gpu_count",
            "available_gpu_count",
            "total_cpu_cores",
            "available_cpu_cores",
            "last_sync_at",
            "created_at",
        ]:
            assert f in fields

    def test_cluster_summary_nullable_fields_accept_none(self) -> None:
        from src.modules.monitoring.api.schemas.responses import ClusterSummaryResponse

        obj = ClusterSummaryResponse(
            id=1,
            cluster_name="c",
            cluster_arn="arn",
            region="us-east-1",
            status="active",
            total_nodes=3,
            available_nodes=3,
            created_at="2026-06-13T00:00:00Z",
        )
        assert obj.health_status is None
        assert obj.total_gpu_count is None
        assert obj.available_gpu_count is None
        assert obj.total_cpu_cores is None
        assert obj.available_cpu_cores is None
        assert obj.last_sync_at is None


class TestClusterListResponse:
    """ClusterListResponse 链路（端点 2C.4 首先使用）."""

    def test_cluster_list_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import ClusterListResponse

        for f in ["items", "total"]:
            assert f in ClusterListResponse.model_fields

    def test_cluster_list_response_defaults(self) -> None:
        from src.modules.monitoring.api.schemas.responses import ClusterListResponse

        obj = ClusterListResponse()
        assert obj.items == []
        assert obj.total == 0


class TestClusterDetailResponse:
    """ClusterDetailResponse 继承 Summary 并扩展字段."""

    def test_cluster_detail_response_extends_summary(self) -> None:
        from src.modules.monitoring.api.schemas.responses import (
            ClusterDetailResponse,
            ClusterSummaryResponse,
        )

        assert issubclass(ClusterDetailResponse, ClusterSummaryResponse)

    def test_cluster_detail_response_extra_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import ClusterDetailResponse

        fields = ClusterDetailResponse.model_fields
        for f in [
            "vpc_id",
            "instance_groups",
            "total_memory_gb",
            "available_memory_gb",
            "fsx_filesystem_id",
            "fsx_mount_point",
            "prometheus_endpoint",
            "grafana_workspace_id",
            "running_jobs_count",
            "pending_jobs_count",
            "updated_at",
        ]:
            assert f in fields

    def test_cluster_detail_nullable_fields_accept_none(self) -> None:
        from src.modules.monitoring.api.schemas.responses import ClusterDetailResponse

        obj = ClusterDetailResponse(
            id=1,
            cluster_name="c",
            cluster_arn="arn",
            region="us-east-1",
            status="active",
            total_nodes=3,
            available_nodes=3,
            created_at="2026-06-13T00:00:00Z",
            vpc_id="vpc-1",
            running_jobs_count=0,
            pending_jobs_count=0,
            updated_at="2026-06-13T00:00:00Z",
        )
        assert obj.total_memory_gb is None
        assert obj.available_memory_gb is None
        assert obj.fsx_filesystem_id is None
        assert obj.fsx_mount_point is None
        assert obj.prometheus_endpoint is None
        assert obj.grafana_workspace_id is None
        assert obj.instance_groups == []


class TestInstanceGroupResponse:
    """InstanceGroupResponse 字段（ClusterDetail.instance_groups 元素）."""

    def test_instance_group_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import InstanceGroupResponse

        fields = InstanceGroupResponse.model_fields
        for f in [
            "instance_group_name",
            "instance_type",
            "instance_count",
            "available_count",
            "capacity_type",
            "spot_interruption_behavior",
        ]:
            assert f in fields

    def test_instance_group_spot_behavior_accepts_none(self) -> None:
        from src.modules.monitoring.api.schemas.responses import InstanceGroupResponse

        obj = InstanceGroupResponse(
            instance_group_name="g1",
            instance_type="ml.g5.xlarge",
            instance_count=2,
            available_count=1,
            capacity_type="on_demand",
        )
        assert obj.spot_interruption_behavior is None


class TestNodeSummaryResponse:
    """NodeSummaryResponse / NodeListResponse."""

    def test_node_summary_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import NodeSummaryResponse

        fields = NodeSummaryResponse.model_fields
        for f in [
            "node_name",
            "instance_type",
            "instance_group",
            "status",
            "cpu_capacity",
            "cpu_used",
            "memory_capacity_gb",
            "memory_used_gb",
            "gpu_capacity",
            "gpu_used",
            "pod_count",
            "age",
        ]:
            assert f in fields

    def test_node_list_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import NodeListResponse

        for f in ["items", "total"]:
            assert f in NodeListResponse.model_fields


class TestResourceUtilizationResponse:
    """ResourceUtilizationResponse 字段."""

    def test_resource_utilization_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import ResourceUtilizationResponse

        for f in ["resource_type", "total", "used", "available", "utilization_percentage", "unit"]:
            assert f in ResourceUtilizationResponse.model_fields


class TestMetricSeriesResponse:
    """MetricSeriesResponse 字段及 MetricDataPointResponse 复用."""

    def test_metric_series_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import MetricSeriesResponse

        for f in ["metric_name", "labels", "data_points"]:
            assert f in MetricSeriesResponse.model_fields

    def test_metric_series_reuses_metric_data_point(self) -> None:
        from src.modules.monitoring.api.schemas.responses import (
            MetricDataPointResponse,
            MetricSeriesResponse,
        )

        obj = MetricSeriesResponse(metric_name="cpu", labels={"node": "n1"})
        assert obj.data_points == []
        # data_points 元素类型应为现有 MetricDataPointResponse
        point = MetricDataPointResponse(timestamp="2026-06-13T00:00:00Z", value=0.5)
        obj_with_point = MetricSeriesResponse(metric_name="cpu", data_points=[point])
        assert obj_with_point.data_points[0].value == 0.5


class TestAlertResponse:
    """AlertResponse / AlertListResponse."""

    def test_alert_response_fields(self) -> None:
        from src.modules.monitoring.api.schemas.responses import AlertResponse

        fields = AlertResponse.model_fields
        for f in [
            "id",
            "severity",
            "title",
            "message",
            "source",
            "resource_type",
            "resource_id",
            "fired_at",
            "resolved_at",
            "status",
        ]:
            assert f in fields

    def test_alert_resolved_at_accepts_none(self) -> None:
        from src.modules.monitoring.api.schemas.responses import AlertResponse

        obj = AlertResponse(
            id="a-1",
            severity="warning",
            title="t",
            message="m",
            source="prometheus",
            resource_type="cluster",
            resource_id="1",
            fired_at="2026-06-13T00:00:00Z",
            status="firing",
        )
        assert obj.resolved_at is None

    def test_alert_list_response_is_paginated(self) -> None:
        from src.modules.monitoring.api.schemas.responses import AlertListResponse

        for f in ["items", "total", "page", "page_size", "total_pages"]:
            assert f in AlertListResponse.model_fields

    def test_alert_list_response_pagination_defaults(self) -> None:
        from src.modules.monitoring.api.schemas.responses import AlertListResponse

        obj = AlertListResponse()
        assert obj.items == []
        assert obj.total == 0
        assert obj.page == 1
        assert obj.page_size == 20
        assert obj.total_pages == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
