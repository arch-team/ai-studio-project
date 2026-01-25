"""HyperPod 训练任务客户端 - 专注于任务管理操作"""

import logging
from typing import Any

from .base_client import HyperPodBaseClient

logger = logging.getLogger(__name__)


class HyperPodJobClient(HyperPodBaseClient):
    """HyperPod 训练任务管理客户端

    职责：
    - 提交训练任务
    - 查询任务状态
    - 停止/取消任务
    - 恢复任务执行
    """

    async def submit_training_job(
        self,
        cluster_name: str,
        job_name: str,
        job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """提交训练任务到集群

        Args:
            cluster_name: 集群名称
            job_name: 任务名称
            job_config: 任务配置，支持以下字段:
                - image_uri: Docker 镜像 URI
                - node_count: 节点数量
                - command: 运行命令
                - environment: 环境变量字典
                - namespace: Kubernetes namespace
                - queue_name: Kueue queue 名称
                - priority_class: WorkloadPriorityClass 名称
                - gpu_count: GPU 数量

        Returns:
            包含任务信息的字典
        """

        def _submit() -> dict[str, Any]:
            self._ensure_sdk_available()
            self._ensure_cluster_context(cluster_name)

            from sagemaker.hyperpod.common.config import Metadata
            from sagemaker.hyperpod.training import HyperPodPytorchJob
            from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
                Containers,
                ReplicaSpec,
                Resources,
                RunPolicy,
                Spec,
                Template,
            )
            from src.modules.training.domain.value_objects.constants import (
                DEFAULT_CONTAINER_NAME,
                DEFAULT_GPU_PER_NODE,
                DEFAULT_NAMESPACE,
                DEFAULT_NODE_COUNT,
                DEFAULT_TASKS_PER_NODE,
            )

            # 提取配置参数
            image_uri = job_config.get("image_uri")
            command = job_config.get("command") or job_config.get("entrypoint_command")
            env_dict = job_config.get("environment") or {}
            gpu_count = job_config.get("gpu_count", DEFAULT_GPU_PER_NODE)
            node_count = job_config.get("node_count", DEFAULT_NODE_COUNT)
            namespace = job_config.get("namespace", DEFAULT_NAMESPACE)
            queue_name = job_config.get("queue_name")
            priority_class = job_config.get("priority_class")

            # 构建环境变量
            env_list = self._build_env_list(env_dict)

            # 构建资源配置
            resources = Resources(
                limits={"nvidia.com/gpu": str(gpu_count)},
                requests={"nvidia.com/gpu": str(gpu_count)},
            )

            # 处理命令格式
            cmd = None
            if command:
                cmd = command if isinstance(command, list) else [command]

            # 构建容器配置
            container = Containers(
                name=DEFAULT_CONTAINER_NAME,
                image=image_uri,
                command=cmd,
                env=env_list,
                resources=resources,
            )

            # 构建 ReplicaSpec
            replica_spec = ReplicaSpec(
                name="worker",
                replicas=node_count,
                template=Template(spec=Spec(containers=[container])),
            )

            # 构建 Kueue 标签
            labels = self._build_kueue_labels(queue_name, priority_class)

            # 构建 Metadata
            metadata_kwargs: dict[str, Any] = {"name": job_name, "namespace": namespace}
            if labels:
                metadata_kwargs["labels"] = labels

            # 创建并提交任务
            nproc_per_node = str(job_config.get("tasks_per_node", DEFAULT_TASKS_PER_NODE))
            job = HyperPodPytorchJob(
                metadata=Metadata(**metadata_kwargs),
                nproc_per_node=nproc_per_node,
                replica_specs=[replica_spec],
                run_policy=RunPolicy(),
            )
            job.create()

            # 获取状态
            job_status = getattr(job, "status", None)
            status_str = "unknown"
            if job_status:
                status_str = self._map_status(getattr(job_status, "phase", "Pending"))

            return {
                "job_name": job_name,
                "status": status_str,
                "cluster_name": cluster_name,
                "namespace": namespace,
            }

        return await self._run_in_executor(_submit)

    async def get_training_job_status(
        self, cluster_name: str, job_name: str, namespace: str = "default"
    ) -> dict[str, Any]:
        """获取训练任务状态

        Args:
            cluster_name: 集群名称
            job_name: 任务名称
            namespace: Kubernetes namespace

        Returns:
            包含任务状态信息的字典
        """

        def _get_status() -> dict[str, Any]:
            self._ensure_sdk_available()
            self._ensure_cluster_context(cluster_name)

            from sagemaker.hyperpod.training import HyperPodPytorchJob

            job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)

            # 尝试刷新状态
            try:
                job.refresh()
            except Exception as e:
                logger.debug(f"Job refresh failed for {job_name}, using cached status: {e}")

            # 解析状态
            status_str = self._parse_job_status(job)
            start_time = None
            end_time = None

            if job.status:
                start_time = getattr(job.status, "startTime", None)
                end_time = getattr(job.status, "completionTime", None)

            return {
                "job_name": job.metadata.name if job.metadata else job_name,
                "status": status_str,
                "start_time": start_time,
                "end_time": end_time,
                "cluster_name": cluster_name,
            }

        return await self._run_in_executor(_get_status)

    def _parse_job_status(self, job: Any) -> str:
        """解析任务状态

        Args:
            job: HyperPodPytorchJob 实例

        Returns:
            标准化的任务状态字符串
        """
        status_str = "submitted"  # 默认状态

        if not job.status:
            return status_str

        conditions = getattr(job.status, "conditions", None)
        if not conditions:
            return status_str

        # 检查终止状态（优先级最高）
        for condition in conditions:
            cond_type = getattr(condition, "type", "")
            cond_status = getattr(condition, "status", "")

            if cond_status == "True" and cond_type in ("Succeeded", "Completed", "Failed", "Error", "Suspended"):
                return self._map_status(cond_type)

        # 检查 PodsRunning 条件
        for condition in conditions:
            if getattr(condition, "type", "") == "PodsRunning":
                return "running"

        # 使用第一个 True 状态
        for condition in conditions:
            if getattr(condition, "status", "") == "True":
                return self._map_status(getattr(condition, "type", ""))

        return status_str

    async def stop_training_job(self, cluster_name: str, job_name: str, namespace: str = "default") -> dict[str, Any]:
        """停止训练任务

        Args:
            cluster_name: 集群名称
            job_name: 任务名称
            namespace: Kubernetes namespace

        Returns:
            操作结果
        """

        def _stop() -> dict[str, Any]:
            self._ensure_sdk_available()
            self._ensure_cluster_context(cluster_name)

            from sagemaker.hyperpod.training import HyperPodPytorchJob

            job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
            job.delete()

            return {
                "job_name": job_name,
                "status": "stopped",
                "cluster_name": cluster_name,
                "namespace": namespace,
            }

        return await self._run_in_executor(_stop)

    async def list_training_job_pods(
        self, cluster_name: str, job_name: str, namespace: str = "default"
    ) -> list[dict[str, Any]]:
        """列出训练任务的所有 Pod

        Args:
            cluster_name: 集群名称
            job_name: 任务名称
            namespace: Kubernetes namespace

        Returns:
            Pod 信息列表
        """

        def _list_pods() -> list[dict[str, Any]]:
            self._ensure_sdk_available()
            self._ensure_cluster_context(cluster_name)

            from sagemaker.hyperpod.training import HyperPodPytorchJob

            job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
            return job.list_pods()

        return await self._run_in_executor(_list_pods)

    async def resume_training_job(
        self,
        cluster_name: str,
        job_name: str,
        checkpoint_path: str | None = None,
        job_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """从检查点恢复训练任务

        Args:
            cluster_name: 集群名称
            job_name: 新任务名称
            checkpoint_path: 检查点 S3 路径
            job_config: 任务配置

        Returns:
            恢复操作结果
        """
        if job_config is None:
            from src.modules.training.domain.exceptions import HyperPodOperationError

            raise HyperPodOperationError("resume", "job_config is required", job_name)

        # 添加检查点恢复环境变量
        enhanced_config = job_config.copy()
        if checkpoint_path:
            env = enhanced_config.get("environment", {})
            env["CHECKPOINT_PATH"] = checkpoint_path
            env["RESUME_FROM_CHECKPOINT"] = "true"
            enhanced_config["environment"] = env

        # 使用 submit 方法恢复任务
        return await self.submit_training_job(cluster_name, job_name, enhanced_config)