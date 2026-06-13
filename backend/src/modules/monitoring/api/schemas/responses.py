"""Monitoring API response schemas (T061)."""

from datetime import datetime

from pydantic import BaseModel, Field


class MetricDataPointResponse(BaseModel):
    """指标数据点响应."""

    timestamp: datetime = Field(..., description="时间戳")
    value: float = Field(..., description="指标值")


class MetricResponse(BaseModel):
    """单个指标响应."""

    metric_name: str = Field(..., description="指标名称")
    data_points: list[MetricDataPointResponse] = Field(default_factory=list, description="数据点列表")


class ClusterMetricsResponse(BaseModel):
    """集群指标响应."""

    cluster_name: str = Field(..., description="集群名称")
    metrics: list[MetricResponse] = Field(default_factory=list, description="指标列表")


class GPUUtilizationPointResponse(BaseModel):
    """GPU 利用率数据点响应."""

    gpu_id: str = Field(..., description="GPU ID")
    instance: str = Field(..., description="实例名称")
    timestamp: datetime = Field(..., description="时间戳")
    utilization_percent: float = Field(..., description="利用率百分比")


class GPUUtilizationResponse(BaseModel):
    """GPU 利用率响应."""

    job_id: int = Field(..., description="任务 ID")
    data_points: list[GPUUtilizationPointResponse] = Field(default_factory=list, description="GPU 利用率数据点列表")


class GrafanaDashboardInfo(BaseModel):
    """Grafana 仪表盘信息."""

    id: str = Field(..., description="仪表盘 ID")
    name: str = Field(..., description="仪表盘名称")
    url: str = Field(..., description="仪表盘 URL")
    description: str | None = Field(None, description="仪表盘描述")


class GrafanaDashboardsResponse(BaseModel):
    """Grafana 仪表盘列表响应."""

    dashboards: list[GrafanaDashboardInfo] = Field(default_factory=list, description="仪表盘列表")


class StorageMetricsResponse(BaseModel):
    """存储指标响应."""

    total_bytes: float = Field(..., description="总容量（字节）")
    used_bytes: float = Field(..., description="已用容量（字节）")
    available_bytes: float = Field(..., description="可用容量（字节）")
    usage_percent: float = Field(..., description="使用率百分比")
    mountpoint: str = Field(..., description="挂载点")


class NetworkMetricsResponse(BaseModel):
    """网络指标响应."""

    latency_ms: float = Field(..., description="延迟（毫秒）")
    bandwidth_mbps: float = Field(..., description="带宽（Mbps）")
    packet_loss_percent: float = Field(..., description="丢包率百分比")
    interface: str = Field(..., description="网络接口")


class ClusterHealthResponse(BaseModel):
    """集群健康状态响应."""

    cluster_id: int = Field(..., description="集群 ID")
    cluster_name: str = Field(..., description="集群名称")
    status: str = Field(..., description="健康状态")
    checked_at: datetime = Field(..., description="检查时间")
    storage_alert_count: int = Field(0, description="存储告警数量")
    network_alert_count: int = Field(0, description="网络告警数量")


# === 监控页响应 Schema（对齐前端 frontend/src/features/monitoring/types/index.ts） ===


class ClusterSummaryResponse(BaseModel):
    """集群摘要响应（前端 ClusterSummary）."""

    id: int = Field(..., description="集群 ID")
    cluster_name: str = Field(..., description="集群名称")
    cluster_arn: str = Field(..., description="集群 ARN")
    region: str = Field(..., description="AWS 区域")
    status: str = Field(..., description="集群状态: creating/active/updating/deleting/failed")
    health_status: str | None = Field(None, description="健康状态: healthy/degraded/unhealthy")
    total_nodes: int = Field(..., description="节点总数")
    available_nodes: int = Field(..., description="可用节点数")
    total_gpu_count: int | None = Field(None, description="GPU 总数")
    available_gpu_count: int | None = Field(None, description="可用 GPU 数")
    total_cpu_cores: int | None = Field(None, description="CPU 核心总数")
    available_cpu_cores: int | None = Field(None, description="可用 CPU 核心数")
    last_sync_at: datetime | None = Field(None, description="最近同步时间")
    created_at: datetime = Field(..., description="创建时间")


class ClusterListResponse(BaseModel):
    """集群列表响应（前端 ClusterListResponse）."""

    items: list[ClusterSummaryResponse] = Field(default_factory=list, description="集群列表")
    total: int = Field(0, description="集群总数")


class InstanceGroupResponse(BaseModel):
    """实例组响应（前端 InstanceGroup，ClusterDetail.instance_groups 元素）."""

    instance_group_name: str = Field(..., description="实例组名称")
    instance_type: str = Field(..., description="实例类型")
    instance_count: int = Field(..., description="实例数量")
    available_count: int = Field(..., description="可用实例数")
    capacity_type: str = Field(..., description="容量类型: on_demand/spot")
    spot_interruption_behavior: str | None = Field(None, description="Spot 中断行为: stop/terminate/hibernate")


class ClusterDetailResponse(ClusterSummaryResponse):
    """集群详情响应（前端 ClusterDetail，继承 ClusterSummary）."""

    vpc_id: str = Field(..., description="VPC ID")
    instance_groups: list[InstanceGroupResponse] = Field(default_factory=list, description="实例组列表")
    total_memory_gb: float | None = Field(None, description="内存总量（GB）")
    available_memory_gb: float | None = Field(None, description="可用内存（GB）")
    fsx_filesystem_id: str | None = Field(None, description="FSx 文件系统 ID")
    fsx_mount_point: str | None = Field(None, description="FSx 挂载点")
    prometheus_endpoint: str | None = Field(None, description="Prometheus 端点")
    grafana_workspace_id: str | None = Field(None, description="Grafana 工作区 ID")
    running_jobs_count: int = Field(..., description="运行中任务数")
    pending_jobs_count: int = Field(..., description="排队中任务数")
    updated_at: datetime = Field(..., description="更新时间")


class NodeSummaryResponse(BaseModel):
    """节点摘要响应（前端 NodeSummary）."""

    node_name: str = Field(..., description="节点名称")
    instance_type: str = Field(..., description="实例类型")
    instance_group: str = Field(..., description="所属实例组")
    status: str = Field(..., description="节点状态: ready/not_ready/unknown")
    cpu_capacity: float = Field(..., description="CPU 容量")
    cpu_used: float = Field(..., description="CPU 已用")
    memory_capacity_gb: float = Field(..., description="内存容量（GB）")
    memory_used_gb: float = Field(..., description="内存已用（GB）")
    gpu_capacity: int = Field(..., description="GPU 容量")
    gpu_used: int = Field(..., description="GPU 已用")
    pod_count: int = Field(..., description="Pod 数量")
    age: str = Field(..., description="节点存活时长")


class NodeListResponse(BaseModel):
    """节点列表响应（前端 NodeListResponse）."""

    items: list[NodeSummaryResponse] = Field(default_factory=list, description="节点列表")
    total: int = Field(0, description="节点总数")


class ResourceUtilizationResponse(BaseModel):
    """资源利用率响应（前端 ResourceUtilization）."""

    resource_type: str = Field(..., description="资源类型: cpu/memory/gpu/storage")
    total: float = Field(..., description="资源总量")
    used: float = Field(..., description="已用量")
    available: float = Field(..., description="可用量")
    utilization_percentage: float = Field(..., description="利用率百分比")
    unit: str = Field(..., description="计量单位")


class MetricSeriesResponse(BaseModel):
    """指标序列响应（前端 MetricSeries），复用 MetricDataPointResponse."""

    metric_name: str = Field(..., description="指标名称")
    labels: dict[str, str] = Field(default_factory=dict, description="指标标签")
    data_points: list[MetricDataPointResponse] = Field(default_factory=list, description="数据点列表")


class AlertResponse(BaseModel):
    """告警响应（前端 Alert）."""

    id: str = Field(..., description="告警 ID")
    severity: str = Field(..., description="严重级别: critical/warning/info")
    title: str = Field(..., description="告警标题")
    message: str = Field(..., description="告警内容")
    source: str = Field(..., description="告警来源")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源 ID")
    fired_at: datetime = Field(..., description="触发时间")
    resolved_at: datetime | None = Field(None, description="解决时间")
    status: str = Field(..., description="告警状态: firing/resolved/acknowledged")


class AlertListResponse(BaseModel):
    """告警分页列表响应（前端 AlertListResponse）."""

    items: list[AlertResponse] = Field(default_factory=list, description="告警列表")
    total: int = Field(0, description="告警总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
