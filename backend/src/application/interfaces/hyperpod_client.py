"""HyperPod Client Interface - SageMaker HyperPod operations contract.

Defines the port interface for HyperPod cluster management operations.
Infrastructure layer provides the concrete implementation using AWS SDK.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IHyperPodClient(ABC):
    """Interface for SageMaker HyperPod operations.

    This interface abstracts the HyperPod SDK, allowing the application
    layer to interact with HyperPod without depending on AWS SDK details.
    """

    @abstractmethod
    async def create_cluster(
        self,
        cluster_name: str,
        instance_groups: List[Dict[str, Any]],
        vpc_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new HyperPod cluster.

        Args:
            cluster_name: Name for the cluster.
            instance_groups: List of instance group configurations.
            vpc_config: VPC and subnet configuration.

        Returns:
            Cluster creation response with ARN and status.
        """
        pass

    @abstractmethod
    async def describe_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Get cluster details.

        Args:
            cluster_name: Name of the cluster.

        Returns:
            Cluster details including status and instance groups.
        """
        pass

    @abstractmethod
    async def list_clusters(
        self, max_results: int = 100, next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all HyperPod clusters.

        Args:
            max_results: Maximum number of results.
            next_token: Pagination token.

        Returns:
            List of clusters with pagination info.
        """
        pass

    @abstractmethod
    async def delete_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Delete a HyperPod cluster.

        Args:
            cluster_name: Name of the cluster to delete.

        Returns:
            Deletion confirmation response.
        """
        pass

    @abstractmethod
    async def update_cluster(
        self, cluster_name: str, instance_groups: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update cluster instance groups.

        Args:
            cluster_name: Name of the cluster.
            instance_groups: Updated instance group configurations.

        Returns:
            Update response with new cluster state.
        """
        pass

    @abstractmethod
    async def submit_training_job(
        self,
        cluster_name: str,
        job_name: str,
        job_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit a training job to the cluster.

        Args:
            cluster_name: Target cluster name.
            job_name: Name for the training job.
            job_config: Training job configuration.

        Returns:
            Job submission response with job ID.
        """
        pass

    @abstractmethod
    async def get_training_job_status(
        self, cluster_name: str, job_name: str
    ) -> Dict[str, Any]:
        """Get training job status.

        Args:
            cluster_name: Cluster running the job.
            job_name: Name of the training job.

        Returns:
            Job status and details.
        """
        pass

    @abstractmethod
    async def stop_training_job(
        self, cluster_name: str, job_name: str
    ) -> Dict[str, Any]:
        """Stop a running training job.

        Args:
            cluster_name: Cluster running the job.
            job_name: Name of the training job.

        Returns:
            Stop confirmation response.
        """
        pass
