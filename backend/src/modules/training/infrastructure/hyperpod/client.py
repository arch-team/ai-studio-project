"""HyperPod Client - Facade 模式，委托各子客户端。"""

from typing import Any

import aioboto3

from src.modules.training.application.interfaces import IHyperPodClient

from .checkpoint_client import CheckpointClient
from .cluster_client import ClusterClient
from .job_client import JobClient


class HyperPodClient(IHyperPodClient):
    """HyperPod SDK 客户端 Facade。

    注意: HyperPod SDK 的训练任务操作 (submit/get_status/stop 等) 需要先设置
    集群上下文，通过 set_cluster_context() 配置 kubeconfig。
    """

    def __init__(
        self,
        region: str = "us-east-1",
        default_cluster_name: str | None = None,
    ) -> None:
        self._region = region
        self._default_cluster_name = default_cluster_name
        self._session = aioboto3.Session()

        # 初始化子客户端
        self._cluster = ClusterClient(self._session, region, default_cluster_name)
        self._jobs = JobClient(self._cluster)
        self._checkpoints = CheckpointClient(self._session, region, self._cluster)

    # =========================================================================
    # 兼容属性 - 保持测试中对内部属性的访问
    # =========================================================================

    @property
    def _cluster_contexts(self) -> set[str]:
        return ClusterClient._cluster_contexts

    def _ensure_cluster_context(self, cluster_name: str | None = None) -> None:
        """委托给 ClusterClient（保持测试兼容）。"""
        self._cluster.ensure_cluster_context(cluster_name)

    # =========================================================================
    # 集群管理 - 委托 ClusterClient
    # =========================================================================

    async def create_cluster(
        self, cluster_name: str, instance_groups: list[dict[str, Any]], vpc_config: dict[str, Any]
    ) -> dict[str, Any]:
        """创建新的 HyperPod 集群。"""
        return await self._cluster.create_cluster(cluster_name, instance_groups, vpc_config)

    async def describe_cluster(self, cluster_name: str) -> dict[str, Any]:
        """获取集群详细信息。"""
        return await self._cluster.describe_cluster(cluster_name)

    async def list_clusters(self, max_results: int = 100, next_token: str | None = None) -> dict[str, Any]:
        """列出所有 HyperPod 集群。"""
        return await self._cluster.list_clusters(max_results, next_token)

    async def delete_cluster(self, cluster_name: str) -> dict[str, Any]:
        """删除 HyperPod 集群。"""
        return await self._cluster.delete_cluster(cluster_name)

    async def update_cluster(self, cluster_name: str, instance_groups: list[dict[str, Any]]) -> dict[str, Any]:
        """更新集群实例组配置。"""
        return await self._cluster.update_cluster(cluster_name, instance_groups)

    # =========================================================================
    # 训练任务管理 - 委托 JobClient
    # =========================================================================

    async def submit_training_job(self, cluster_name: str, job_name: str, job_config: dict[str, Any]) -> dict[str, Any]:
        """提交训练任务到集群。"""
        return await self._jobs.submit_training_job(cluster_name, job_name, job_config)

    async def get_training_job_status(
        self, cluster_name: str, job_name: str, namespace: str = "default"
    ) -> dict[str, Any]:
        """获取训练任务状态。"""
        return await self._jobs.get_training_job_status(cluster_name, job_name, namespace)

    async def stop_training_job(self, cluster_name: str, job_name: str, namespace: str = "default") -> dict[str, Any]:
        """停止训练任务。"""
        return await self._jobs.stop_training_job(cluster_name, job_name, namespace)

    async def list_training_job_pods(
        self, cluster_name: str, job_name: str, namespace: str = "default"
    ) -> list[dict[str, Any]]:
        """列出训练任务的所有 Pod。"""
        return await self._jobs.list_training_job_pods(cluster_name, job_name, namespace)

    async def cancel_training_job(self, job_id: str, namespace: str = "default") -> dict[str, Any]:
        """取消训练任务 (stop_training_job 的别名)。"""
        return await self._jobs.cancel_training_job(job_id, namespace)

    async def get_job_pods(self, job_id: str, namespace: str = "default") -> list[dict[str, Any]]:
        """获取任务 Pod 列表 (list_training_job_pods 的别名)。"""
        return await self._jobs.get_job_pods(job_id, namespace)

    # =========================================================================
    # 检查点管理 - 委托 CheckpointClient
    # =========================================================================

    async def verify_checkpoint_exists(self, s3_path: str) -> bool:
        """验证 S3 检查点文件是否存在。"""
        return await self._checkpoints.verify_checkpoint_exists(s3_path)

    async def list_checkpoints(self, job_id: str, checkpoint_base_path: str) -> list[dict[str, Any]]:
        """列出任务的所有检查点。"""
        return await self._checkpoints.list_checkpoints(job_id, checkpoint_base_path)

    async def resume_training_job(
        self,
        cluster_name: str,
        job_name: str,
        checkpoint_path: str | None = None,
        job_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """从检查点恢复训练任务。"""
        return await self._checkpoints.resume_training_job(cluster_name, job_name, checkpoint_path, job_config)

    async def trigger_preemption(
        self,
        cluster_name: str,
        target_job_name: str,
        preemption_job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """通过提交高优先级任务触发抢占。"""
        return await self._checkpoints.trigger_preemption(cluster_name, target_job_name, preemption_job_config)

    async def get_pod_status(
        self,
        cluster_name: str,
        job_name: str,
        pod_name: str,
        namespace: str = "default",
    ) -> dict[str, Any]:
        """获取单个 Pod 状态。"""
        return await self._checkpoints.get_pod_status(cluster_name, job_name, pod_name, namespace)
