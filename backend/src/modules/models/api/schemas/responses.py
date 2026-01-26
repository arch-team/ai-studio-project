"""Model API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.models.domain.entities import Model  # noqa: F401


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


class ModelSummary(EntitySchema["Model"]):
    """Model summary for list responses.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

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


class ModelDetail(ModelSummary):
    """Model detail response - 继承 ModelSummary 扩展更多字段."""

    description: str | None = None

    # Relationships
    checkpoint_id: int | None = None

    # Storage
    model_uri: str | None = None
    registry_arn: str | None = None
    registry_status: str | None = None

    # Training info
    hyperparameters: dict[str, Any] | None = None

    # Framework
    framework_version: str | None = None

    # Metadata
    size_bytes: int | None = None
    model_format: str | None = None

    # Timestamps
    updated_at: datetime
    archived_at: datetime | None = None

    # 继承父类的枚举映射，无需重复声明


class ModelListResponse(BaseModel):
    """Paginated list of models."""

    items: list[ModelSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# === Version Comparison Schemas ===


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
    """Model versions list response."""

    model_name: str
    versions: list[ModelVersionSummary]
    comparison: VersionComparison | None = None


# === Error Schemas ===


class ModelErrorResponse(BaseModel):
    """Model operation error response."""

    code: str
    message: str
    details: dict | None = None
