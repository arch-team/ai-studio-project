"""Training API response schemas."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.training.domain.entities import Checkpoint, JobTemplate, TrainingJob  # noqa: F401


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
    """Training job summary for list view.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

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


class TrainingJobDetail(TrainingJobSummary):
    """Training job detailed view - 继承 TrainingJobSummary 扩展更多字段.

    自动继承父类枚举映射，新增枚举字段自动推断。
    """

    description: str | None = None
    owner_id: int
    image_uri: str
    tasks_per_node: int
    distribution_strategy: DistributionStrategyEnum
    mixed_precision: bool
    use_spot_instances: bool
    current_step: int | None = None
    latest_accuracy: Decimal | None = None
    duration_seconds: int | None = None
    total_gpu_hours: Decimal | None = None
    estimated_cost_usd: Decimal | None = None
    hyperpod_job_arn: str | None = None  # Only visible to admin
    kueue_status: str | None = None
    kueue_workload_name: str | None = None
    error_message: str | None = None
    completed_at: datetime | None = None


class TrainingJobListResponse(BaseModel):
    """Paginated list of training jobs."""

    items: list[TrainingJobSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class CheckpointResponse(EntitySchema["Checkpoint"]):
    """Checkpoint response.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

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


# === Job Template Response Schemas ===


class TemplateVisibilityEnum(str, Enum):
    """Template visibility scope."""

    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class JobTemplateSummary(EntitySchema["JobTemplate"]):
    """Job template summary for list view.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

    id: int
    name: str
    description: str | None = None
    visibility: TemplateVisibilityEnum
    usage_count: int
    owner_id: int
    created_at: datetime


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


# === Log Schemas ===


class LogEntry(BaseModel):
    """Single log entry."""

    timestamp: datetime
    pod_name: str | None = None
    message: str


class TrainingLogsResponse(BaseModel):
    """Training job logs response."""

    logs: list[LogEntry]
    next_token: str | None = None


# === Kueue Debug Schemas ===


class KueueCondition(BaseModel):
    """Kueue Workload condition."""

    type: str
    status: str
    last_transition_time: datetime | None = None
    reason: str | None = None
    message: str | None = None


class PodSetAssignment(BaseModel):
    """Pod set resource assignment."""

    name: str
    flavors: dict[str, str] | None = None
    resource_usage: dict[str, str] | None = None
    count: int | None = None


class KueueAdmission(BaseModel):
    """Kueue admission info."""

    cluster_queue: str
    pod_set_assignments: list[PodSetAssignment] | None = None


class KueueWorkloadStatus(BaseModel):
    """Kueue workload status."""

    admitted: bool = False
    quota_reserved: bool = False
    pods_ready: bool = False
    evicted: bool = False
    finished: bool = False


class ResourceUsage(BaseModel):
    """Resource usage info."""

    used: str
    total: str


class KueueQuotaUsage(BaseModel):
    """Kueue quota usage info."""

    cpu: ResourceUsage | None = None
    memory: ResourceUsage | None = None
    gpu: ResourceUsage | None = None


class QueueInfo(BaseModel):
    """Queue information."""

    local_queue: str | None = None
    cluster_queue: str | None = None
    queue_position: int | None = None


class PreemptionEvent(BaseModel):
    """Preemption history event."""

    preempted_at: datetime
    preempting_workload: str | None = None
    reason: str | None = None


class KueueDebugResponse(BaseModel):
    """Kueue Workload debug information."""

    workload_name: str
    namespace: str
    status: KueueWorkloadStatus
    admission: KueueAdmission | None = None
    conditions: list[KueueCondition] | None = None
    queue_info: QueueInfo | None = None
    quota_usage: KueueQuotaUsage | None = None
    preemption_history: list[PreemptionEvent] | None = None
    raw_yaml: str | None = None  # Only visible to admin


# === Training Metrics Schemas (T220) ===


class MetricDataPoint(BaseModel):
    """单个指标数据点."""

    timestamp: datetime
    value: float


class TrainingMetricsResponse(BaseModel):
    """训练指标查询响应 (FR-026)."""

    job_id: int
    metrics: dict[str, list[MetricDataPoint]]


class JobMetricsData(BaseModel):
    """单个任务的指标数据 (用于对比)."""

    job_id: int
    metric_type: str
    data_points: list[MetricDataPoint]


class JobMetricsComparisonResponse(BaseModel):
    """多任务指标对比响应."""

    metric_type: str
    jobs: list[JobMetricsData]
