"""Quotas API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.quotas.domain.entities import ResourceLimitConfig, ResourceQuota  # noqa: F401


class LimitRoleEnum(str, Enum):
    """Role for resource limit configuration."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class PriorityDefaultEnum(str, Enum):
    """Default priority for training jobs."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResourceLimitConfigResponse(EntitySchema["ResourceLimitConfig"]):
    """Resource limit config response.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

    id: int
    config_name: str
    role: LimitRoleEnum
    project_id: int | None = None
    max_gpu_per_job: int
    max_cpu_per_job: int
    max_memory_gb_per_job: int
    max_storage_gb_per_job: int
    max_nodes_per_job: int
    priority_default: PriorityDefaultEnum
    created_at: datetime
    updated_at: datetime


class ResourceLimitConfigListResponse(BaseModel):
    """Paginated list of resource limit configs."""

    items: list[ResourceLimitConfigResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# ResourceQuota Schemas (T058-T060)
# =============================================================================


class QuotaTypeEnum(str, Enum):
    """Quota type enumeration."""

    USER = "user"
    TEAM = "team"
    PROJECT = "project"


class QuotaStatusEnum(str, Enum):
    """Quota status enumeration."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class ResourceQuotaResponse(EntitySchema["ResourceQuota"]):
    """Resource quota response schema.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

    id: int
    name: str
    description: str | None = None
    quota_type: QuotaTypeEnum
    max_cpu_cores: int
    reserved_cpu_cores: int
    max_gpu_count: int
    reserved_gpu_count: int
    gpu_types: list[str] | None = None
    max_memory_gb: int
    reserved_memory_gb: int
    max_storage_gb: int | None = None
    max_concurrent_jobs: int
    max_total_jobs: int | None = None
    max_spot_instances: int
    status: QuotaStatusEnum
    valid_from: datetime
    valid_until: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ResourceQuotaListResponse(BaseModel):
    """Paginated list of resource quotas."""

    items: list[ResourceQuotaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
