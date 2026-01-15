"""ResourceLimitConfig API Schemas - Pydantic models for request/response."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.api.v1.schemas.common import ErrorResponse

__all__ = [
    "LimitRoleEnum",
    "PriorityDefaultEnum",
    "CreateResourceLimitConfigRequest",
    "UpdateResourceLimitConfigRequest",
    "ResourceLimitConfigResponse",
    "ResourceLimitConfigListResponse",
    "ErrorResponse",
]

# === Enums ===


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


# === Request Schemas ===


class CreateResourceLimitConfigRequest(BaseModel):
    """Request body for creating a resource limit config."""

    config_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Configuration name",
    )
    role: LimitRoleEnum = Field(..., description="Applicable role")
    project_id: int | None = Field(
        None,
        description="Project ID (null for global config)",
    )
    max_gpu_per_job: int = Field(
        default=8,
        ge=1,
        le=1024,
        description="Maximum GPUs per job",
    )
    max_cpu_per_job: int = Field(
        default=64,
        ge=1,
        le=4096,
        description="Maximum CPU cores per job",
    )
    max_memory_gb_per_job: int = Field(
        default=512,
        ge=1,
        le=16384,
        description="Maximum memory (GB) per job",
    )
    max_storage_gb_per_job: int = Field(
        default=1000,
        ge=1,
        le=102400,
        description="Maximum storage (GB) per job",
    )
    max_nodes_per_job: int = Field(
        default=4,
        ge=1,
        le=256,
        description="Maximum nodes per job",
    )
    priority_default: PriorityDefaultEnum = Field(
        default=PriorityDefaultEnum.MEDIUM,
        description="Default priority for new jobs",
    )


class UpdateResourceLimitConfigRequest(BaseModel):
    """Request body for updating a resource limit config."""

    config_name: str | None = Field(
        None,
        min_length=1,
        max_length=128,
        description="Configuration name",
    )
    role: LimitRoleEnum | None = Field(None, description="Applicable role")
    project_id: int | None = Field(
        None,
        description="Project ID (null for global config)",
    )
    max_gpu_per_job: int | None = Field(
        None,
        ge=1,
        le=1024,
        description="Maximum GPUs per job",
    )
    max_cpu_per_job: int | None = Field(
        None,
        ge=1,
        le=4096,
        description="Maximum CPU cores per job",
    )
    max_memory_gb_per_job: int | None = Field(
        None,
        ge=1,
        le=16384,
        description="Maximum memory (GB) per job",
    )
    max_storage_gb_per_job: int | None = Field(
        None,
        ge=1,
        le=102400,
        description="Maximum storage (GB) per job",
    )
    max_nodes_per_job: int | None = Field(
        None,
        ge=1,
        le=256,
        description="Maximum nodes per job",
    )
    priority_default: PriorityDefaultEnum | None = Field(
        None,
        description="Default priority for new jobs",
    )


# === Response Schemas ===


class ResourceLimitConfigResponse(BaseModel):
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

    class Config:
        from_attributes = True


class ResourceLimitConfigListResponse(BaseModel):
    """Paginated list of resource limit configs."""

    items: list[ResourceLimitConfigResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ErrorResponse is imported from common.py
