"""监控 API 端点 (T061).

提供集群指标、GPU 利用率、存储/网络监控和 Grafana 仪表盘 API。
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from src.modules.auth.api.dependencies import get_current_active_user
from src.shared.utils import utc_now

from ..application.services import ClusterHealthService, PrometheusService
from .dependencies import get_cluster_health_service, get_prometheus_service
from .schemas import (
    ClusterHealthResponse,
    ClusterMetricsResponse,
    GPUUtilizationPointResponse,
    GPUUtilizationResponse,
    GrafanaDashboardInfo,
    GrafanaDashboardsResponse,
    MetricDataPointResponse,
    MetricResponse,
    NetworkMetricsResponse,
    StorageMetricsResponse,
)

router = APIRouter()


@router.get("/clusters/{cluster_name}/metrics", response_model=ClusterMetricsResponse)
async def get_cluster_metrics(
    cluster_name: str,
    metric_names: str | None = Query(None, description="逗号分隔的指标名称"),
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    _: None = Depends(get_current_active_user),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> ClusterMetricsResponse:
    """获取集群指标 (T061).

    查询 Prometheus 获取集群监控指标。
    """
    # 默认时间范围: 最近 1 小时
    if end_time is None:
        end_time = utc_now()
    if start_time is None:
        start_time = end_time - timedelta(hours=1)

    # 默认指标
    if metric_names:
        names = [n.strip() for n in metric_names.split(",")]
    else:
        names = [
            "DCGM_FI_DEV_GPU_UTIL",
            "node_cpu_usage",
            "node_memory_usage",
        ]

    try:
        result = await prometheus_service.query_metrics(
            metric_names=names,
            start_time=start_time,
            end_time=end_time,
        )

        metrics = []
        for name, data_points in result.items():
            metrics.append(
                MetricResponse(
                    metric_name=name,
                    data_points=[
                        MetricDataPointResponse(
                            timestamp=dp.timestamp,
                            value=dp.value,
                        )
                        for dp in data_points
                    ],
                )
            )

        return ClusterMetricsResponse(cluster_name=cluster_name, metrics=metrics)
    except Exception:
        # Prometheus 不可用时返回空结果
        return ClusterMetricsResponse(cluster_name=cluster_name, metrics=[])


@router.get("/jobs/{job_id}/gpu-utilization", response_model=GPUUtilizationResponse)
async def get_job_gpu_utilization(
    job_id: int,
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    _: None = Depends(get_current_active_user),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> GPUUtilizationResponse:
    """获取训练任务的 GPU 利用率."""
    if end_time is None:
        end_time = utc_now()
    if start_time is None:
        start_time = end_time - timedelta(hours=1)

    try:
        result = await prometheus_service.get_gpu_utilization(
            cluster_name="default",  # TODO: 从任务获取集群名称
            start_time=start_time,
            end_time=end_time,
        )

        data_points = [
            GPUUtilizationPointResponse(
                gpu_id=dp.gpu_id,
                instance=dp.instance,
                timestamp=dp.timestamp,
                utilization_percent=dp.utilization_percent,
            )
            for dp in result
        ]

        return GPUUtilizationResponse(job_id=job_id, data_points=data_points)
    except Exception:
        return GPUUtilizationResponse(job_id=job_id, data_points=[])


@router.get("/grafana/dashboards", response_model=GrafanaDashboardsResponse)
async def get_grafana_dashboards(
    _: None = Depends(get_current_active_user),
) -> GrafanaDashboardsResponse:
    """获取 Grafana 仪表盘列表 (T063)."""
    # 返回预配置的仪表盘列表
    dashboards = [
        GrafanaDashboardInfo(
            id="hyperpod-overview",
            name="HyperPod 集群概览",
            url="/grafana/d/hyperpod-overview",
            description="集群健康状态、GPU 利用率、训练任务分布",
        ),
        GrafanaDashboardInfo(
            id="training-jobs",
            name="训练任务监控",
            url="/grafana/d/training-jobs",
            description="训练任务状态、资源使用、性能指标",
        ),
        GrafanaDashboardInfo(
            id="storage-capacity",
            name="存储容量监控",
            url="/grafana/d/storage-capacity",
            description="FSx 存储使用率、趋势分析",
        ),
        GrafanaDashboardInfo(
            id="network-performance",
            name="网络性能监控",
            url="/grafana/d/network-performance",
            description="网络延迟、带宽、丢包率",
        ),
    ]

    return GrafanaDashboardsResponse(dashboards=dashboards)


@router.get("/storage", response_model=StorageMetricsResponse)
async def get_storage_metrics(
    _: None = Depends(get_current_active_user),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> StorageMetricsResponse:
    """获取存储指标 (FR-020)."""
    try:
        result = await prometheus_service.get_storage_capacity_metrics()
        return StorageMetricsResponse(
            total_bytes=result.total_bytes,
            used_bytes=result.used_bytes,
            available_bytes=result.available_bytes,
            usage_percent=result.usage_percent,
            mountpoint=result.mountpoint,
        )
    except Exception:
        # Prometheus 不可用时返回默认值
        return StorageMetricsResponse(
            total_bytes=0,
            used_bytes=0,
            available_bytes=0,
            usage_percent=0,
            mountpoint="/fsx",
        )


@router.get("/network", response_model=NetworkMetricsResponse)
async def get_network_metrics(
    _: None = Depends(get_current_active_user),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> NetworkMetricsResponse:
    """获取网络指标 (FR-021)."""
    try:
        result = await prometheus_service.get_network_metrics()
        return NetworkMetricsResponse(
            latency_ms=result.latency_ms,
            bandwidth_mbps=result.bandwidth_mbps,
            packet_loss_percent=result.packet_loss_percent,
            interface=result.interface,
        )
    except Exception:
        # Prometheus 不可用时返回默认值
        return NetworkMetricsResponse(
            latency_ms=0,
            bandwidth_mbps=0,
            packet_loss_percent=0,
            interface="eth0",
        )


@router.get("/clusters/{cluster_name}/health", response_model=ClusterHealthResponse)
async def get_cluster_health(
    cluster_name: str,
    _: None = Depends(get_current_active_user),
    health_service: ClusterHealthService = Depends(get_cluster_health_service),
) -> ClusterHealthResponse:
    """获取集群健康状态 (T068)."""
    from ...domain.repositories import IHyperPodClusterRepository

    # 首先通过名称获取集群
    cluster_repo: IHyperPodClusterRepository = health_service._cluster_repository
    cluster = await cluster_repo.get_by_name(cluster_name)

    if cluster is None:
        # 集群不存在时返回默认状态
        return ClusterHealthResponse(
            cluster_id=0,
            cluster_name=cluster_name,
            status="unknown",
            checked_at=utc_now(),
            storage_alert_count=0,
            network_alert_count=0,
        )

    try:
        result = await health_service.check_health(cluster.id)
        return ClusterHealthResponse(
            cluster_id=result.cluster_id,
            cluster_name=result.cluster_name,
            status=result.status.value,
            checked_at=result.checked_at,
            storage_alert_count=len(result.storage_alerts),
            network_alert_count=len(result.network_alerts),
        )
    except Exception:
        return ClusterHealthResponse(
            cluster_id=cluster.id,
            cluster_name=cluster_name,
            status="unknown",
            checked_at=utc_now(),
            storage_alert_count=0,
            network_alert_count=0,
        )
