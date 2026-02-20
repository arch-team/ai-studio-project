"""Prometheus 监控服务 (T062).

实现存储容量监控 (FR-020) 和网络性能监控 (FR-021)。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ...infrastructure.external.prometheus_client import IPrometheusClient


@dataclass
class MetricDataPoint:
    """指标数据点."""

    timestamp: datetime
    value: float


@dataclass
class StorageCapacityMetrics:
    """存储容量指标."""

    total_bytes: float
    used_bytes: float
    available_bytes: float
    usage_percent: float
    mountpoint: str


@dataclass
class StorageAlert:
    """存储告警."""

    severity: str  # warning, high, critical
    message: str
    mountpoint: str
    usage_percent: float


@dataclass
class NetworkMetrics:
    """网络指标."""

    latency_ms: float
    bandwidth_mbps: float
    packet_loss_percent: float
    interface: str


@dataclass
class NetworkAlert:
    """网络告警."""

    severity: str
    message: str
    metric_type: str  # latency, bandwidth, packet_loss
    value: float


@dataclass
class GPUUtilizationPoint:
    """GPU 利用率数据点."""

    gpu_id: str
    instance: str
    timestamp: datetime
    utilization_percent: float


# 告警阈值配置
STORAGE_THRESHOLDS = {
    "warning": 80.0,
    "high": 90.0,
    "critical": 95.0,
}

NETWORK_LATENCY_THRESHOLDS = {
    "warning": 50.0,  # ms
    "high": 100.0,
    "critical": 200.0,
}


class PrometheusService:
    """Prometheus 监控服务.

    提供存储容量监控、网络性能监控和 GPU 利用率查询功能。
    """

    def __init__(self, prometheus_client: IPrometheusClient):
        self._client = prometheus_client

    async def query_metrics(
        self,
        metric_names: list[str],
        start_time: datetime,
        end_time: datetime,
        step: str = "1m",
    ) -> dict[str, list[MetricDataPoint]]:
        """查询指标数据.

        Args:
            metric_names: 要查询的指标名称列表
            start_time: 开始时间
            end_time: 结束时间
            step: 时间步长

        Returns:
            指标名称到数据点列表的映射
        """
        result: dict[str, list[MetricDataPoint]] = {}

        for metric_name in metric_names:
            try:
                raw_result = await self._client.query_range(
                    query=metric_name,
                    start=start_time,
                    end=end_time,
                    step=step,
                )
                data_points = self._parse_range_result(raw_result)
                result[metric_name] = data_points
            except Exception as e:
                raise Exception(f"Prometheus query error for {metric_name}: {e}") from e

        return result

    async def get_storage_capacity_metrics(self) -> StorageCapacityMetrics:
        """获取存储容量指标 (FR-020)."""
        # 查询 FSx 存储使用率
        query = 'node_filesystem_avail_bytes{mountpoint="/fsx"}'
        avail_result = await self._client.query_instant(query)

        query_total = 'node_filesystem_size_bytes{mountpoint="/fsx"}'
        total_result = await self._client.query_instant(query_total)

        # 解析结果
        if avail_result and total_result:
            avail_bytes = float(avail_result[0].get("value", [0, "0"])[1])
            total_bytes = float(total_result[0].get("value", [0, "0"])[1])
            used_bytes = total_bytes - avail_bytes
            usage_percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
            mountpoint = avail_result[0].get("metric", {}).get("mountpoint", "/fsx")
        else:
            # 返回默认值或从 mock 数据中获取
            avail_bytes = 0.0
            total_bytes = 0.0
            used_bytes = 0.0
            usage_percent = 0.0
            mountpoint = "/fsx"

        return StorageCapacityMetrics(
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            available_bytes=avail_bytes,
            usage_percent=usage_percent,
            mountpoint=mountpoint,
        )

    async def check_storage_alerts(self) -> list[StorageAlert]:
        """检查存储告警 (FR-020).

        告警级别:
        - warning: 80% 使用率
        - high: 90% 使用率
        - critical: 95% 使用率
        """
        alerts: list[StorageAlert] = []

        # 查询存储使用率
        query = "100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)"
        result = await self._client.query_instant(query)

        for item in result:
            usage_percent = float(item.get("value", [0, "0"])[1])
            mountpoint = item.get("metric", {}).get("mountpoint", "unknown")

            severity = self._get_severity(usage_percent, STORAGE_THRESHOLDS)
            if severity:
                alerts.append(
                    StorageAlert(
                        severity=severity,
                        message=f"Storage usage at {usage_percent:.1f}% on {mountpoint}",
                        mountpoint=mountpoint,
                        usage_percent=usage_percent,
                    )
                )

        return alerts

    async def get_network_metrics(self) -> NetworkMetrics:
        """获取网络性能指标 (FR-021)."""
        latency_ms = await self._query_instant_value(
            "avg(node_network_receive_latency_seconds) * 1000"
        )
        bandwidth_mbps = await self._query_instant_value(
            "avg(rate(node_network_receive_bytes_total[5m])) / 1024 / 1024 * 8"
        )
        packet_loss_percent = await self._query_instant_value(
            "avg(node_network_receive_drop_total / node_network_receive_packets_total) * 100"
        )

        return NetworkMetrics(
            latency_ms=latency_ms,
            bandwidth_mbps=bandwidth_mbps,
            packet_loss_percent=packet_loss_percent,
            interface="eth0",
        )

    async def check_network_alerts(self) -> list[NetworkAlert]:
        """检查网络告警 (FR-021)."""
        alerts: list[NetworkAlert] = []

        # 检查延迟
        latency_query = "avg(node_network_receive_latency_seconds) * 1000"
        latency_result = await self._client.query_instant(latency_query)

        if latency_result:
            latency_ms = float(latency_result[0].get("value", [0, "0"])[1])
            severity = self._get_severity(latency_ms, NETWORK_LATENCY_THRESHOLDS)
            if severity:
                alerts.append(
                    NetworkAlert(
                        severity=severity,
                        message=f"Network latency at {latency_ms:.1f}ms",
                        metric_type="latency",
                        value=latency_ms,
                    )
                )

        return alerts

    async def get_gpu_utilization(
        self,
        cluster_name: str,
        start_time: datetime,
        end_time: datetime,
        step: str = "1m",
    ) -> list[GPUUtilizationPoint]:
        """获取 GPU 利用率数据.

        Args:
            cluster_name: 集群名称
            start_time: 开始时间
            end_time: 结束时间
            step: 时间步长

        Returns:
            GPU 利用率数据点列表
        """
        query = f'DCGM_FI_DEV_GPU_UTIL{{cluster="{cluster_name}"}}'
        result = await self._client.query_range(
            query=query,
            start=start_time,
            end=end_time,
            step=step,
        )

        data_points: list[GPUUtilizationPoint] = []
        for item in result:
            metric = item.get("metric", {})
            gpu_id = metric.get("gpu", "0")
            instance = metric.get("instance", "unknown")

            for value in item.get("values", []):
                timestamp = datetime.fromtimestamp(float(value[0]))
                utilization = float(value[1])
                data_points.append(
                    GPUUtilizationPoint(
                        gpu_id=gpu_id,
                        instance=instance,
                        timestamp=timestamp,
                        utilization_percent=utilization,
                    )
                )

        return data_points

    async def _query_instant_value(self, query: str, default: float = 0.0) -> float:
        """执行即时查询并提取第一个结果值."""
        result = await self._client.query_instant(query)
        if result:
            return float(result[0].get("value", [0, "0"])[1])
        return default

    def _parse_range_result(self, raw_result: list[dict[str, Any]]) -> list[MetricDataPoint]:
        """解析范围查询结果."""
        data_points: list[MetricDataPoint] = []

        for item in raw_result:
            for value in item.get("values", []):
                timestamp = datetime.fromtimestamp(float(value[0]))
                metric_value = float(value[1])
                data_points.append(MetricDataPoint(timestamp=timestamp, value=metric_value))

        return data_points

    @staticmethod
    def _get_severity(value: float, thresholds: dict[str, float]) -> str | None:
        """根据值和阈值配置获取告警级别."""
        if value >= thresholds["critical"]:
            return "critical"
        if value >= thresholds["high"]:
            return "high"
        if value >= thresholds["warning"]:
            return "warning"
        return None
