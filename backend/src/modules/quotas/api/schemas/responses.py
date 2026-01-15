"""Quotas API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.quotas.domain.entities import ResourceLimitConfig


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
    """Resource limit config response."""

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

    @classmethod
    def _map_entity_fields(cls, entity: "ResourceLimitConfig") -> dict:
        """Map ResourceLimitConfig entity to schema fields."""
        return {
            "id": entity.id,
            "config_name": entity.config_name,
            "role": LimitRoleEnum(entity.role.value),
            "project_id": entity.project_id,
            "max_gpu_per_job": entity.max_gpu_per_job,
            "max_cpu_per_job": entity.max_cpu_per_job,
            "max_memory_gb_per_job": entity.max_memory_gb_per_job,
            "max_storage_gb_per_job": entity.max_storage_gb_per_job,
            "max_nodes_per_job": entity.max_nodes_per_job,
            "priority_default": PriorityDefaultEnum(entity.priority_default.value),
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }


class ResourceLimitConfigListResponse(BaseModel):
    """Paginated list of resource limit configs."""

    items: list[ResourceLimitConfigResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
