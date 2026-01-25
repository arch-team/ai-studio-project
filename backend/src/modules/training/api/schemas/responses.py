"""Training API response schemas."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel

from src.shared.api.schemas import AutoMappingEntitySchema


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


class TrainingJobSummary(AutoMappingEntitySchema["TrainingJob"]):
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
    preemption_count: int = 0
    created_at: datetime
    started_at: datetime | None = None

    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
        "status": JobStatusEnum,
        "priority": JobPriorityEnum,
    }


class TrainingJobDetail(TrainingJobSummary):
    """Training job detailed view - 继承 TrainingJobSummary 扩展更多字段."""

    description: str | None = None
    owner_id: int
    image_uri: str
    tasks_per_node: int
    distribution_strategy: DistributionStrategyEnum
    mixed_precision: bool
    use_spot_instances: bool
    current_step: int | None = None
    latest_accuracy: Decimal | None = None
    total_gpu_hours: Decimal | None = None
    estimated_cost_usd: Decimal | None = None
    kueue_status: str | None = None
    kueue_workload_name: str | None = None
    error_message: str | None = None
    completed_at: datetime | None = None

    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
        **TrainingJobSummary._enum_mappings,
        "distribution_strategy": DistributionStrategyEnum,
    }


class TrainingJobListResponse(BaseModel):
    """Paginated list of training jobs."""

    items: list[TrainingJobSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class CheckpointResponse(AutoMappingEntitySchema["Checkpoint"]):
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

    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
        "checkpoint_type": CheckpointTypeEnum,
        "storage_tier": StorageTierEnum,
        "status": CheckpointStatusEnum,
    }


# === Job Template Response Schemas ===


class TemplateVisibilityEnum(str, Enum):
    """Template visibility scope."""

    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class JobTemplateSummary(AutoMappingEntitySchema["JobTemplate"]):
    """Job template summary for list view."""

    id: int
    name: str
    description: str | None = None
    visibility: TemplateVisibilityEnum
    usage_count: int
    owner_id: int
    created_at: datetime

    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
        "visibility": TemplateVisibilityEnum,
    }


class JobTemplateDetail(JobTemplateSummary):
    """Job template detailed view."""

    training_config: dict
    last_used_at: datetime | None = None
    updated_at: datetime


class JobTemplateListResponse(BaseModel):
    """Paginated list of job templates."""

    items: list[JobTemplateSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
