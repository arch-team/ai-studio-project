"""Training Job API Schemas - Pydantic models for request/response."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from src.api.v1.schemas.base import EntitySchema
from src.api.v1.schemas.common import ErrorResponse
from src.core.mapping import EnumMapper

if TYPE_CHECKING:
    from src.domain.entities.training_job import TrainingJob

# === Enums ===


class JobStatusEnum(str, Enum):
    """Training job status."""

    SUBMITTED = "submitted"
    RUNNING = "running"
    PAUSED = "paused"
    PREEMPTED = "preempted"
    COMPLETED = "completed"
    FAILED = "failed"


class JobPriorityEnum(str, Enum):
    """Job priority for Kueue scheduling."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DistributionStrategyEnum(str, Enum):
    """Distributed training strategy."""

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


class StorageTierEnum(str, Enum):
    """Checkpoint storage tier."""

    NVME = "nvme"
    FSX = "fsx"
    S3 = "s3"


class CheckpointStatusEnum(str, Enum):
    """Checkpoint status."""

    AVAILABLE = "available"
    ARCHIVED = "archived"
    DELETED = "deleted"


# === Request Schemas ===


class CreateTrainingJobRequest(BaseModel):
    """Request body for creating a training job."""

    job_name: str = Field(
        ...,
        min_length=3,
        max_length=128,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="Unique job name (lowercase alphanumeric with hyphens)",
    )
    display_name: str | None = Field(
        None, max_length=256, description="Human-readable display name"
    )
    description: str | None = Field(
        None, max_length=2000, description="Job description"
    )
    image_uri: str = Field(..., description="Docker image URI")
    instance_type: str = Field(
        ..., description="EC2 instance type (e.g., ml.p4d.24xlarge)"
    )
    node_count: int = Field(..., ge=1, le=256, description="Number of training nodes")
    tasks_per_node: int = Field(
        default=1, ge=1, le=8, description="Tasks (GPUs) per node"
    )
    entrypoint_command: list[str] = Field(
        ..., min_length=1, description="Command to execute"
    )
    environment_variables: dict[str, str] | None = Field(
        None, description="Environment variables"
    )
    dataset_id: int | None = Field(None, description="Associated dataset ID")
    data_mount_path: str = Field(default="/data", description="Data mount path")
    checkpoint_mount_path: str = Field(
        default="/checkpoints", description="Checkpoint mount path"
    )
    checkpoint_interval: int | None = Field(
        None, ge=1, description="Checkpoint interval (epochs)"
    )
    hyperparameters: dict | None = Field(None, description="Training hyperparameters")
    max_epochs: int | None = Field(None, ge=1, description="Maximum epochs")
    batch_size: int | None = Field(None, ge=1, description="Batch size")
    learning_rate: float | None = Field(None, ge=0, description="Learning rate")
    distribution_strategy: DistributionStrategyEnum = Field(
        default=DistributionStrategyEnum.DDP, description="Distribution strategy"
    )
    priority: JobPriorityEnum = Field(
        default=JobPriorityEnum.MEDIUM, description="Job priority"
    )
    mixed_precision: bool = Field(
        default=False, description="Use mixed precision (AMP)"
    )
    use_spot_instances: bool = Field(default=False, description="Use spot instances")


# === Response Schemas ===


class TrainingJobSummary(EntitySchema["TrainingJob"]):
    """Training job summary for list responses."""

    id: int
    job_name: str
    display_name: str | None = None
    owner_id: int
    owner_username: str | None = None
    status: JobStatusEnum
    priority: JobPriorityEnum
    instance_type: str
    node_count: int
    current_epoch: int | None = None
    latest_loss: Decimal | None = None
    checkpoints_count: int = 0
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None
    estimated_cost_usd: Decimal | None = None

    @classmethod
    def _map_entity_fields(cls, entity: "TrainingJob") -> dict:
        """Map TrainingJob entity to summary schema fields."""
        return {
            "id": entity.id,
            "job_name": entity.job_name,
            "display_name": entity.display_name,
            "owner_id": entity.owner_id,
            "status": EnumMapper.to_api(entity.status, JobStatusEnum),
            "priority": EnumMapper.to_api(entity.priority, JobPriorityEnum),
            "instance_type": entity.instance_type,
            "node_count": entity.node_count,
            "current_epoch": entity.current_epoch,
            "latest_loss": entity.latest_loss,
            "submitted_at": entity.submitted_at,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
            "duration_seconds": entity.duration_seconds,
            "estimated_cost_usd": entity.estimated_cost_usd,
        }


class TrainingJobDetail(EntitySchema["TrainingJob"]):
    """Training job detail response."""

    # Basic info
    id: int
    job_name: str
    display_name: str | None = None
    description: str | None = None
    owner_id: int
    owner_username: str | None = None

    # Status info
    status: JobStatusEnum
    hyperpod_status: str | None = None
    kueue_workload_name: str | None = None
    kueue_status: str | None = None

    # Compute config
    image_uri: str
    instance_type: str
    node_count: int
    tasks_per_node: int = 1
    entrypoint_command: list[str]

    # Environment
    environment_variables: dict[str, str] | None = None
    dataset_id: int | None = None
    dataset_name: str | None = None
    data_mount_path: str | None = None
    checkpoint_mount_path: str | None = None

    # Training config
    hyperparameters: dict | None = None
    max_epochs: int | None = None
    batch_size: int | None = None
    learning_rate: Decimal | None = None
    distribution_strategy: DistributionStrategyEnum
    priority: JobPriorityEnum
    mixed_precision: bool = False
    use_spot_instances: bool = False

    # Pod stats
    total_pods: int | None = None
    running_pods: int = 0
    failed_pods: int = 0
    preemption_count: int = 0

    # Training progress
    current_epoch: int | None = None
    current_step: int | None = None
    latest_loss: Decimal | None = None
    latest_accuracy: Decimal | None = None

    # Time stats
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None
    total_gpu_hours: Decimal | None = None

    # Cost
    estimated_cost_usd: Decimal | None = None

    # Error info
    error_message: str | None = None
    failure_reason: str | None = None

    # Admin-only field
    hyperpod_job_arn: str | None = None

    # Metadata
    checkpoints_count: int = 0
    created_at: datetime
    updated_at: datetime

    @classmethod
    def _map_entity_fields(cls, entity: "TrainingJob") -> dict:
        """Map TrainingJob entity to detail schema fields."""
        return {
            "id": entity.id,
            "job_name": entity.job_name,
            "display_name": entity.display_name,
            "description": entity.description,
            "owner_id": entity.owner_id,
            "status": EnumMapper.to_api(entity.status, JobStatusEnum),
            "hyperpod_status": entity.hyperpod_status,
            "kueue_workload_name": entity.kueue_workload_name,
            "kueue_status": entity.kueue_status,
            "image_uri": entity.image_uri,
            "instance_type": entity.instance_type,
            "node_count": entity.node_count,
            "tasks_per_node": entity.tasks_per_node,
            "entrypoint_command": entity.entrypoint_command,
            "environment_variables": entity.environment_variables,
            "dataset_id": entity.dataset_id,
            "data_mount_path": entity.data_mount_path,
            "checkpoint_mount_path": entity.checkpoint_mount_path,
            "hyperparameters": entity.hyperparameters,
            "max_epochs": entity.max_epochs,
            "batch_size": entity.batch_size,
            "learning_rate": entity.learning_rate,
            "distribution_strategy": EnumMapper.to_api(
                entity.distribution_strategy, DistributionStrategyEnum
            ),
            "priority": EnumMapper.to_api(entity.priority, JobPriorityEnum),
            "mixed_precision": entity.mixed_precision,
            "use_spot_instances": entity.use_spot_instances,
            "total_pods": entity.total_pods,
            "running_pods": entity.running_pods,
            "failed_pods": entity.failed_pods,
            "preemption_count": entity.preemption_count,
            "current_epoch": entity.current_epoch,
            "current_step": entity.current_step,
            "latest_loss": entity.latest_loss,
            "latest_accuracy": entity.latest_accuracy,
            "submitted_at": entity.submitted_at,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
            "duration_seconds": entity.duration_seconds,
            "total_gpu_hours": entity.total_gpu_hours,
            "estimated_cost_usd": entity.estimated_cost_usd,
            "error_message": entity.error_message,
            "failure_reason": entity.failure_reason,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }


class TrainingJobListResponse(BaseModel):
    """Paginated list of training jobs."""

    items: list[TrainingJobSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# === Checkpoint Schemas ===


class CheckpointResponse(BaseModel):
    """Checkpoint response."""

    id: int
    training_job_id: int
    checkpoint_name: str
    storage_path: str
    checkpoint_type: CheckpointTypeEnum
    epoch: int | None = None
    step: int | None = None
    size_bytes: int | None = None
    loss: Decimal | None = None
    accuracy: Decimal | None = None
    storage_tier: StorageTierEnum
    status: CheckpointStatusEnum
    metadata: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CheckpointListResponse(BaseModel):
    """List of checkpoints."""

    checkpoints: list[CheckpointResponse]


class CreateCheckpointRequest(BaseModel):
    """Request to create a manual checkpoint."""

    checkpoint_name: str | None = Field(
        None, max_length=256, description="Optional checkpoint name"
    )


# === Log Schemas ===


class LogEntry(BaseModel):
    """Single log entry."""

    timestamp: datetime
    pod_name: str
    message: str


class TrainingLogsResponse(BaseModel):
    """Training logs response."""

    logs: list[LogEntry]
    next_token: str | None = None


# === Metrics Schemas ===


class MetricDataPoint(BaseModel):
    """Single metric data point."""

    timestamp: datetime
    value: float
    labels: dict[str, str] | None = None


class MetricSeries(BaseModel):
    """Metric time series."""

    metric_name: str
    data_points: list[MetricDataPoint]


class TrainingMetricsResponse(BaseModel):
    """Training metrics response."""

    metrics: list[MetricSeries]


# === Kueue Debug Schemas ===


class KueueCondition(BaseModel):
    """Kueue workload condition."""

    type: str
    status: str
    last_transition_time: datetime | None = None
    reason: str | None = None
    message: str | None = None


class KueueStatus(BaseModel):
    """Kueue workload status."""

    admitted: bool = False
    quota_reserved: bool = False
    pods_ready: bool = False
    evicted: bool = False
    finished: bool = False


class PodSetAssignment(BaseModel):
    """Kueue pod set assignment."""

    name: str
    flavors: dict[str, str] | None = None
    resource_usage: dict[str, str] | None = None
    count: int = 0


class KueueAdmission(BaseModel):
    """Kueue admission info."""

    cluster_queue: str | None = None
    pod_set_assignments: list[PodSetAssignment] = []


class KueueQueueInfo(BaseModel):
    """Kueue queue info."""

    local_queue: str | None = None
    cluster_queue: str | None = None
    queue_position: int | None = None


class ResourceUsage(BaseModel):
    """Resource usage info."""

    used: str
    total: str


class KueueQuotaUsage(BaseModel):
    """Kueue quota usage."""

    cpu: ResourceUsage | None = None
    memory: ResourceUsage | None = None
    gpu: dict[str, int] | None = None


class PreemptionEvent(BaseModel):
    """Preemption history event."""

    preempted_at: datetime
    preempting_workload: str | None = None
    reason: str | None = None


class KueueDebugResponse(BaseModel):
    """Kueue workload debug info."""

    workload_name: str | None = None
    namespace: str | None = None
    status: KueueStatus
    admission: KueueAdmission | None = None
    conditions: list[KueueCondition] = []
    queue_info: KueueQueueInfo | None = None
    quota_usage: KueueQuotaUsage | None = None
    preemption_history: list[PreemptionEvent] = []
    raw_yaml: str | None = None  # Admin only


# === Error Schemas ===
# ErrorResponse is imported from common.py


class QuotaExceededErrorResponse(BaseModel):
    """Quota exceeded error response."""

    code: str = "QUOTA_EXCEEDED"
    message: str
    quota_type: str
    requested: int
    available: int
