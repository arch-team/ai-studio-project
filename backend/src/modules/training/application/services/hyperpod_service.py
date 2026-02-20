"""HyperPod 服务 - 通过 HyperPod SDK 管理训练任务生命周期。

T036: HyperPodPytorchJob 集成逻辑
封装 HyperPod SDK 操作，提供重试机制和错误处理。
"""

import asyncio
from typing import Any

import structlog

from src.modules.training.application.interfaces import IHyperPodClient
from src.modules.training.domain.entities.training_job import TrainingJob
from src.shared.domain.exceptions import EntityNotFoundError

logger = structlog.get_logger(__name__)

# 状态映射: HyperPod SDK 状态 → 平台标准状态
STATUS_MAPPING = {
    "Pending": "submitted",
    "Running": "running",
    "Succeeded": "completed",
    "Failed": "failed",
}


def map_hyperpod_status(hyperpod_status: str) -> str:
    """将 HyperPod 状态映射为平台标准状态."""
    return STATUS_MAPPING.get(hyperpod_status, "unknown")


def build_volume_config(
    data_path: str | None = None,
    checkpoint_path: str | None = None,
) -> list[dict[str, Any]]:
    """构建 FSx for Lustre 卷挂载配置."""
    # (卷名, 容器挂载路径, 宿主机路径)
    volume_specs = [
        ("training-data", "/data", data_path),
        ("checkpoints", "/checkpoints", checkpoint_path),
    ]
    return [
        {"name": name, "type": "hostPath", "mount_path": mount, "path": path}
        for name, mount, path in volume_specs
        if path
    ]


def build_job_config(job: TrainingJob) -> dict[str, Any]:
    """从 TrainingJob 实体构建 HyperPod 任务配置."""
    config: dict[str, Any] = {
        "image_uri": job.image_uri,
        "instance_type": job.instance_type,
        "node_count": job.node_count,
        "tasks_per_node": job.tasks_per_node,
        "command": job.entrypoint_command,
    }

    if job.environment_variables:
        config["environment"] = job.environment_variables

    return config


class HyperPodServiceError(Exception):
    """HyperPod 服务异常，包含重试信息."""

    def __init__(self, message: str, retries: int = 0, original_error: Exception | None = None):
        super().__init__(message)
        self.retries = retries
        self.original_error = original_error


class HyperPodService:
    """HyperPod SDK 服务 - 管理训练任务生命周期。

    提供提交、暂停、恢复、终止操作，内置重试机制。
    """

    def __init__(
        self,
        hyperpod_client: IHyperPodClient,
        cluster_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self._client = hyperpod_client
        self._cluster_name = cluster_name
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def _execute_with_retry(
        self,
        operation: str,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """带重试的操作执行。

        Raises:
            HyperPodServiceError: 超过最大重试次数后抛出
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(
                    "hyperpod_operation_retry",
                    operation=operation,
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    error_type=type(e).__name__,
                    error=str(e),
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay)

        raise HyperPodServiceError(
            f"{operation} failed after {self._max_retries} retries: {last_error}",
            retries=self._max_retries,
            original_error=last_error,
        )

    async def submit_job(
        self,
        job_name: str,
        job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """向 HyperPod 集群提交训练任务.

        Raises:
            HyperPodServiceError: 提交失败
        """
        return await self._execute_with_retry(
            "submit_job",
            self._client.submit_training_job,
            cluster_name=self._cluster_name,
            job_name=job_name,
            job_config=job_config,
        )

    async def get_job_status(self, job_name: str) -> dict[str, Any]:
        """获取训练任务状态.

        Raises:
            EntityNotFoundError: 任务不存在
        """
        try:
            return await self._client.get_training_job_status(
                cluster_name=self._cluster_name,
                job_name=job_name,
            )
        except Exception as e:
            if "not found" in str(e).lower():
                logger.info("job_not_found_in_hyperpod", job_name=job_name)
                raise EntityNotFoundError(
                    entity_type="TrainingJob",
                    entity_id=job_name,
                ) from e
            logger.error("get_job_status_failed", job_name=job_name, error_type=type(e).__name__, error=str(e))
            raise

    async def terminate_job(self, job_name: str) -> dict[str, Any]:
        """终止运行中的训练任务.

        Raises:
            HyperPodServiceError: 终止失败
        """
        return await self._execute_with_retry(
            "terminate_job",
            self._client.stop_training_job,
            cluster_name=self._cluster_name,
            job_name=job_name,
        )

    async def pause_job(self, job_name: str) -> dict[str, Any]:
        """暂停训练任务.

        HyperPod SDK 无原生暂停支持，通过信号触发 checkpoint + 终止实现。
        训练脚本负责优雅退出。
        """
        await self._client.stop_training_job(
            cluster_name=self._cluster_name,
            job_name=job_name,
        )

        return {
            "job_name": job_name,
            "status": "paused",
            "cluster_name": self._cluster_name,
        }

    async def resume_job(
        self,
        job_name: str,
        job_config: dict[str, Any],
        checkpoint_path: str | None = None,
    ) -> dict[str, Any]:
        """恢复已暂停的训练任务。通过携带 checkpoint 路径重新提交实现."""
        config = dict(job_config)
        if checkpoint_path:
            config["checkpoint_path"] = checkpoint_path

        return await self._client.submit_training_job(
            cluster_name=self._cluster_name,
            job_name=job_name,
            job_config=config,
        )

    async def list_job_pods(self, job_name: str) -> list[dict[str, Any]]:
        """列出训练任务的 Pod 列表."""
        return await self._client.list_training_job_pods(
            cluster_name=self._cluster_name,
            job_name=job_name,
        )
