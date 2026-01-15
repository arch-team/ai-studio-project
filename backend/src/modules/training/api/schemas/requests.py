"""Training API request schemas."""

from enum import Enum

from pydantic import BaseModel, Field


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
    """Request body for creating a training job."""

    job_name: str = Field(..., min_length=1, max_length=128, description="Job name")
    image_uri: str = Field(..., description="Docker image URI")
    instance_type: str = Field(..., description="Instance type (e.g., ml.p4d.24xlarge)")
    entrypoint_command: list[str] = Field(..., description="Entrypoint command")

    display_name: str | None = Field(None, max_length=256, description="Display name")
    description: str | None = Field(None, description="Job description")

    node_count: int = Field(default=1, ge=1, le=256, description="Number of nodes")
    tasks_per_node: int = Field(default=1, ge=1, description="Tasks per node")

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
    checkpoint_mount_path: str | None = Field(
        default="/checkpoints", description="Checkpoint mount path"
    )
    checkpoint_interval: int | None = Field(None, ge=1, description="Checkpoint interval")


class CreateCheckpointRequest(BaseModel):
    """Request body for creating a manual checkpoint."""

    checkpoint_name: str | None = Field(None, max_length=256, description="Checkpoint name")
