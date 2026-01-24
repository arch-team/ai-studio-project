"""HyperPod Client - SageMaker HyperPod SDK integration."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

import boto3

from src.modules.training.application.interfaces import IHyperPodClient

logger = logging.getLogger(__name__)

# Conditional imports for testing environments
try:
    from sagemaker.hyperpod.training import HyperPodPytorchJob
except ImportError:
    HyperPodPytorchJob = None  # type: ignore

# set_cluster_context 用于配置 kubeconfig 连接 HyperPod 集群
try:
    from sagemaker.hyperpod import set_cluster_context
except ImportError:
    set_cluster_context = None  # type: ignore


STATUS_MAPPING = {
    # HyperPod/Kubernetes job condition types
    "Pending": "submitted",
    "Created": "submitted",
    "Scheduled": "submitted",
    "Running": "running",
    "Succeeded": "completed",
    "Completed": "completed",
    "Failed": "failed",
    "Error": "failed",
    "Suspended": "paused",
}


def _map_status(hyperpod_status: str) -> str:
    """Map HyperPod status to platform standard status."""
    return STATUS_MAPPING.get(hyperpod_status, "unknown")


T = TypeVar("T")


class HyperPodClient(IHyperPodClient):
    """HyperPod SDK client implementation.

    注意: HyperPod SDK 的训练任务操作 (submit/get_status/stop 等) 需要先设置
    集群上下文，通过 set_cluster_context() 配置 kubeconfig。否则 SDK 无法与
    Kubernetes API 交互，导致 job.status 始终为 None。
    """

    # 已设置上下文的集群缓存 (避免重复设置)
    _cluster_contexts: set[str] = set()

    def __init__(
        self,
        region: str = "us-east-1",
        default_cluster_name: str | None = None,
    ) -> None:
        """Initialize HyperPod client.

        Args:
            region: AWS 区域
            default_cluster_name: 默认集群名称 (可选，用于自动设置上下文)
        """
        self._region = region
        self._default_cluster_name = default_cluster_name
        self._sagemaker_client = boto3.client("sagemaker", region_name=region)

    def _ensure_cluster_context(self, cluster_name: str | None = None) -> None:
        """确保集群上下文已设置 (同步方法，在 executor 中调用)。

        HyperPod SDK 需要先调用 set_cluster_context() 配置 kubeconfig，
        才能正确执行 HyperPodPytorchJob 的操作 (create/get/refresh 等)。

        Args:
            cluster_name: 集群名称，如果为 None 则使用默认集群
        """
        target_cluster = cluster_name or self._default_cluster_name

        if not target_cluster:
            logger.warning("No cluster name provided for context setup")
            return

        # 检查是否已设置此集群的上下文
        if target_cluster in self._cluster_contexts:
            return

        if set_cluster_context is None:
            logger.warning(
                "set_cluster_context not available, SDK status operations may fail"
            )
            return

        try:
            logger.info(f"Setting cluster context for: {target_cluster}")
            set_cluster_context(target_cluster)
            self._cluster_contexts.add(target_cluster)
            logger.info(f"Cluster context set successfully: {target_cluster}")
        except Exception as e:
            logger.error(f"Failed to set cluster context: {e}")
            # 不抛出异常，让操作继续尝试 (可能已经配置了 kubeconfig)

    async def _run_in_executor(self, func: Callable[[], T]) -> T:
        """Run a blocking function in executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func)

    async def create_cluster(
        self,
        cluster_name: str,
        instance_groups: list[dict[str, Any]],
        vpc_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new HyperPod cluster."""
        return await self._run_in_executor(
            lambda: self._sagemaker_client.create_cluster(
                ClusterName=cluster_name,
                InstanceGroups=instance_groups,
                VpcConfig=vpc_config,
            )
        )

    async def describe_cluster(self, cluster_name: str) -> dict[str, Any]:
        """Get cluster details using boto3 SageMaker API."""
        return await self._run_in_executor(
            lambda: self._sagemaker_client.describe_cluster(ClusterName=cluster_name)
        )

    async def list_clusters(
        self, max_results: int = 100, next_token: str | None = None
    ) -> dict[str, Any]:
        """List all HyperPod clusters."""
        params: dict[str, Any] = {"MaxResults": max_results}
        if next_token:
            params["NextToken"] = next_token

        return await self._run_in_executor(
            lambda: self._sagemaker_client.list_clusters(**params)
        )

    async def delete_cluster(self, cluster_name: str) -> dict[str, Any]:
        """Delete a HyperPod cluster."""
        return await self._run_in_executor(
            lambda: self._sagemaker_client.delete_cluster(ClusterName=cluster_name)
        )

    async def update_cluster(
        self, cluster_name: str, instance_groups: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Update cluster instance groups."""
        return await self._run_in_executor(
            lambda: self._sagemaker_client.update_cluster(
                ClusterName=cluster_name,
                InstanceGroups=instance_groups,
            )
        )

    async def submit_training_job(
        self,
        cluster_name: str,
        job_name: str,
        job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit a training job to the cluster using HyperPod SDK.

        Args:
            cluster_name: 集群名称
            job_name: 任务名称
            job_config: 任务配置，支持以下字段:
                - image_uri: Docker 镜像 URI
                - instance_type: 实例类型 (未使用，由集群决定)
                - node_count: 节点数量 (replicas)
                - tasks_per_node: 每节点任务数 (nproc_per_node)
                - command: 运行命令
                - environment: 环境变量字典
                - entrypoint_command: 入口命令
        """

        def _submit() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            # 确保集群上下文已设置
            self._ensure_cluster_context(cluster_name)

            # 导入必要的配置类
            from sagemaker.hyperpod.common.config import Metadata
            from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
                Containers,
                ReplicaSpec,
                RunPolicy,
                Spec,
                Template,
            )

            # 构建容器配置
            image_uri = job_config.get("image_uri")
            command = job_config.get("command") or job_config.get("entrypoint_command")
            env_dict = job_config.get("environment") or {}

            # 构建环境变量列表
            env_list = None
            if env_dict:
                from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
                    Env,
                )

                env_list = [Env(name=k, value=str(v)) for k, v in env_dict.items()]

            # 构建容器 (SDK 限制: 只能使用部分字段)
            container = Containers(
                name="pytorch",
                image=image_uri,
                command=command if isinstance(command, list) else [command] if command else None,
                env=env_list,
            )

            # 构建 ReplicaSpec
            # 注意: name 必须小写，符合 Kubernetes RFC 1123 命名规范
            node_count = job_config.get("node_count", 1)
            replica_spec = ReplicaSpec(
                name="worker",
                replicas=node_count,
                template=Template(
                    spec=Spec(containers=[container])
                ),
            )

            # 构建运行策略 (SDK 使用默认值)
            run_policy = RunPolicy()

            # 创建 HyperPodPytorchJob
            nproc_per_node = str(job_config.get("tasks_per_node", 1))
            job = HyperPodPytorchJob(
                metadata=Metadata(name=job_name),
                nproc_per_node=nproc_per_node,
                replica_specs=[replica_spec],
                run_policy=run_policy,
            )

            # 提交任务
            job.create()

            # 获取状态
            job_status = getattr(job, "status", None)
            status_str = "unknown"
            if job_status:
                status_str = _map_status(getattr(job_status, "phase", "Pending"))

            return {
                "job_name": job_name,
                "status": status_str,
                "cluster_name": cluster_name,
            }

        return await self._run_in_executor(_submit)

    async def get_training_job_status(
        self, cluster_name: str, job_name: str
    ) -> dict[str, Any]:
        """Get training job status using HyperPod SDK."""

        def _get_status() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            # 确保集群上下文已设置 (状态查询关键依赖)
            self._ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name)

            # 尝试刷新状态 (SDK 需要显式刷新)
            try:
                job.refresh()
            except Exception:
                # refresh 可能失败，继续使用当前状态
                pass

            # 从 conditions 获取当前状态
            status_str = "submitted"  # 默认状态: 已提交
            start_time = None
            end_time = None

            if job.status:
                start_time = getattr(job.status, "startTime", None)
                end_time = getattr(job.status, "completionTime", None)

                # 从 conditions 提取状态
                conditions = getattr(job.status, "conditions", None)
                if conditions:
                    for condition in conditions:
                        cond_type = getattr(condition, "type", "")
                        cond_status = getattr(condition, "status", "")
                        if cond_status == "True":
                            status_str = _map_status(cond_type)
                            break

            return {
                "job_name": job.metadata.name if job.metadata else job_name,
                "status": status_str,
                "start_time": start_time,
                "end_time": end_time,
                "cluster_name": cluster_name,
            }

        return await self._run_in_executor(_get_status)

    async def stop_training_job(
        self, cluster_name: str, job_name: str
    ) -> dict[str, Any]:
        """Stop a running training job using HyperPod SDK."""

        def _stop() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            # 确保集群上下文已设置
            self._ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name)
            job.delete()

            return {
                "job_name": job_name,
                "status": "stopped",
                "cluster_name": cluster_name,
            }

        return await self._run_in_executor(_stop)

    async def list_training_job_pods(
        self, cluster_name: str, job_name: str
    ) -> list[dict[str, Any]]:
        """List pods for a training job using HyperPod SDK."""

        def _list_pods() -> list[dict[str, Any]]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            # 确保集群上下文已设置
            self._ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name)
            return job.list_pods()

        return await self._run_in_executor(_list_pods)

    # ==========================================================================
    # E2E 测试支持方法 (抢占 SLA 测试)
    # ==========================================================================

    async def cancel_training_job(self, job_id: str) -> dict[str, Any]:
        """取消训练任务 (stop_training_job 的别名)"""
        return await self.stop_training_job(cluster_name="", job_name=job_id)

    async def get_job_pods(self, job_id: str) -> list[dict[str, Any]]:
        """获取任务 Pod 列表 (list_training_job_pods 的别名)"""
        return await self.list_training_job_pods(cluster_name="", job_name=job_id)

    async def get_pod_status(
        self, cluster_name: str, job_name: str, pod_name: str
    ) -> dict[str, Any]:
        """获取单个 Pod 状态"""

        def _get_status() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            # 确保集群上下文已设置
            self._ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name)
            pods = job.list_pods()

            for pod in pods:
                if pod.get("name") == pod_name:
                    return {
                        "name": pod_name,
                        "phase": pod.get("phase", "Unknown"),
                        "status": pod.get("status", {}),
                    }

            raise ValueError(f"Pod {pod_name} not found")

        return await self._run_in_executor(_get_status)

    async def verify_checkpoint_exists(self, s3_path: str) -> bool:
        """验证 S3 检查点文件是否存在

        Args:
            s3_path: S3 路径, 格式 s3://bucket/key
        """
        import re

        from botocore.exceptions import ClientError

        def _check_exists() -> bool:
            match = re.match(r"s3://([^/]+)/(.+)", s3_path)
            if not match:
                raise ValueError(f"Invalid S3 path: {s3_path}")

            bucket, key = match.groups()
            s3_client = boto3.client("s3", region_name=self._region)

            try:
                s3_client.head_object(Bucket=bucket, Key=key)
                return True
            except ClientError:
                return False

        return await self._run_in_executor(_check_exists)

    async def list_checkpoints(
        self, job_id: str, checkpoint_base_path: str
    ) -> list[dict[str, Any]]:
        """列出任务的所有检查点

        Args:
            job_id: 训练任务 ID
            checkpoint_base_path: 检查点 S3 基础路径 (s3://bucket/prefix)
        """
        import re

        def _list() -> list[dict[str, Any]]:
            match = re.match(r"s3://([^/]+)/(.+)", checkpoint_base_path)
            if not match:
                return []

            bucket, prefix = match.groups()
            s3_client = boto3.client("s3", region_name=self._region)

            # 构造检查点目录前缀
            checkpoint_prefix = f"{prefix.rstrip('/')}/{job_id}/"

            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=checkpoint_prefix,
            )

            checkpoints = []
            for obj in response.get("Contents", []):
                checkpoints.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "etag": obj["ETag"],
                })

            return checkpoints

        return await self._run_in_executor(_list)

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
            job_config: 任务配置 (复用原任务配置)
        """

        def _resume() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            if job_config is None:
                raise ValueError("job_config is required for resume")

            # 确保集群上下文已设置
            self._ensure_cluster_context(cluster_name)

            # 导入必要的配置类
            from sagemaker.hyperpod.common.config import Metadata
            from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
                Containers,
                Env,
                ReplicaSpec,
                RunPolicy,
                Spec,
                Template,
            )

            # 添加检查点恢复环境变量
            env_dict = (job_config.get("environment") or {}).copy()
            if checkpoint_path:
                env_dict["CHECKPOINT_PATH"] = checkpoint_path
                env_dict["RESUME_FROM_CHECKPOINT"] = "true"

            # 构建环境变量列表
            env_list = None
            if env_dict:
                env_list = [Env(name=k, value=str(v)) for k, v in env_dict.items()]

            # 构建容器配置
            command = job_config.get("command")
            container = Containers(
                name="pytorch",
                image=job_config.get("image_uri"),
                command=command if isinstance(command, list) else [command] if command else None,
                env=env_list,
            )

            # 构建 ReplicaSpec
            node_count = job_config.get("node_count", 1)
            replica_spec = ReplicaSpec(
                name="Worker",
                replicas=node_count,
                template=Template(spec=Spec(containers=[container])),
            )

            # 创建 HyperPodPytorchJob
            nproc_per_node = str(job_config.get("tasks_per_node", 1))
            job = HyperPodPytorchJob(
                metadata=Metadata(name=job_name),
                nproc_per_node=nproc_per_node,
                replica_specs=[replica_spec],
                run_policy=RunPolicy(),
            )
            job.create()

            # 获取状态
            job_status = getattr(job, "status", None)
            status_str = "unknown"
            if job_status:
                status_str = _map_status(getattr(job_status, "phase", "Pending"))

            return {
                "job_name": job_name,
                "status": status_str,
                "cluster_name": cluster_name,
                "checkpoint_path": checkpoint_path,
                "resumed": True,
            }

        return await self._run_in_executor(_resume)

    async def trigger_preemption(
        self,
        cluster_name: str,
        target_job_name: str,
        preemption_job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """通过提交高优先级任务触发抢占

        工作原理:
        1. 获取目标任务的资源占用信息
        2. 提交一个 critical 优先级的任务抢占资源
        3. Kueue 自动触发低优先级任务的 preemption
        4. 返回高优先级任务信息和抢占状态

        Args:
            cluster_name: 集群名称
            target_job_name: 要被抢占的低优先级任务名称
            preemption_job_config: 高优先级任务配置 (必须包含 priority="critical")
        """
        import time

        def _trigger() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            # 确保集群上下文已设置
            self._ensure_cluster_context(cluster_name)

            # 导入必要的配置类
            from sagemaker.hyperpod.common.config import Metadata
            from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
                Containers,
                Env,
                ReplicaSpec,
                RunPolicy,
                Spec,
                Template,
            )

            # 验证目标任务存在
            target_job = HyperPodPytorchJob.get(name=target_job_name)
            if target_job.status != "Running":
                raise ValueError(f"Target job {target_job_name} is not running")

            # 生成高优先级任务名称
            preemption_job_name = f"preempt-{target_job_name}-{int(time.time())}"

            # 确保高优先级配置
            env_dict = (preemption_job_config.get("environment") or {}).copy()
            env_dict["KUEUE_PRIORITY_CLASS"] = "critical"
            env_list = [Env(name=k, value=str(v)) for k, v in env_dict.items()]

            # 构建容器配置
            command = preemption_job_config.get("command")
            container = Containers(
                name="pytorch",
                image=preemption_job_config.get("image_uri"),
                command=command if isinstance(command, list) else [command] if command else None,
                env=env_list,
            )

            # 构建 ReplicaSpec
            node_count = preemption_job_config.get("node_count", 1)
            replica_spec = ReplicaSpec(
                name="Worker",
                replicas=node_count,
                template=Template(spec=Spec(containers=[container])),
            )

            # 创建并提交高优先级任务
            preemption_job = HyperPodPytorchJob(
                metadata=Metadata(name=preemption_job_name),
                nproc_per_node="1",
                replica_specs=[replica_spec],
                run_policy=RunPolicy(),
            )
            preemption_job.create()

            # 获取状态
            job_status = getattr(preemption_job, "status", None)
            status_str = "unknown"
            if job_status:
                status_str = _map_status(getattr(job_status, "phase", "Pending"))

            return {
                "target_job_name": target_job_name,
                "preemption_job_name": preemption_job_name,
                "preemption_job_status": status_str,
                "mechanism": "high_priority_task",
            }

        return await self._run_in_executor(_trigger)
