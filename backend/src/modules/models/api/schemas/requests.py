"""Model API request schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModelFrameworkEnum(str, Enum):
    """Model framework types."""

    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    JAX = "jax"
    OTHER = "other"


class CreateModelRequest(BaseModel):
    """Request body for registering a model."""

    training_job_id: int = Field(..., description="Source training job ID")
    checkpoint_id: int = Field(..., description="Source checkpoint ID")
    model_name: str = Field(
        ...,
        min_length=3,
        max_length=128,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="Model name (lowercase alphanumeric with hyphens)",
    )
    display_name: str | None = Field(None, max_length=256, description="Human-readable display name")
    description: str | None = Field(None, max_length=2000, description="Model description")
    framework: ModelFrameworkEnum = Field(default=ModelFrameworkEnum.PYTORCH, description="ML framework")
    framework_version: str | None = Field(None, max_length=32, description="Framework version")
    metrics: dict[str, Any] | None = Field(None, description="Training metrics (accuracy, loss, f1_score, etc.)")
    hyperparameters: dict[str, Any] | None = Field(None, description="Training hyperparameters")
    tags: list[str] | None = Field(None, max_length=10, description="Model tags")


class UpdateModelRequest(BaseModel):
    """Request body for updating a model."""

    display_name: str | None = Field(None, max_length=256, description="Human-readable display name")
    description: str | None = Field(None, max_length=2000, description="Model description")
    tags: list[str] | None = Field(None, max_length=10, description="Model tags")
