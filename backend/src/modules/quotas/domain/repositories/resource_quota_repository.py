"""ResourceQuota Repository Interface - Abstract data access contract (T058-T060)."""

from abc import ABC, abstractmethod

from ..entities import ResourceQuota
from ..value_objects import QuotaStatus, QuotaType


class IResourceQuotaRepository(ABC):
    """Abstract repository interface for ResourceQuota."""

    @abstractmethod
    async def get_by_id(self, quota_id: int) -> ResourceQuota | None:
        """Get quota by ID."""

    @abstractmethod
    async def get_by_name(self, name: str) -> ResourceQuota | None:
        """Get quota by unique name."""

    @abstractmethod
    async def list_quotas(
        self,
        quota_type: QuotaType | None = None,
        status: QuotaStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[ResourceQuota], int]:
        """List quotas with pagination and filters."""

    @abstractmethod
    async def create(self, quota: ResourceQuota) -> ResourceQuota:
        """Create a new quota."""

    @abstractmethod
    async def update(self, quota: ResourceQuota) -> ResourceQuota:
        """Update an existing quota."""

    @abstractmethod
    async def soft_delete(self, quota_id: int) -> bool:
        """Soft delete a quota (set status to expired)."""

    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check if quota with name exists."""
