"""SageMaker HyperPod 客户端接口。"""

from abc import ABC, abstractmethod
from typing import Any


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
