"""Training domain exceptions.

使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段。
"""

from dataclasses import dataclass, field

from src.shared.domain.problem import Problem, problem

# =============================================================================
# 训练任务异常
# =============================================================================


@problem(404, "TRAINING_JOB_NOT_FOUND", "TrainingJob '{job_id}' not found")
@dataclass
class TrainingJobNotFoundError(Problem):
    """训练任务未找到."""

    job_id: str


@problem(404, "CHECKPOINT_NOT_FOUND", "Checkpoint '{checkpoint_id}' not found")
@dataclass
class CheckpointNotFoundError(Problem):
    """检查点未找到."""

    checkpoint_id: str


@problem(409, "DUPLICATE_JOB_NAME", "Training job with name '{job_name}' already exists")
@dataclass
class DuplicateJobNameError(Problem):
    """任务名称重复."""

    job_name: str


@problem(
    400,
    "NO_VALID_CHECKPOINT",
    "Cannot resume job {job_id}: no valid checkpoint available for recovery",
)
@dataclass
class NoValidCheckpointError(Problem):
    """无有效检查点可恢复."""

    job_id: int


@problem(409, "INVALID_JOB_STATE", "Cannot {operation} job {job_id} in state '{current_state}'")
@dataclass
class InvalidJobStateError(Problem):
    """任务状态无效."""

    job_id: int
    current_state: str
    operation: str


@problem(500, "CHECKPOINT_STORAGE_ERROR")
@dataclass
class CheckpointStorageError(Problem):
    """检查点存储失败."""

    message: str = field(default="Checkpoint storage operation failed")
    job_id: int | None = None


@problem(
    500,
    "CHECKPOINT_MIGRATION_ERROR",
    "Failed to migrate checkpoint {checkpoint_id} from {source_tier} to {target_tier}: {reason}",
)
@dataclass
class CheckpointMigrationError(Problem):
    """检查点迁移失败."""

    checkpoint_id: int
    source_tier: str
    target_tier: str
    reason: str


@problem(404, "JOB_TEMPLATE_NOT_FOUND", "JobTemplate '{template_id}' not found")
@dataclass
class JobTemplateNotFoundError(Problem):
    """任务模板未找到."""

    template_id: int


@problem(
    403,
    "JOB_TEMPLATE_PERMISSION_DENIED",
    "Permission denied: cannot {operation} template {template_id}",
)
@dataclass
class JobTemplatePermissionDeniedError(Problem):
    """模板权限拒绝."""

    operation: str
    template_id: int


# =============================================================================
# HyperPod 相关异常
# =============================================================================


@problem(
    503,
    "HYPERPOD_SDK_UNAVAILABLE",
    "HyperPod SDK component '{component}' is not available. Please install sagemaker-hyperpod package.",
)
@dataclass
class HyperPodSDKUnavailableError(Problem):
    """HyperPod SDK 不可用."""

    component: str = "HyperPodPytorchJob"


@problem(404, "HYPERPOD_POD_NOT_FOUND", "Pod '{pod_name}' not found in job '{job_name}'")
@dataclass
class HyperPodPodNotFoundError(Problem):
    """HyperPod Pod 未找到."""

    job_name: str
    pod_name: str


@problem(500, "HYPERPOD_OPERATION_ERROR")
@dataclass
class HyperPodOperationError(Problem):
    """HyperPod 操作失败."""

    operation: str
    reason: str
    job_name: str | None = None

    def __post_init__(self) -> None:
        """根据 job_name 生成消息."""
        if self.job_name:
            self.message = f"HyperPod operation '{self.operation}' on job '{self.job_name}' " f"failed: {self.reason}"
        else:
            self.message = f"HyperPod operation '{self.operation}' failed: {self.reason}"
        super().__post_init__()


# =============================================================================
# 向后兼容别名 (deprecated)
# =============================================================================

# TrainingError 作为 Problem 的别名
TrainingError = Problem
"""[DEPRECATED] 使用 Problem 替代."""
