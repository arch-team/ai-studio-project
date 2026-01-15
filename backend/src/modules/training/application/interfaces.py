"""HyperPod Client Interface - SageMaker HyperPod operations contract."""

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
    async def list_clusters(
        self, max_results: int = 100, next_token: str | None = None
    ) -> dict[str, Any]:
        """List all HyperPod clusters."""

    @abstractmethod
    async def delete_cluster(self, cluster_name: str) -> dict[str, Any]:
        """Delete a HyperPod cluster."""

    @abstractmethod
    async def update_cluster(
        self, cluster_name: str, instance_groups: list[dict[str, Any]]
    ) -> dict[str, Any]:
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
    async def get_training_job_status(
        self, cluster_name: str, job_name: str
    ) -> dict[str, Any]:
        """Get training job status."""

    @abstractmethod
    async def stop_training_job(
        self, cluster_name: str, job_name: str
    ) -> dict[str, Any]:
        """Stop a running training job."""

    @abstractmethod
    async def list_training_job_pods(
        self, cluster_name: str, job_name: str
    ) -> list[dict[str, Any]]:
        """List pods for a training job."""
