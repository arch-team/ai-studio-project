"""HyperPod 训练任务管理客户端。"""

import asyncio
from typing import Any

import structlog

from src.modules.training.domain.exceptions import HyperPodSDKUnavailableError

from .cluster_client import ClusterClient
from .config_builder import build_container, build_kueue_labels, build_replica_spec

logger = structlog.get_logger(__name__)

# 条件导入
try:
    from sagemaker.hyperpod.training import HyperPodPytorchJob
except ImportError:
    HyperPodPytorchJob = None

STATUS_MAPPING = {
    "Pending": "submitted",
    "Created": "submitted",
    "Scheduled": "submitted",
    "Running": "running",
    "Succeeded": "completed",
    "Completed": "completed",
    "Failed": "failed",
    "Error": "failed",
    "Suspended": "suspended",
    "Preempted": "preempted",
}

# 终态条件类型 - 一旦匹配则停止搜索
_TERMINAL_CONDITION_TYPES = {"Succeeded", "Completed", "Failed", "Error", "Suspended"}


def _map_status(hyperpod_status: str) -> str:
    """映射 HyperPod 状态到平台标准状态。"""
    return STATUS_MAPPING.get(hyperpod_status, "unknown")


def _get_initial_status(job: Any) -> str:
    """从刚创建的 HyperPodPytorchJob 获取初始状态字符串。"""
    job_status = getattr(job, "status", None)
    if job_status:
        return _map_status(getattr(job_status, "phase", "Pending"))
    return "unknown"


class JobClient:
    """HyperPod 训练任务管理客户端。"""

    def __init__(self, cluster_client: ClusterClient):
        self._cluster = cluster_client

    @staticmethod
    def _resolve_status_from_conditions(conditions: list | None) -> str:
        """从 HyperPod job conditions 列表解析当前状态。"""
        if not conditions:
            return "submitted"

        has_pods_running = False
        for cond in conditions:
            cond_type = getattr(cond, "type", "")
            cond_status = getattr(cond, "status", "")

            if cond_type == "PodsRunning":
                has_pods_running = True

            # 终态条件优先级最高
            if cond_status == "True" and cond_type in _TERMINAL_CONDITION_TYPES:
                return _map_status(cond_type)

        if has_pods_running:
            return "running"

        # 没有终态也没有 PodsRunning，取第一个 True 条件
        for cond in conditions:
            if getattr(cond, "status", "") == "True":
                return _map_status(getattr(cond, "type", ""))

        return "submitted"

    async def submit_training_job(
        self,
        cluster_name: str,
        job_name: str,
        job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """提交训练任务到集群。"""

        def _submit() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise HyperPodSDKUnavailableError()

            self._cluster.ensure_cluster_context(cluster_name)

            from sagemaker.hyperpod.common.config import Metadata
            from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import RunPolicy

            # 提取配置参数
            image_uri = job_config.get("image_uri")
            command = job_config.get("command") or job_config.get("entrypoint_command")
            env_dict = job_config.get("environment") or {}
            gpu_count = job_config.get("gpu_count", 1)
            node_count = job_config.get("node_count", 1)
            namespace = job_config.get("namespace", "default")
            queue_name = job_config.get("queue_name")
            priority_class = job_config.get("priority_class")

            # 使用 config_builder 构建配置
            container = build_container(image_uri, command, env_dict, gpu_count)
            replica_spec = build_replica_spec(container, node_count)
            labels = build_kueue_labels(queue_name, priority_class)

            # 构建 Metadata
            metadata_kwargs: dict[str, Any] = {"name": job_name, "namespace": namespace}
            if labels:
                metadata_kwargs["labels"] = labels

            # 创建 HyperPodPytorchJob
            nproc_per_node = str(job_config.get("tasks_per_node", 1))
            job = HyperPodPytorchJob(
                metadata=Metadata(**metadata_kwargs),
                nproc_per_node=nproc_per_node,
                replica_specs=[replica_spec],
                run_policy=RunPolicy(),
            )
            job.create()

            return {
                "job_name": job_name,
                "status": _get_initial_status(job),
                "cluster_name": cluster_name,
                "namespace": namespace,
            }

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _submit)

    async def get_training_job_status(
        self, cluster_name: str, job_name: str, namespace: str = "default"
    ) -> dict[str, Any]:
        """获取训练任务状态。"""

        def _get_status() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise HyperPodSDKUnavailableError()

            self._cluster.ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)

            try:
                job.refresh()
            except Exception as e:
                logger.debug("job_refresh_failed", job_name=job_name, error=str(e))

            # 从 conditions 获取当前状态
            status_str = "submitted"
            start_time = None
            end_time = None

            if job.status:
                start_time = getattr(job.status, "startTime", None)
                end_time = getattr(job.status, "completionTime", None)
                status_str = self._resolve_status_from_conditions(getattr(job.status, "conditions", None))

            return {
                "job_name": job.metadata.name if job.metadata else job_name,
                "status": status_str,
                "start_time": start_time,
                "end_time": end_time,
                "cluster_name": cluster_name,
            }

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_status)

    async def stop_training_job(self, cluster_name: str, job_name: str, namespace: str = "default") -> dict[str, Any]:
        """停止训练任务。"""

        def _stop() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise HyperPodSDKUnavailableError()

            self._cluster.ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
            job.delete()

            return {
                "job_name": job_name,
                "status": "stopped",
                "cluster_name": cluster_name,
                "namespace": namespace,
            }

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _stop)

    async def list_training_job_pods(
        self, cluster_name: str, job_name: str, namespace: str = "default"
    ) -> list[dict[str, Any]]:
        """列出训练任务的所有 Pod。"""

        def _list_pods() -> list[dict[str, Any]]:
            if HyperPodPytorchJob is None:
                raise HyperPodSDKUnavailableError()

            self._cluster.ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
            return job.list_pods()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _list_pods)

    async def cancel_training_job(self, job_id: str, namespace: str = "default") -> dict[str, Any]:
        """取消训练任务 (stop_training_job 的别名)。"""
        return await self.stop_training_job(cluster_name="", job_name=job_id, namespace=namespace)

    async def get_job_pods(self, job_id: str, namespace: str = "default") -> list[dict[str, Any]]:
        """获取任务 Pod 列表 (list_training_job_pods 的别名)。"""
        return await self.list_training_job_pods(cluster_name="", job_name=job_id, namespace=namespace)
