"""集群监控 API 端点 (Task 2C.4).

为前端监控页"集群概览"提供 **无 monitoring 前缀** 的 `/clusters*` 路由：
- GET /clusters            集群列表（读穿透：DB 为主，缺失/过期回源 SageMaker）
- GET /clusters/{id}       集群详情
- GET /clusters/{id}/nodes 集群节点列表
- GET /clusters/{id}/metrics 集群指标序列

故障降级：所有数据端点 try/except，依赖异常时记 warning + 返回空/默认结构，
返回 200 而非 5xx，保证前端优雅降级。集群不存在返回 404。
"""

from datetime import datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.modules.auth.api.dependencies import get_current_active_user
from src.shared.utils import utc_now

from ..application.services import PrometheusService
from ..application.services.cluster_sync_service import ClusterSyncService
from ..domain.entities import HyperPodCluster
from ..domain.repositories import IHyperPodClusterRepository
from .dependencies import (
    get_cluster_repository,
    get_cluster_sync_service,
    get_prometheus_service,
)
from .schemas import (
    ClusterDetailResponse,
    ClusterListResponse,
    ClusterSummaryResponse,
    InstanceGroupResponse,
    MetricDataPointResponse,
    MetricSeriesResponse,
    NodeListResponse,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


def _to_summary(cluster: HyperPodCluster) -> ClusterSummaryResponse:
    """将集群实体映射为摘要响应（enum 取 .value，health_status 可空）."""
    assert cluster.id is not None, "Cluster must have ID"
    return ClusterSummaryResponse(
        id=cluster.id,
        cluster_name=cluster.cluster_name,
        cluster_arn=cluster.cluster_arn,
        region=cluster.region,
        status=cluster.status.value,
        health_status=cluster.health_status.value if cluster.health_status else None,
        total_nodes=cluster.total_nodes,
        available_nodes=cluster.available_nodes,
        total_gpu_count=cluster.total_gpu_count,
        available_gpu_count=None,
        total_cpu_cores=cluster.total_cpu_cores,
        available_cpu_cores=None,
        last_sync_at=cluster.last_sync_at,
        created_at=cluster.created_at,
    )


def _to_instance_groups(cluster: HyperPodCluster) -> list[InstanceGroupResponse]:
    """将实体的 instance_groups（SageMaker 原生 dict）映射为响应模型.

    SageMaker InstanceGroups 字段为 PascalCase；CurrentCount 可能缺失或为 null
    （key 在但值为 None），用 `or 0` 同时兜底两种情况，避免 int(None) 抛 TypeError
    逃逸成 5xx，违反"数据端点不 5xx"契约。available_count 暂等于总数（CurrentCount），
    无节点级独立来源；待 2D.1 接入节点级数据（list_cluster_nodes）后修正为真实可用数。
    容量类型映射 OnDemand→on_demand / Spot→spot。
    """
    groups: list[InstanceGroupResponse] = []
    for g in cluster.instance_groups:
        current = int(g.get("CurrentCount") or 0)
        capacity_raw = str(g.get("CapacityType", "OnDemand"))
        capacity_type = "spot" if capacity_raw.lower().startswith("spot") else "on_demand"
        groups.append(
            InstanceGroupResponse(
                instance_group_name=str(g.get("InstanceGroupName", "")),
                instance_type=str(g.get("InstanceType", "")),
                instance_count=current,
                # available_count 暂等于总数 CurrentCount（语义近似），待 2D.1 修正。
                available_count=current,
                capacity_type=capacity_type,
                spot_interruption_behavior=None,
            )
        )
    return groups


def _to_detail(cluster: HyperPodCluster) -> ClusterDetailResponse:
    """将集群实体映射为详情响应."""
    assert cluster.id is not None, "Cluster must have ID"
    return ClusterDetailResponse(
        id=cluster.id,
        cluster_name=cluster.cluster_name,
        cluster_arn=cluster.cluster_arn,
        region=cluster.region,
        status=cluster.status.value,
        health_status=cluster.health_status.value if cluster.health_status else None,
        total_nodes=cluster.total_nodes,
        available_nodes=cluster.available_nodes,
        total_gpu_count=cluster.total_gpu_count,
        available_gpu_count=None,
        total_cpu_cores=cluster.total_cpu_cores,
        available_cpu_cores=None,
        last_sync_at=cluster.last_sync_at,
        created_at=cluster.created_at,
        vpc_id=cluster.vpc_id,
        instance_groups=_to_instance_groups(cluster),
        total_memory_gb=float(cluster.total_memory_gb) if cluster.total_memory_gb is not None else None,
        available_memory_gb=None,
        fsx_filesystem_id=cluster.fsx_filesystem_id,
        fsx_mount_point=cluster.fsx_mount_point,
        prometheus_endpoint=cluster.prometheus_endpoint,
        grafana_workspace_id=cluster.grafana_workspace_id,
        # 运行/排队任务数来自 training 模块，集群实体无此数据，默认 0。
        running_jobs_count=0,
        pending_jobs_count=0,
        updated_at=cluster.updated_at,
    )


@router.get("/clusters", response_model=ClusterListResponse)
async def list_clusters(
    _: None = Depends(get_current_active_user),
    sync_service: ClusterSyncService = Depends(get_cluster_sync_service),
) -> ClusterListResponse:
    """获取集群列表（读穿透）.

    回源失败时降级返回空列表，不 5xx。
    """
    try:
        clusters = await sync_service.get_clusters()
        items = [_to_summary(c) for c in clusters]
        return ClusterListResponse(items=items, total=len(items))
    except Exception as e:
        logger.warning("cluster_list_degraded", error=str(e))
        return ClusterListResponse(items=[], total=0)


@router.get("/clusters/{cluster_id}", response_model=ClusterDetailResponse)
async def get_cluster_detail(
    cluster_id: int,
    _: None = Depends(get_current_active_user),
    cluster_repo: IHyperPodClusterRepository = Depends(get_cluster_repository),
) -> ClusterDetailResponse:
    """获取集群详情.

    集群不存在返回 404；查询异常时同样按 404 处理（前端可优雅降级到列表页）。
    映射异常（如 instance_groups 含脏数据）同样按 404 降级，绝不逃逸成 5xx。
    """
    try:
        cluster = await cluster_repo.get_by_id(cluster_id)
    except Exception as e:
        logger.warning("cluster_detail_degraded", cluster_id=cluster_id, error=str(e))
        cluster = None

    if cluster is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster '{cluster_id}' not found",
        )

    # 双保险：_to_instance_groups 已加固不抛，此处再包一层；
    # 映射意外失败时按 docstring 承诺降级为 404，而非 500。
    try:
        return _to_detail(cluster)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("cluster_detail_mapping_failed", cluster_id=cluster_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster '{cluster_id}' not found",
        ) from e


@router.get("/clusters/{cluster_id}/nodes", response_model=NodeListResponse)
async def list_cluster_nodes(
    cluster_id: int,
    _: None = Depends(get_current_active_user),
    cluster_repo: IHyperPodClusterRepository = Depends(get_cluster_repository),
) -> NodeListResponse:
    """获取集群节点列表.

    集群不存在返回 404。节点级明细需 K8s/SageMaker list-cluster-nodes 能力，
    当前 SageMaker 只读客户端仅提供 describe-cluster，故返回结构正确的空列表。
    TODO(2D.1): 接入节点级数据源（list_cluster_nodes）后补充真实节点明细。
    """
    try:
        cluster = await cluster_repo.get_by_id(cluster_id)
    except Exception as e:
        logger.warning("cluster_nodes_degraded", cluster_id=cluster_id, error=str(e))
        cluster = None

    if cluster is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster '{cluster_id}' not found",
        )

    return NodeListResponse(items=[], total=0)


@router.get("/clusters/{cluster_id}/metrics", response_model=list[MetricSeriesResponse])
async def get_cluster_metric_series(
    cluster_id: int,
    metric_names: str | None = Query(None, description="逗号分隔的指标名称"),
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    step: str = Query("1m", description="时间步长"),
    _: None = Depends(get_current_active_user),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> list[MetricSeriesResponse]:
    """获取集群指标序列（前端 MetricSeries 列表）.

    AMP 故障时降级返回空 list，不 5xx。
    """
    if end_time is None:
        end_time = utc_now()
    if start_time is None:
        start_time = end_time - timedelta(hours=1)

    if metric_names:
        names = [n.strip() for n in metric_names.split(",") if n.strip()]
    else:
        names = ["DCGM_FI_DEV_GPU_UTIL", "node_cpu_usage", "node_memory_usage"]

    try:
        result = await prometheus_service.query_metrics(
            metric_names=names,
            start_time=start_time,
            end_time=end_time,
            step=step,
        )
        return [
            MetricSeriesResponse(
                metric_name=name,
                labels={},
                data_points=[MetricDataPointResponse(timestamp=dp.timestamp, value=dp.value) for dp in data_points],
            )
            for name, data_points in result.items()
        ]
    except Exception as e:
        logger.warning("cluster_metrics_degraded", cluster_id=cluster_id, error=str(e))
        return []
