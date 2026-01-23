"""训练模块应用层接口定义

包含:
- IHyperPodClient: SageMaker HyperPod 操作契约
- IMetricsService: 训练指标查询契约 (T037c)
- INotificationService: 告警通知契约 (T037c)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


# =============================================================================
# HyperPod Client Interface
# =============================================================================


class IHyperPodClient(ABC):
    """Interface for SageMaker HyperPod operations."""

    @abstractmethod
    async def create_cluster(
        self,
        cluster_name: str,
        instance_groups: list[dict[str, Any]],
        vpc_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new HyperPod cluster."""

    @abstractmethod
    async def describe_cluster(self, cluster_name: str) -> dict[str, Any]:
        """Get cluster details."""

    @abstractmethod
    async def list_clusters(
        self, max_results: int = 100, next_token: str | None = None
    ) -> dict[str, Any]:
        """List all HyperPod clusters."""

    @abstractmethod
    async def delete_cluster(self, cluster_name: str) -> dict[str, Any]:
        """Delete a HyperPod cluster."""

    @abstractmethod
    async def update_cluster(
        self, cluster_name: str, instance_groups: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Update cluster instance groups."""

    @abstractmethod
    async def submit_training_job(
        self,
        cluster_name: str,
        job_name: str,
        job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit a training job to the cluster."""

    @abstractmethod
    async def get_training_job_status(
        self, cluster_name: str, job_name: str
    ) -> dict[str, Any]:
        """Get training job status."""

    @abstractmethod
    async def stop_training_job(
        self, cluster_name: str, job_name: str
    ) -> dict[str, Any]:
        """Stop a running training job."""

    @abstractmethod
    async def list_training_job_pods(
        self, cluster_name: str, job_name: str
    ) -> list[dict[str, Any]]:
        """List pods for a training job."""


# =============================================================================
# Metrics Service Interface (T037c)
# =============================================================================


@dataclass
class MetricPoint:
    """指标数据点"""

    timestamp: datetime
    value: float


class IMetricsService(ABC):
    """指标服务接口

    提供训练指标的查询能力，支持按时间范围获取指标历史。
    实现可以对接 CloudWatch、Prometheus 或自定义指标存储。
    """

    @abstractmethod
    async def get_metric_history(
        self,
        job_id: int,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MetricPoint]:
        """获取指定任务的指标历史数据

        Args:
            job_id: 训练任务 ID
            metric_name: 指标名称 (如 'loss', 'accuracy', 'perplexity')
            start_time: 查询起始时间
            end_time: 查询结束时间

        Returns:
            list[MetricPoint]: 指标数据点列表，按时间升序排列
        """
        pass


# =============================================================================
# Notification Service Interface (T037c)
# =============================================================================


@dataclass
class Alert:
    """告警消息"""

    title: str
    message: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    recipient_ids: list[int]  # 接收者用户 ID 列表
    metadata: dict[str, Any] | None = None


class INotificationService(ABC):
    """通知服务接口

    提供告警通知发送能力。
    实现可以对接邮件、Slack、钉钉等通知渠道。
    """

    @abstractmethod
    async def send_alert(self, alert: Alert) -> None:
        """发送告警通知

        Args:
            alert: 告警消息
        """
        pass
