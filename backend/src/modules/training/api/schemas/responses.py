"""训练模块 API 响应 Schema."""

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, ClassVar

from pydantic import BaseModel, PlainSerializer

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.training.domain.entities import Checkpoint, JobTemplate, TrainingJob  # noqa: F401

# OpenAPI 契约中 loss/cost 等为 number；Pydantic v2 默认把 Decimal 序列化为
# JSON 字符串，会破坏前端 number 类型契约（如 loss.toFixed 抛 TypeError）
ApiDecimal = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class JobStatusEnum(str, Enum):
    """任务状态."""

    SUBMITTED = "submitted"
    RUNNING = "running"
    PAUSED = "paused"
    PREEMPTED = "preempted"
    COMPLETED = "completed"
    FAILED = "failed"


class JobPriorityEnum(str, Enum):
    """任务优先级."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DistributionStrategyEnum(str, Enum):
    """分布式训练策略."""

    DDP = "ddp"
    FSDP = "fsdp"
    DEEPSPEED = "deepspeed"
    HOROVOD = "horovod"


class CheckpointTypeEnum(str, Enum):
    """检查点类型."""

    EPOCH = "epoch"
    STEP = "step"
    BEST = "best"
    FINAL = "final"
    MANUAL = "manual"


class CheckpointStatusEnum(str, Enum):
    """检查点状态."""

    AVAILABLE = "available"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StorageTierEnum(str, Enum):
    """存储层级."""

    NVME = "nvme"
    FSX = "fsx"
    S3 = "s3"


class TrainingJobSummary(EntitySchema["TrainingJob"]):
    """训练任务列表摘要.

    枚举映射由 EntitySchema 自动从字段类型推断。
    gpu_per_node/total_epochs 是 tasks_per_node/max_epochs 的 API 别名（前端契约）。
    """

    id: int
    job_name: str
    display_name: str | None = None
    status: JobStatusEnum
    priority: JobPriorityEnum
    instance_type: str
    node_count: int
    gpu_per_node: int = 1
    distribution_strategy: DistributionStrategyEnum | None = None
    current_epoch: int | None = None
    total_epochs: int | None = None
    latest_loss: ApiDecimal | None = None
    preemption_count: int = 0
    created_at: datetime
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None
    estimated_cost_usd: ApiDecimal | None = None

    _custom_mappings: ClassVar[dict[str, Callable[[Any], Any]]] = {
        "gpu_per_node": lambda e: e.tasks_per_node,
        "total_epochs": lambda e: e.max_epochs,
    }


class TrainingJobDetail(TrainingJobSummary):
    """训练任务详情 - 继承 TrainingJobSummary 扩展更多字段.

    自动继承父类枚举映射，新增枚举字段自动推断。
    entry_point 为 entrypoint_command 的展示形式（前端契约）。
    """

    description: str | None = None
    owner_id: int
    image_uri: str
    tasks_per_node: int
    entry_point: str | None = None
    entrypoint_command: list[str] = []
    environment_variables: dict | None = None
    dataset_id: int | None = None
    data_mount_path: str | None = None
    checkpoint_mount_path: str | None = None
    hyperparameters: dict | None = None
    max_epochs: int | None = None
    batch_size: int | None = None
    learning_rate: float | None = None
    mixed_precision: bool
    use_spot_instances: bool
    total_pods: int | None = None
    running_pods: int = 0
    failed_pods: int = 0
    current_step: int | None = None
    latest_accuracy: ApiDecimal | None = None
    duration_seconds: int | None = None
    total_gpu_hours: ApiDecimal | None = None
    estimated_cost_usd: ApiDecimal | None = None
    hyperpod_job_arn: str | None = None  # 仅管理员可见
    hyperpod_status: str | None = None
    kueue_status: str | None = None
    kueue_workload_name: str | None = None
    error_message: str | None = None
    failure_reason: str | None = None
    checkpoints_count: int = 0
    updated_at: datetime | None = None

    _custom_mappings: ClassVar[dict[str, Callable[[Any], Any]]] = {
        "gpu_per_node": lambda e: e.tasks_per_node,
        "total_epochs": lambda e: e.max_epochs,
        "entry_point": lambda e: " ".join(e.entrypoint_command) if e.entrypoint_command else None,
    }


class TrainingJobListResponse(BaseModel):
    """训练任务分页列表响应."""

    items: list[TrainingJobSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class CheckpointListResponse(BaseModel):
    """检查点列表响应.

    items 与 checkpoints 内容相同：items 对齐前端分页约定，checkpoints 对齐 OpenAPI 契约。
    """

    items: list["CheckpointResponse"]
    checkpoints: list["CheckpointResponse"]
    total: int


class CheckpointResponse(EntitySchema["Checkpoint"]):
    """检查点响应.

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
    loss: ApiDecimal | None = None
    accuracy: ApiDecimal | None = None
    storage_tier: StorageTierEnum
    status: CheckpointStatusEnum
    metadata: dict | None = None
    created_at: datetime


# === 任务模板响应 Schema ===


class TemplateVisibilityEnum(str, Enum):
    """模板可见性范围."""

    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class JobTemplateSummary(EntitySchema["JobTemplate"]):
    """任务模板列表摘要.

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
    """任务模板详情."""

    training_config: dict
    last_used_at: datetime | None = None
    updated_at: datetime


class JobTemplateListResponse(BaseModel):
    """任务模板分页列表响应."""

    items: list[JobTemplateSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# === 日志 Schema ===


class LogEntry(BaseModel):
    """单条日志条目."""

    timestamp: datetime
    pod_name: str | None = None
    message: str


class TrainingLogsResponse(BaseModel):
    """训练任务日志响应."""

    logs: list[LogEntry]
    next_token: str | None = None


# === Kueue 调试 Schema ===


class KueueCondition(BaseModel):
    """Kueue Workload 条件."""

    type: str
    status: str
    last_transition_time: datetime | None = None
    reason: str | None = None
    message: str | None = None


class PodSetAssignment(BaseModel):
    """Pod 集合资源分配."""

    name: str
    flavors: dict[str, str] | None = None
    resource_usage: dict[str, str] | None = None
    count: int | None = None


class KueueAdmission(BaseModel):
    """Kueue 准入信息."""

    cluster_queue: str
    pod_set_assignments: list[PodSetAssignment] | None = None


class KueueWorkloadStatus(BaseModel):
    """Kueue Workload 状态."""

    admitted: bool = False
    quota_reserved: bool = False
    pods_ready: bool = False
    evicted: bool = False
    finished: bool = False


class ResourceUsage(BaseModel):
    """资源使用量."""

    used: str
    total: str


class KueueQuotaUsage(BaseModel):
    """Kueue 配额使用量."""

    cpu: ResourceUsage | None = None
    memory: ResourceUsage | None = None
    gpu: ResourceUsage | None = None


class QueueInfo(BaseModel):
    """队列信息."""

    local_queue: str | None = None
    cluster_queue: str | None = None
    queue_position: int | None = None


class PreemptionEvent(BaseModel):
    """抢占历史事件."""

    preempted_at: datetime
    preempting_workload: str | None = None
    reason: str | None = None


class KueueDebugResponse(BaseModel):
    """Kueue Workload 调试信息."""

    workload_name: str
    namespace: str
    status: KueueWorkloadStatus
    admission: KueueAdmission | None = None
    conditions: list[KueueCondition] | None = None
    queue_info: QueueInfo | None = None
    quota_usage: KueueQuotaUsage | None = None
    preemption_history: list[PreemptionEvent] | None = None
    raw_yaml: str | None = None  # 仅管理员可见


# === 训练指标 Schema (T220) ===


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
