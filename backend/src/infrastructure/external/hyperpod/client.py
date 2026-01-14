"""HyperPod Client - SageMaker HyperPod SDK integration.

Implements IHyperPodClient interface using sagemaker-hyperpod SDK and boto3.
"""

import asyncio
from typing import Any, Dict, List, Optional

import boto3

from src.application.interfaces.hyperpod_client import IHyperPodClient

# Note: These imports will be available when sagemaker-hyperpod is properly installed
# For now, we use try-except to handle potential import issues during testing
try:
    from sagemaker.hyperpod.training import HyperPodPytorchJob
    from sagemaker.hyperpod.cluster import Cluster
except ImportError:
    # Mock classes for testing when SDK is not available
    HyperPodPytorchJob = None  # type: ignore
    Cluster = None  # type: ignore


# Status mapping: HyperPod SDK status -> Platform standard status
STATUS_MAPPING = {
    "Pending": "submitted",
    "Running": "running",
    "Succeeded": "completed",
    "Failed": "failed",
}


def _map_status(hyperpod_status: str) -> str:
    """Map HyperPod status to platform standard status."""
    return STATUS_MAPPING.get(hyperpod_status, "unknown")


class HyperPodClient(IHyperPodClient):
    """HyperPod SDK client implementation.

    Wraps sagemaker-hyperpod SDK and boto3 for cluster and training job management.
    All operations are async for FastAPI compatibility.
    """

    def __init__(self, region: str = "us-west-2") -> None:
        """Initialize HyperPod client.

        Args:
            region: AWS region for the client.
        """
        self._region = region
        self._sagemaker_client = boto3.client("sagemaker", region_name=region)

    async def create_cluster(
        self,
        cluster_name: str,
        instance_groups: List[Dict[str, Any]],
        vpc_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new HyperPod cluster.

        Uses boto3 SageMaker API for cluster creation.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._sagemaker_client.create_cluster(
                ClusterName=cluster_name,
                InstanceGroups=instance_groups,
                VpcConfig=vpc_config,
            ),
        )

    async def describe_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Get cluster details using HyperPod SDK."""
        loop = asyncio.get_event_loop()

        def _describe() -> Dict[str, Any]:
            if Cluster is None:
                # Fallback to boto3 if SDK is not available
                return self._sagemaker_client.describe_cluster(ClusterName=cluster_name)
            return Cluster.describe(cluster_name=cluster_name)

        return await loop.run_in_executor(None, _describe)

    async def list_clusters(
        self, max_results: int = 100, next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all HyperPod clusters."""
        loop = asyncio.get_event_loop()

        def _list() -> Dict[str, Any]:
            params: Dict[str, Any] = {"MaxResults": max_results}
            if next_token:
                params["NextToken"] = next_token
            return self._sagemaker_client.list_clusters(**params)

        return await loop.run_in_executor(None, _list)

    async def delete_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Delete a HyperPod cluster."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._sagemaker_client.delete_cluster(ClusterName=cluster_name),
        )

    async def update_cluster(
        self, cluster_name: str, instance_groups: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update cluster instance groups."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._sagemaker_client.update_cluster(
                ClusterName=cluster_name,
                InstanceGroups=instance_groups,
            ),
        )

    async def submit_training_job(
        self,
        cluster_name: str,
        job_name: str,
        job_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit a training job to the cluster using HyperPod SDK."""
        loop = asyncio.get_event_loop()

        def _submit() -> Dict[str, Any]:
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

        return await loop.run_in_executor(None, _submit)

    async def get_training_job_status(
        self, cluster_name: str, job_name: str
    ) -> Dict[str, Any]:
        """Get training job status using HyperPod SDK."""
        loop = asyncio.get_event_loop()

        def _get_status() -> Dict[str, Any]:
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

        return await loop.run_in_executor(None, _get_status)

    async def stop_training_job(
        self, cluster_name: str, job_name: str
    ) -> Dict[str, Any]:
        """Stop a running training job using HyperPod SDK."""
        loop = asyncio.get_event_loop()

        def _stop() -> Dict[str, Any]:
            if HyperPodPytorchJob is None:
                raise RuntimeError("HyperPod SDK not available")

            job = HyperPodPytorchJob.get(name=job_name)
            job.delete()

            return {
                "job_name": job_name,
                "status": "stopped",
                "cluster_name": cluster_name,
            }

        return await loop.run_in_executor(None, _stop)
