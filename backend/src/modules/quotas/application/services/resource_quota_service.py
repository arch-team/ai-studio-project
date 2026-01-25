"""ResourceQuota Application Service (T058-T060).

业务用例编排，处理资源配额的 CRUD 操作。
"""

from typing import Any

from src.modules.quotas.domain.entities import ResourceQuota
from src.modules.quotas.domain.exceptions import (
    DuplicateQuotaNameError,
    QuotaNotFoundError,
)
from src.modules.quotas.domain.repositories import IResourceQuotaRepository
from src.modules.quotas.domain.value_objects import QuotaStatus, QuotaType
from src.shared.utils import utc_now


class ResourceQuotaService:
    """Application service for ResourceQuota operations."""

    def __init__(self, repository: IResourceQuotaRepository) -> None:
        """Initialize service with repository."""
        self._repository = repository

    async def get_quota(self, quota_id: int) -> ResourceQuota:
        """Get a quota by ID.

        Raises:
            QuotaNotFoundError: If quota not found.
        """
        quota = await self._repository.get_by_id(quota_id)
        if quota is None:
            raise QuotaNotFoundError(identifier=str(quota_id))
        return quota

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
        return await self._repository.list_quotas(
            quota_type=quota_type,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def create_quota(self, data: dict[str, Any]) -> ResourceQuota:
        """Create a new quota.

        Raises:
            DuplicateQuotaNameError: If quota name already exists.
        """
        # Check for duplicate name
        if await self._repository.exists_by_name(data["name"]):
            raise DuplicateQuotaNameError(name=data["name"])

        # Build entity
        now = utc_now()
        quota = ResourceQuota(
            id=0,  # Will be assigned by database
            name=data["name"],
            description=data.get("description"),
            quota_type=QuotaType(data["quota_type"]),
            max_cpu_cores=data["max_cpu_cores"],
            reserved_cpu_cores=data.get("reserved_cpu_cores", 0),
            max_gpu_count=data["max_gpu_count"],
            reserved_gpu_count=data.get("reserved_gpu_count", 0),
            gpu_types=data.get("gpu_types", []),
            max_memory_gb=data["max_memory_gb"],
            reserved_memory_gb=data.get("reserved_memory_gb", 0),
            max_storage_gb=data.get("max_storage_gb"),
            max_concurrent_jobs=data.get("max_concurrent_jobs", 5),
            max_total_jobs=data.get("max_total_jobs"),
            max_spot_instances=data.get("max_spot_instances", 0),
            status=QuotaStatus.ACTIVE,
            valid_from=data.get("valid_from", now),
            valid_until=data.get("valid_until"),
            created_by=data.get("created_by"),
            created_at=now,
            updated_at=now,
        )

        return await self._repository.create(quota)

    async def update_quota(
        self, quota_id: int, data: dict[str, Any]
    ) -> ResourceQuota:
        """Update an existing quota.

        Raises:
            QuotaNotFoundError: If quota not found.
            DuplicateQuotaNameError: If new name conflicts.
        """
        quota = await self._repository.get_by_id(quota_id)
        if quota is None:
            raise QuotaNotFoundError(identifier=str(quota_id))

        # Check name uniqueness if changing
        new_name = data.get("name")
        if new_name and new_name != quota.name:
            if await self._repository.exists_by_name(new_name):
                raise DuplicateQuotaNameError(name=new_name)
            quota.name = new_name

        # Update fields
        if "description" in data:
            quota.description = data["description"]
        if "quota_type" in data:
            quota.quota_type = QuotaType(data["quota_type"])
        if "max_cpu_cores" in data:
            quota.max_cpu_cores = data["max_cpu_cores"]
        if "reserved_cpu_cores" in data:
            quota.reserved_cpu_cores = data["reserved_cpu_cores"]
        if "max_gpu_count" in data:
            quota.max_gpu_count = data["max_gpu_count"]
        if "reserved_gpu_count" in data:
            quota.reserved_gpu_count = data["reserved_gpu_count"]
        if "gpu_types" in data:
            quota.gpu_types = data["gpu_types"]
        if "max_memory_gb" in data:
            quota.max_memory_gb = data["max_memory_gb"]
        if "reserved_memory_gb" in data:
            quota.reserved_memory_gb = data["reserved_memory_gb"]
        if "max_storage_gb" in data:
            quota.max_storage_gb = data["max_storage_gb"]
        if "max_concurrent_jobs" in data:
            quota.max_concurrent_jobs = data["max_concurrent_jobs"]
        if "max_total_jobs" in data:
            quota.max_total_jobs = data["max_total_jobs"]
        if "max_spot_instances" in data:
            quota.max_spot_instances = data["max_spot_instances"]
        if "status" in data:
            quota.status = QuotaStatus(data["status"])
        if "valid_from" in data:
            quota.valid_from = data["valid_from"]
        if "valid_until" in data:
            quota.valid_until = data["valid_until"]

        quota.updated_at = utc_now()
        return await self._repository.update(quota)

    async def delete_quota(self, quota_id: int) -> None:
        """Delete (soft) a quota.

        Raises:
            QuotaNotFoundError: If quota not found.
        """
        success = await self._repository.soft_delete(quota_id)
        if not success:
            raise QuotaNotFoundError(identifier=str(quota_id))
