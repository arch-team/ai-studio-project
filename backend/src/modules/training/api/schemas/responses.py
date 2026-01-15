"""Training API response schemas."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.training.domain.entities import Checkpoint, TrainingJob


class JobStatusEnum(str, Enum):
    """Job status."""

    SUBMITTED = "submitted"
    RUNNING = "running"
    PAUSED = "paused"
    PREEMPTED = "preempted"
    COMPLETED = "completed"
    FAILED = "failed"


class JobPriorityEnum(str, Enum):
    """Job priority."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DistributionStrategyEnum(str, Enum):
    """Distribution strategy."""

    DDP = "ddp"
    FSDP = "fsdp"
    DEEPSPEED = "deepspeed"
    HOROVOD = "horovod"


class CheckpointTypeEnum(str, Enum):
    """Checkpoint type."""

    EPOCH = "epoch"
    STEP = "step"
    BEST = "best"
    FINAL = "final"
    MANUAL = "manual"


class CheckpointStatusEnum(str, Enum):
    """Checkpoint status."""

    AVAILABLE = "available"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StorageTierEnum(str, Enum):
    """Storage tier."""

    NVME = "nvme"
    FSX = "fsx"
    S3 = "s3"


class TrainingJobSummary(EntitySchema["TrainingJob"]):
    """Training job summary for list view."""

    id: int
    job_name: str
    display_name: str | None = None
    status: JobStatusEnum
    priority: JobPriorityEnum
    instance_type: str
    node_count: int
    current_epoch: int | None = None
    latest_loss: Decimal | None = None
    created_at: datetime
    started_at: datetime | None = None

    @classmethod
    def _map_entity_fields(cls, entity: "TrainingJob") -> dict:
        return {
            "id": entity.id,
            "job_name": entity.job_name,
            "display_name": entity.display_name,
            "status": JobStatusEnum(entity.status.value.lower()),
            "priority": JobPriorityEnum(entity.priority.value.lower()),
            "instance_type": entity.instance_type,
            "node_count": entity.node_count,
            "current_epoch": entity.current_epoch,
            "latest_loss": entity.latest_loss,
            "created_at": entity.created_at,
            "started_at": entity.started_at,
        }


class TrainingJobDetail(EntitySchema["TrainingJob"]):
    """Training job detailed view."""

    id: int
    job_name: str
    display_name: str | None = None
    description: str | None = None
    owner_id: int
    status: JobStatusEnum
    priority: JobPriorityEnum
    image_uri: str
    instance_type: str
    node_count: int
    tasks_per_node: int
    distribution_strategy: DistributionStrategyEnum
    mixed_precision: bool
    use_spot_instances: bool
    current_epoch: int | None = None
    current_step: int | None = None
    latest_loss: Decimal | None = None
    latest_accuracy: Decimal | None = None
    total_gpu_hours: Decimal | None = None
    estimated_cost_usd: Decimal | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def _map_entity_fields(cls, entity: "TrainingJob") -> dict:
        return {
            "id": entity.id,
            "job_name": entity.job_name,
            "display_name": entity.display_name,
            "description": entity.description,
            "owner_id": entity.owner_id,
            "status": JobStatusEnum(entity.status.value.lower()),
            "priority": JobPriorityEnum(entity.priority.value.lower()),
            "image_uri": entity.image_uri,
            "instance_type": entity.instance_type,
            "node_count": entity.node_count,
            "tasks_per_node": entity.tasks_per_node,
            "distribution_strategy": DistributionStrategyEnum(entity.distribution_strategy.value.lower()),
            "mixed_precision": entity.mixed_precision,
            "use_spot_instances": entity.use_spot_instances,
            "current_epoch": entity.current_epoch,
            "current_step": entity.current_step,
            "latest_loss": entity.latest_loss,
            "latest_accuracy": entity.latest_accuracy,
            "total_gpu_hours": entity.total_gpu_hours,
            "estimated_cost_usd": entity.estimated_cost_usd,
            "error_message": entity.error_message,
            "created_at": entity.created_at,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
        }


class TrainingJobListResponse(BaseModel):
    """Paginated list of training jobs."""

    items: list[TrainingJobSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class CheckpointResponse(BaseModel):
    """Checkpoint response."""

    id: int
    training_job_id: int
    checkpoint_name: str
    storage_path: str
    checkpoint_type: CheckpointTypeEnum
    epoch: int | None = None
    step: int | None = None
    size_bytes: int
    loss: Decimal | None = None
    accuracy: Decimal | None = None
    storage_tier: StorageTierEnum
    status: CheckpointStatusEnum
    metadata: dict | None = None
    created_at: datetime
