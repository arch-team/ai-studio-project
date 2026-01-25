"""HyperPodCluster Repository Interface (T068)."""

from abc import ABC, abstractmethod

from ..entities import HyperPodCluster
from ..value_objects import ClusterStatus


class IHyperPodClusterRepository(ABC):
    """Abstract repository interface for HyperPodCluster entity."""

    @abstractmethod
    async def get_by_id(self, cluster_id: int) -> HyperPodCluster | None:
        """Get cluster by ID."""

    @abstractmethod
    async def get_by_name(self, cluster_name: str) -> HyperPodCluster | None:
        """Get cluster by name."""

    @abstractmethod
    async def get_by_arn(self, cluster_arn: str) -> HyperPodCluster | None:
        """Get cluster by ARN."""

    @abstractmethod
    async def create(self, cluster: HyperPodCluster) -> HyperPodCluster:
        """Create a new cluster."""

    @abstractmethod
    async def update(self, cluster: HyperPodCluster) -> HyperPodCluster:
        """Update an existing cluster."""

    @abstractmethod
    async def list_clusters(
        self,
        offset: int = 0,
        limit: int = 20,
        status: ClusterStatus | None = None,
    ) -> list[HyperPodCluster]:
        """List clusters with pagination and optional status filter."""

    @abstractmethod
    async def count_clusters(
        self,
        status: ClusterStatus | None = None,
    ) -> int:
        """Count clusters with optional status filter."""
