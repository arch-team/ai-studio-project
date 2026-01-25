"""训练模块应用层接口定义

包含:
- IHyperPodClient: SageMaker HyperPod 操作契约
- IMetricsService: 训练指标查询契约 (T037c)
- INotificationService: 告警通知契约 (T037c)
- IStorageService: 检查点存储操作契约 (T038)
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
    async def list_clusters(self, max_results: int = 100, next_token: str | None = None) -> dict[str, Any]:
        """List all HyperPod clusters."""

    @abstractmethod
    async def delete_cluster(self, cluster_name: str) -> dict[str, Any]:
        """Delete a HyperPod cluster."""

    @abstractmethod
    async def update_cluster(self, cluster_name: str, instance_groups: list[dict[str, Any]]) -> dict[str, Any]:
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
    async def get_training_job_status(self, cluster_name: str, job_name: str) -> dict[str, Any]:
        """Get training job status."""

    @abstractmethod
    async def stop_training_job(self, cluster_name: str, job_name: str) -> dict[str, Any]:
        """Stop a running training job."""

    @abstractmethod
    async def list_training_job_pods(self, cluster_name: str, job_name: str) -> list[dict[str, Any]]:
        """List pods for a training job."""

    # =========================================================================
    # E2E 测试支持方法 (抢占 SLA 测试)
    # =========================================================================

    @abstractmethod
    async def cancel_training_job(self, job_id: str) -> dict[str, Any]:
        """取消训练任务 (stop_training_job 的别名)"""

    @abstractmethod
    async def get_job_pods(self, job_id: str) -> list[dict[str, Any]]:
        """获取任务 Pod 列表 (list_training_job_pods 的别名)"""

    @abstractmethod
    async def get_pod_status(self, cluster_name: str, job_name: str, pod_name: str) -> dict[str, Any]:
        """获取单个 Pod 状态"""

    @abstractmethod
    async def verify_checkpoint_exists(self, s3_path: str) -> bool:
        """验证检查点文件是否存在"""

    @abstractmethod
    async def list_checkpoints(self, job_id: str, checkpoint_base_path: str) -> list[dict[str, Any]]:
        """列出任务检查点"""

    @abstractmethod
    async def resume_training_job(
        self,
        cluster_name: str,
        job_name: str,
        checkpoint_path: str | None = None,
        job_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """从检查点恢复任务"""

    @abstractmethod
    async def trigger_preemption(
        self,
        cluster_name: str,
        target_job_name: str,
        preemption_job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """通过提交高优先级任务触发抢占"""


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


# =============================================================================
# Storage Service Interface (T038)
# =============================================================================


@dataclass
class StorageInfo:
    """存储信息"""

    path: str
    size_bytes: int
    checksum: str


class IStorageService(ABC):
    """检查点存储服务接口 (T038)

    提供检查点的存储层操作能力，支持 NVMe、FSx、S3 三层存储。
    负责检查点文件的保存、迁移和完整性验证。
    """

    @abstractmethod
    async def check_nvme_available(self, job_id: int) -> bool:
        """检查 NVMe 存储是否可用

        Args:
            job_id: 训练任务 ID

        Returns:
            bool: NVMe 存储是否可用
        """

    @abstractmethod
    async def check_fsx_available(self, job_id: int) -> bool:
        """检查 FSx 存储是否可用

        Args:
            job_id: 训练任务 ID

        Returns:
            bool: FSx 存储是否可用
        """

    @abstractmethod
    async def get_storage_path(
        self,
        job_id: int,
        checkpoint_name: str,
        storage_tier: str,
    ) -> str:
        """生成检查点存储路径

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            storage_tier: 存储层级 (NVME, FSX, S3)

        Returns:
            str: 完整存储路径
        """

    @abstractmethod
    async def save_checkpoint(
        self,
        job_id: int,
        checkpoint_name: str,
        storage_tier: str,
    ) -> StorageInfo:
        """保存检查点到指定存储层

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            storage_tier: 目标存储层级

        Returns:
            StorageInfo: 包含路径、大小、校验和的存储信息
        """

    @abstractmethod
    async def calculate_checksum(self, storage_path: str) -> str:
        """计算检查点文件的 SHA-256 校验和

        Args:
            storage_path: 文件存储路径

        Returns:
            str: SHA-256 校验和
        """

    @abstractmethod
    async def get_checkpoint_size(self, storage_path: str) -> int:
        """获取检查点文件大小

        Args:
            storage_path: 文件存储路径

        Returns:
            int: 文件大小 (字节)
        """

    @abstractmethod
    async def migrate_checkpoint(
        self,
        source_path: str,
        target_tier: str,
        job_id: int,
    ) -> str:
        """迁移检查点到目标存储层

        Args:
            source_path: 源文件路径
            target_tier: 目标存储层级
            job_id: 训练任务 ID

        Returns:
            str: 新的存储路径
        """

    @abstractmethod
    async def verify_integrity(self, storage_path: str, expected_checksum: str) -> bool:
        """验证检查点文件完整性

        Args:
            storage_path: 文件存储路径
            expected_checksum: 预期的 SHA-256 校验和

        Returns:
            bool: 文件是否完整
        """

    @abstractmethod
    async def get_storage_usage(self, storage_tier: str) -> float:
        """获取存储层使用率

        Args:
            storage_tier: 存储层级

        Returns:
            float: 使用率 (0.0 - 1.0)
        """

    @abstractmethod
    async def delete_checkpoint(self, storage_path: str) -> None:
        """删除检查点文件

        Args:
            storage_path: 文件存储路径
        """
