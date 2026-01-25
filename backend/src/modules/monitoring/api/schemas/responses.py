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
    data_points: list[GPUUtilizationPointResponse] = Field(
        default_factory=list, description="GPU 利用率数据点列表"
    )


class GrafanaDashboardInfo(BaseModel):
    """Grafana 仪表盘信息."""

    id: str = Field(..., description="仪表盘 ID")
    name: str = Field(..., description="仪表盘名称")
    url: str = Field(..., description="仪表盘 URL")
    description: str | None = Field(None, description="仪表盘描述")


class GrafanaDashboardsResponse(BaseModel):
    """Grafana 仪表盘列表响应."""

    dashboards: list[GrafanaDashboardInfo] = Field(
        default_factory=list, description="仪表盘列表"
    )


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
