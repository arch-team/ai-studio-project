"""Model API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema
from src.shared.utils import EnumMapper

if TYPE_CHECKING:
    from src.modules.models.domain.entities import Model


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

    @classmethod
    def _map_entity_fields(cls, entity: "Model") -> dict:
        """Map Model entity to summary schema fields."""
        return {
            "id": entity.id,
            "model_name": entity.model_name,
            "version": entity.version,
            "display_name": entity.display_name,
            "owner_id": entity.owner_id,
            "training_job_id": entity.training_job_id,
            "status": EnumMapper.to_api(entity.status, ModelStatusEnum),
            "framework": EnumMapper.to_api(entity.framework, ModelFrameworkEnum),
            "metrics": entity.metrics,
            "tags": entity.tags,
            "created_at": entity.created_at,
            "registered_at": entity.registered_at,
        }


class ModelDetail(EntitySchema["Model"]):
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

    @classmethod
    def _map_entity_fields(cls, entity: "Model") -> dict:
        """Map Model entity to detail schema fields."""
        return {
            "id": entity.id,
            "model_name": entity.model_name,
            "version": entity.version,
            "display_name": entity.display_name,
            "description": entity.description,
            "owner_id": entity.owner_id,
            "training_job_id": entity.training_job_id,
            "checkpoint_id": entity.checkpoint_id,
            "model_uri": entity.model_uri,
            "registry_arn": entity.registry_arn,
            "registry_status": entity.registry_status,
            "metrics": entity.metrics,
            "hyperparameters": entity.hyperparameters,
            "framework": EnumMapper.to_api(entity.framework, ModelFrameworkEnum),
            "framework_version": entity.framework_version,
            "status": EnumMapper.to_api(entity.status, ModelStatusEnum),
            "size_bytes": entity.size_bytes,
            "model_format": entity.model_format,
            "tags": entity.tags,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "registered_at": entity.registered_at,
            "archived_at": entity.archived_at,
        }


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
