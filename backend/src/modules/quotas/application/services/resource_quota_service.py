"""ResourceQuota Application Service (T058-T060).

业务用例编排，处理资源配额的 CRUD 操作。
继承 BaseApplicationService 复用通用 CRUD 模式。
"""

from typing import Any

from src.modules.quotas.domain.entities import ResourceQuota
from src.modules.quotas.domain.exceptions import (
    DuplicateQuotaNameError,
    QuotaNotFoundError,
)
from src.modules.quotas.domain.repositories import IResourceQuotaRepository
from src.modules.quotas.domain.value_objects import QuotaStatus, QuotaType
from src.shared.application.base_service_unified import BaseApplicationService
from src.shared.utils import utc_now


class ResourceQuotaService(BaseApplicationService[ResourceQuota, int]):
    """Application service for ResourceQuota operations."""

    _not_found_error_factory = staticmethod(lambda id: QuotaNotFoundError(identifier=id))

    def __init__(self, repository: IResourceQuotaRepository) -> None:
        super().__init__(repository, "ResourceQuota")

    async def get_quota(self, quota_id: int) -> ResourceQuota:
        """获取配额。

        Raises:
            QuotaNotFoundError: 配额不存在。
        """
        return await self._get_or_raise(quota_id)

    async def list_quotas(
        self,
        quota_type: QuotaType | None = None,
        status: QuotaStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[ResourceQuota], int]:
        """列出配额（带分页和过滤）。"""
        return await self._repository.list_quotas(
            quota_type=quota_type,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def create_quota(self, data: dict[str, Any]) -> ResourceQuota:
        """创建配额。

        Raises:
            DuplicateQuotaNameError: 配额名称已存在。
        """
        if await self._repository.exists_by_name(data["name"]):
            raise DuplicateQuotaNameError(name=data["name"])

        now = utc_now()
        quota = ResourceQuota(
            id=0,
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

    async def update_quota(self, quota_id: int, data: dict[str, Any]) -> ResourceQuota:
        """更新配额。

        Raises:
            QuotaNotFoundError: 配额不存在。
            DuplicateQuotaNameError: 新名称冲突。
        """
        quota = await self._get_or_raise(quota_id)

        # 名称唯一性检查
        new_name = data.get("name")
        if new_name and new_name != quota.name:
            if await self._repository.exists_by_name(new_name):
                raise DuplicateQuotaNameError(name=new_name)

        # 更新字段
        updatable_fields = [
            "name", "description", "max_cpu_cores", "reserved_cpu_cores",
            "max_gpu_count", "reserved_gpu_count", "gpu_types",
            "max_memory_gb", "reserved_memory_gb", "max_storage_gb",
            "max_concurrent_jobs", "max_total_jobs", "max_spot_instances",
            "valid_from", "valid_until",
        ]
        for field in updatable_fields:
            if field in data:
                setattr(quota, field, data[field])

        if "quota_type" in data:
            quota.quota_type = QuotaType(data["quota_type"])
        if "status" in data:
            quota.status = QuotaStatus(data["status"])

        quota.updated_at = utc_now()
        return await self._repository.update(quota)

    async def delete_quota(self, quota_id: int) -> None:
        """删除（软删除）配额。

        Raises:
            QuotaNotFoundError: 配额不存在。
        """
        success = await self._repository.soft_delete(quota_id)
        if not success:
            raise QuotaNotFoundError(identifier=str(quota_id))
