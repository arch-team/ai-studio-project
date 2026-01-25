"""Quotas API request schemas."""

from enum import Enum

from pydantic import BaseModel, Field


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


class CreateResourceQuotaRequest(BaseModel):
    """Request body for creating a resource quota."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Quota name (unique)",
    )
    description: str | None = Field(
        None,
        max_length=1024,
        description="Quota description",
    )
    quota_type: QuotaTypeEnum = Field(
        default=QuotaTypeEnum.USER,
        description="Quota type (user, team, project)",
    )
    max_cpu_cores: int = Field(
        ...,
        ge=1,
        le=10000,
        description="Maximum CPU cores",
    )
    max_gpu_count: int = Field(
        ...,
        ge=1,
        le=1024,
        description="Maximum GPU count",
    )
    max_memory_gb: int = Field(
        ...,
        ge=1,
        le=65536,
        description="Maximum memory (GB)",
    )
    max_concurrent_jobs: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum concurrent jobs",
    )
    gpu_types: list[str] | None = Field(
        None,
        description="Allowed GPU types",
    )
    valid_until: str | None = Field(
        None,
        description="Expiration datetime (ISO 8601)",
    )


class UpdateResourceQuotaRequest(BaseModel):
    """Request body for updating a resource quota."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=128,
        description="Quota name (unique)",
    )
    description: str | None = Field(
        None,
        max_length=1024,
        description="Quota description",
    )
    quota_type: QuotaTypeEnum | None = Field(
        None,
        description="Quota type",
    )
    max_cpu_cores: int | None = Field(
        None,
        ge=1,
        le=10000,
        description="Maximum CPU cores",
    )
    max_gpu_count: int | None = Field(
        None,
        ge=1,
        le=1024,
        description="Maximum GPU count",
    )
    max_memory_gb: int | None = Field(
        None,
        ge=1,
        le=65536,
        description="Maximum memory (GB)",
    )
    max_concurrent_jobs: int | None = Field(
        None,
        ge=1,
        le=100,
        description="Maximum concurrent jobs",
    )
    gpu_types: list[str] | None = Field(
        None,
        description="Allowed GPU types",
    )
    status: QuotaStatusEnum | None = Field(
        None,
        description="Quota status",
    )
    valid_until: str | None = Field(
        None,
        description="Expiration datetime (ISO 8601)",
    )
