"""Model API Schemas - Pydantic models for request/response."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# === Enums ===


class ModelFrameworkEnum(str, Enum):
    """Model framework types."""

    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    JAX = "jax"
    OTHER = "other"


class ModelStatusEnum(str, Enum):
    """Model status types."""

    TRAINING = "training"
    REGISTERED = "registered"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"
    FAILED = "failed"


# === Request Schemas ===


class CreateModelRequest(BaseModel):
    """Request body for registering a model (T031a)."""

    training_job_id: int = Field(..., description="Source training job ID")
    checkpoint_id: int = Field(..., description="Source checkpoint ID")
    model_name: str = Field(
        ...,
        min_length=3,
        max_length=128,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="Model name (lowercase alphanumeric with hyphens)",
    )
    display_name: str | None = Field(
        None, max_length=256, description="Human-readable display name"
    )
    description: str | None = Field(
        None, max_length=2000, description="Model description"
    )
    framework: ModelFrameworkEnum = Field(
        default=ModelFrameworkEnum.PYTORCH, description="ML framework"
    )
    framework_version: str | None = Field(
        None, max_length=32, description="Framework version"
    )
    metrics: dict[str, Any] | None = Field(
        None, description="Training metrics (accuracy, loss, f1_score, etc.)"
    )
    hyperparameters: dict[str, Any] | None = Field(
        None, description="Training hyperparameters"
    )
    tags: list[str] | None = Field(None, max_length=10, description="Model tags")


class UpdateModelRequest(BaseModel):
    """Request body for updating a model."""

    display_name: str | None = Field(
        None, max_length=256, description="Human-readable display name"
    )
    description: str | None = Field(
        None, max_length=2000, description="Model description"
    )
    tags: list[str] | None = Field(None, max_length=10, description="Model tags")


# === Response Schemas ===


class ModelSummary(BaseModel):
    """Model summary for list responses."""

    id: int
    model_name: str
    version: str
    display_name: str | None = None
    owner_id: int
    training_job_id: int | None = None
    status: ModelStatusEnum
    framework: ModelFrameworkEnum
    metrics: dict[str, Any] | None = None
    tags: list[str] | None = None
    created_at: datetime
    registered_at: datetime | None = None

    class Config:
        from_attributes = True


class ModelDetail(BaseModel):
    """Model detail response."""

    id: int
    model_name: str
    version: str
    display_name: str | None = None
    description: str | None = None
    owner_id: int

    # Relationships
    training_job_id: int | None = None
    checkpoint_id: int | None = None

    # Storage
    model_uri: str | None = None
    registry_arn: str | None = None
    registry_status: str | None = None

    # Training info
    metrics: dict[str, Any] | None = None
    hyperparameters: dict[str, Any] | None = None

    # Framework
    framework: ModelFrameworkEnum
    framework_version: str | None = None

    # Status
    status: ModelStatusEnum

    # Metadata
    size_bytes: int | None = None
    model_format: str | None = None
    tags: list[str] | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    registered_at: datetime | None = None
    archived_at: datetime | None = None

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Paginated list of models (T031b)."""

    items: list[ModelSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# === Version Comparison Schemas (T031c) ===


class MetricsDiff(BaseModel):
    """Metrics difference between versions."""

    v1: float | None = None
    v2: float | None = None
    diff: float | None = None
    diff_percent: float | None = None


class VersionComparison(BaseModel):
    """Comparison between two model versions."""

    metrics_diff: dict[str, MetricsDiff]
    hyperparams_changed: list[str]
    framework_changed: bool = False
    tags_added: list[str] = []
    tags_removed: list[str] = []


class ModelVersionSummary(BaseModel):
    """Summary of a model version."""

    id: int
    version: str
    status: ModelStatusEnum
    metrics: dict[str, Any] | None = None
    hyperparameters: dict[str, Any] | None = None
    created_at: datetime
    registered_at: datetime | None = None


class ModelVersionsResponse(BaseModel):
    """Model versions list response (T031c)."""

    model_name: str
    versions: list[ModelVersionSummary]
    comparison: VersionComparison | None = None


# === Error Schemas ===


class ModelErrorResponse(BaseModel):
    """Model operation error response."""

    code: str
    message: str
    details: dict | None = None
