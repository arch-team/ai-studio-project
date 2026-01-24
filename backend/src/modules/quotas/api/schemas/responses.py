"""Quotas API response schemas."""

from datetime import datetime
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel

from src.shared.api.schemas import AutoMappingEntitySchema


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


class ResourceLimitConfigResponse(AutoMappingEntitySchema["ResourceLimitConfig"]):
    """Resource limit config response.

    使用 AutoMappingEntitySchema 自动映射同名字段，
    只需声明枚举映射规则。
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

    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
        "role": LimitRoleEnum,
        "priority_default": PriorityDefaultEnum,
    }


class ResourceLimitConfigListResponse(BaseModel):
    """Paginated list of resource limit configs."""

    items: list[ResourceLimitConfigResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
