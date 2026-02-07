"""HyperPod 检查点管理客户端。"""

import asyncio
import re
import time
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from src.modules.training.domain.exceptions import (
    HyperPodOperationError,
    HyperPodPodNotFoundError,
    HyperPodSDKUnavailableError,
)

from .cluster_client import ClusterClient
from .config_builder import build_container, build_replica_spec
from .job_client import _get_initial_status

# 条件导入
try:
    from sagemaker.hyperpod.training import HyperPodPytorchJob
except ImportError:
    HyperPodPytorchJob = None

# S3 路径正则（匹配 s3://bucket/key）
_S3_PATH_RE = re.compile(r"s3://([^/]+)/(.+)")


class CheckpointClient:
    """HyperPod 检查点管理客户端。"""

    def __init__(self, session: aioboto3.Session, region: str, cluster_client: ClusterClient):
        self._session = session
        self._region = region
        self._cluster = cluster_client

    async def verify_checkpoint_exists(self, s3_path: str) -> bool:
        """验证 S3 检查点文件是否存在。"""
        match = _S3_PATH_RE.match(s3_path)
        if not match:
            raise HyperPodOperationError("verify_checkpoint", f"Invalid S3 path format: {s3_path}")

        bucket, key = match.groups()
        async with self._session.client("s3", region_name=self._region) as s3:
            try:
                await s3.head_object(Bucket=bucket, Key=key)
                return True
            except ClientError:
                return False

    async def list_checkpoints(self, job_id: str, checkpoint_base_path: str) -> list[dict[str, Any]]:
        """列出任务的所有检查点。"""
        match = _S3_PATH_RE.match(checkpoint_base_path)
        if not match:
            return []

        bucket, prefix = match.groups()
        checkpoint_prefix = f"{prefix.rstrip('/')}/{job_id}/"

        async with self._session.client("s3", region_name=self._region) as s3:
            response = await s3.list_objects_v2(Bucket=bucket, Prefix=checkpoint_prefix)

        return [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
                "etag": obj["ETag"],
            }
            for obj in response.get("Contents", [])
        ]

    async def resume_training_job(
        self,
        cluster_name: str,
        job_name: str,
        checkpoint_path: str | None = None,
        job_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """从检查点恢复训练任务。"""

        def _resume() -> dict[str, Any]:
            self._validate_resume_prerequisites(job_config, job_name)
            self._cluster.ensure_cluster_context(cluster_name)

            # 准备恢复配置
            env_dict = self._prepare_resume_environment(job_config, checkpoint_path)
            job = self._create_resume_job(job_name, job_config, env_dict)
            job.create()

            return {
                "job_name": job_name,
                "status": _get_initial_status(job),
                "cluster_name": cluster_name,
                "checkpoint_path": checkpoint_path,
                "resumed": True,
            }

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _resume)

    def _validate_resume_prerequisites(self, job_config: dict[str, Any] | None, job_name: str) -> None:
        """验证恢复前置条件."""
        if HyperPodPytorchJob is None:
            raise HyperPodSDKUnavailableError()
        if job_config is None:
            raise HyperPodOperationError("resume", "job_config is required", job_name)

    def _prepare_resume_environment(self, job_config: dict[str, Any], checkpoint_path: str | None) -> dict:
        """准备恢复环境变量."""
        env_dict = (job_config.get("environment") or {}).copy()
        if checkpoint_path:
            env_dict["CHECKPOINT_PATH"] = checkpoint_path
            env_dict["RESUME_FROM_CHECKPOINT"] = "true"
        return env_dict

    def _create_resume_job(self, job_name: str, job_config: dict[str, Any], env_dict: dict):
        """创建恢复任务."""
        from sagemaker.hyperpod.common.config import Metadata
        from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import RunPolicy

        # 构建配置
        container = build_container(
            job_config.get("image_uri"),
            job_config.get("command"),
            env_dict,
            job_config.get("gpu_count", 0),
        )
        replica_spec = build_replica_spec(container, job_config.get("node_count", 1))

        # 创建任务
        return HyperPodPytorchJob(
            metadata=Metadata(name=job_name),
            nproc_per_node=str(job_config.get("tasks_per_node", 1)),
            replica_specs=[replica_spec],
            run_policy=RunPolicy(),
        )

    async def trigger_preemption(
        self,
        cluster_name: str,
        target_job_name: str,
        preemption_job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """通过提交高优先级任务触发抢占。"""

        def _trigger() -> dict[str, Any]:
            self._validate_preemption_prerequisites(target_job_name)
            self._cluster.ensure_cluster_context(cluster_name)

            # 创建高优先级任务
            preemption_job_name = f"preempt-{target_job_name}-{int(time.time())}"
            preemption_job = self._create_preemption_job(preemption_job_name, preemption_job_config)
            preemption_job.create()

            return {
                "target_job_name": target_job_name,
                "preemption_job_name": preemption_job_name,
                "preemption_job_status": _get_initial_status(preemption_job),
                "mechanism": "high_priority_task",
            }

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _trigger)

    def _validate_preemption_prerequisites(self, target_job_name: str) -> None:
        """验证抢占前置条件."""
        if HyperPodPytorchJob is None:
            raise HyperPodSDKUnavailableError()

        target_job = HyperPodPytorchJob.get(name=target_job_name)
        if target_job.status != "Running":
            raise HyperPodOperationError("trigger_preemption", "Target job is not running", target_job_name)

    def _create_preemption_job(self, job_name: str, job_config: dict[str, Any]):
        """创建高优先级抢占任务."""
        from sagemaker.hyperpod.common.config import Metadata
        from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import RunPolicy

        # 设置高优先级环境变量
        env_dict = (job_config.get("environment") or {}).copy()
        env_dict["KUEUE_PRIORITY_CLASS"] = "critical"

        # 构建配置
        container = build_container(
            job_config.get("image_uri"),
            job_config.get("command"),
            env_dict,
            0,  # 不需要 GPU
        )
        replica_spec = build_replica_spec(container, job_config.get("node_count", 1))

        # 创建任务
        return HyperPodPytorchJob(
            metadata=Metadata(name=job_name),
            nproc_per_node="1",
            replica_specs=[replica_spec],
            run_policy=RunPolicy(),
        )

    async def get_pod_status(
        self,
        cluster_name: str,
        job_name: str,
        pod_name: str,
        namespace: str = "default",
    ) -> dict[str, Any]:
        """获取单个 Pod 状态。"""

        def _get_status() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise HyperPodSDKUnavailableError()

            self._cluster.ensure_cluster_context(cluster_name)

            job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
            pods = job.list_pods()

            for pod in pods:
                if pod.get("name") == pod_name:
                    return {
                        "name": pod_name,
                        "phase": pod.get("phase", "Unknown"),
                        "status": pod.get("status", {}),
                    }

            raise HyperPodPodNotFoundError(job_name, pod_name)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_status)
