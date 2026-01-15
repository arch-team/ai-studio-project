"""HyperPod Client - SageMaker HyperPod SDK integration."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

import boto3

from src.modules.training.application.interfaces import IHyperPodClient

# Conditional imports for testing environments
try:
    from sagemaker.hyperpod.training import HyperPodPytorchJob
except ImportError:
    HyperPodPytorchJob = None  # type: ignore


STATUS_MAPPING = {
    "Pending": "submitted",
    "Running": "running",
    "Succeeded": "completed",
    "Failed": "failed",
}


def _map_status(hyperpod_status: str) -> str:
    """Map HyperPod status to platform standard status."""
    return STATUS_MAPPING.get(hyperpod_status, "unknown")


T = TypeVar("T")


class HyperPodClient(IHyperPodClient):
    """HyperPod SDK client implementation."""

    def __init__(self, region: str = "us-west-2") -> None:
        """Initialize HyperPod client."""
        self._region = region
        self._sagemaker_client = boto3.client("sagemaker", region_name=region)

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

        def _describe() -> dict[str, Any]:
            return self._sagemaker_client.describe_cluster(ClusterName=cluster_name)

        return await self._run_in_executor(_describe)

    async def list_clusters(
        self, max_results: int = 100, next_token: str | None = None
    ) -> dict[str, Any]:
        """List all HyperPod clusters."""

        def _list() -> dict[str, Any]:
            params: dict[str, Any] = {"MaxResults": max_results}
            if next_token:
                params["NextToken"] = next_token
            return self._sagemaker_client.list_clusters(**params)

        return await self._run_in_executor(_list)

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
        """Submit a training job to the cluster using HyperPod SDK."""

        def _submit() -> dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            job = HyperPodPytorchJob.create(
                name=job_name,
                image_uri=job_config.get("image_uri"),
                instance_type=job_config.get("instance_type"),
                node_count=job_config.get("node_count", 1),
                tasks_per_node=job_config.get("tasks_per_node", 1),
                command=job_config.get("command"),
                environment=job_config.get("environment"),
                volumes=job_config.get("volumes"),
            )

            return {
                "job_name": job.name,
                "status": _map_status(job.status),
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

            job = HyperPodPytorchJob.get(name=job_name)

            return {
                "job_name": job.name,
                "status": _map_status(job.status),
                "start_time": getattr(job, "start_time", None),
                "end_time": getattr(job, "end_time", None),
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

            job = HyperPodPytorchJob.get(name=job_name)
            return job.list_pods()

        return await self._run_in_executor(_list_pods)
