"""Training API request schemas."""

import re
from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class DistributionStrategyEnum(str, Enum):
    """Distributed training strategy."""

    DDP = "ddp"
    FSDP = "fsdp"
    DEEPSPEED = "deepspeed"
    HOROVOD = "horovod"


class JobPriorityEnum(str, Enum):
    """Job priority for scheduling."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CreateTrainingJobRequest(BaseModel):
    """Request body for creating a training job.

    entry_point/gpu_per_node 是前端契约别名：
    - entry_point (脚本路径) -> entrypoint_command = ["python", entry_point]
    - gpu_per_node -> tasks_per_node
    """

    job_name: str = Field(..., min_length=1, max_length=128, description="Job name")
    image_uri: str = Field(..., description="Docker image URI")
    instance_type: str = Field(..., description="Instance type (e.g., ml.p4d.24xlarge)")
    entrypoint_command: list[str] | None = Field(None, description="Entrypoint command")
    entry_point: str | None = Field(None, description="Training script path (alias for entrypoint_command)")

    display_name: str | None = Field(None, max_length=256, description="Display name")
    description: str | None = Field(None, description="Job description")

    node_count: int = Field(default=1, ge=1, le=256, description="Number of nodes")
    tasks_per_node: int | None = Field(None, ge=1, description="Tasks per node")
    gpu_per_node: int | None = Field(None, ge=1, le=8, description="GPUs per node (alias for tasks_per_node)")

    environment_variables: dict | None = Field(None, description="Environment variables")
    hyperparameters: dict | None = Field(None, description="Hyperparameters")
    max_epochs: int | None = Field(None, ge=1, description="Max training epochs")
    batch_size: int | None = Field(None, ge=1, description="Batch size")
    learning_rate: float | None = Field(None, gt=0, description="Learning rate")

    distribution_strategy: DistributionStrategyEnum = Field(
        default=DistributionStrategyEnum.DDP,
        description="Distribution strategy",
    )
    priority: JobPriorityEnum = Field(
        default=JobPriorityEnum.MEDIUM,
        description="Job priority",
    )
    mixed_precision: bool = Field(default=False, description="Use mixed precision")
    use_spot_instances: bool = Field(default=False, description="Use spot instances")

    dataset_id: int | None = Field(None, description="Dataset ID")
    data_mount_path: str | None = Field(default="/data", description="Data mount path")
    checkpoint_mount_path: str | None = Field(default="/checkpoints", description="Checkpoint mount path")
    checkpoint_interval: int | None = Field(None, ge=1, description="Checkpoint interval")

    @field_validator("job_name")
    @classmethod
    def validate_job_name(cls, v: str) -> str:
        """Validate job name format: lowercase alphanumeric with hyphens."""
        pattern = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
        if not re.match(pattern, v):
            raise ValueError(
                "Job name must be lowercase alphanumeric with hyphens, " "start and end with alphanumeric characters"
            )
        return v

    @model_validator(mode="after")
    def normalize_aliases(self) -> Self:
        """归一化前端契约别名并校验必填组合。

        Raises:
            ValueError: entrypoint_command 与 entry_point 均未提供时。
        """
        if self.entrypoint_command is None:
            if self.entry_point is None:
                raise ValueError("Either entrypoint_command or entry_point is required")
            self.entrypoint_command = ["python", self.entry_point]
        if self.tasks_per_node is None:
            self.tasks_per_node = self.gpu_per_node if self.gpu_per_node is not None else 1
        return self


class CreateCheckpointRequest(BaseModel):
    """Request body for creating a manual checkpoint."""

    checkpoint_name: str | None = Field(None, max_length=256, description="Checkpoint name")


class UpdateTrainingJobRequest(BaseModel):
    """Request body for updating a training job.

    Only certain fields can be updated after job creation.
    """

    priority: JobPriorityEnum | None = Field(None, description="Job priority")
    description: str | None = Field(None, description="Job description")
    max_epochs: int | None = Field(None, ge=1, description="Max training epochs")
    checkpoint_interval: int | None = Field(None, ge=1, description="Checkpoint interval")


class TemplateVisibilityEnum(str, Enum):
    """Template visibility scope."""

    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class TrainingConfigSchema(BaseModel):
    """Training configuration for templates."""

    image: str = Field(..., description="Docker image URI")
    script_path: str | None = Field(None, description="Training script path")
    instance_type: str = Field(..., description="Instance type")
    instance_count: int = Field(default=1, ge=1, description="Number of instances")
    distribution_strategy: DistributionStrategyEnum = Field(
        default=DistributionStrategyEnum.DDP,
        description="Distribution strategy",
    )
    environment: dict[str, str] | None = Field(None, description="Environment variables")
    hyperparameters: dict | None = Field(None, description="Default hyperparameters")


class CreateJobTemplateRequest(BaseModel):
    """Request body for creating a job template."""

    name: str = Field(..., min_length=1, max_length=128, description="Template name")
    description: str | None = Field(None, description="Template description")
    visibility: TemplateVisibilityEnum = Field(
        default=TemplateVisibilityEnum.PRIVATE,
        description="Visibility scope",
    )
    training_config: TrainingConfigSchema = Field(..., description="Training configuration")


class UpdateJobTemplateRequest(BaseModel):
    """Request body for updating a job template."""

    name: str | None = Field(None, min_length=1, max_length=128, description="Template name")
    description: str | None = Field(None, description="Template description")
    visibility: TemplateVisibilityEnum | None = Field(None, description="Visibility scope")
    training_config: TrainingConfigSchema | None = Field(None, description="Training configuration")


class CreateJobFromTemplateRequest(BaseModel):
    """Request body for creating a training job from a template."""

    job_name: str = Field(..., min_length=1, max_length=128, description="Job name")
    display_name: str | None = Field(None, max_length=256, description="Display name")
    node_count: int | None = Field(None, ge=1, description="Override node count")
    priority: JobPriorityEnum | None = Field(None, description="Override priority")
    environment_variables: dict[str, str] | None = Field(None, description="Additional env vars")

    @field_validator("job_name")
    @classmethod
    def validate_job_name(cls, v: str) -> str:
        """Validate job name format: lowercase alphanumeric with hyphens."""
        pattern = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
        if not re.match(pattern, v):
            raise ValueError(
                "Job name must be lowercase alphanumeric with hyphens, " "start and end with alphanumeric characters"
            )
        return v
