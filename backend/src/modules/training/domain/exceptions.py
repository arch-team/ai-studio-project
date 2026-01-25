"""Training domain exceptions.

设计说明:
---------
每个异常类包含以下类属性：
- http_status: 对应的 HTTP 状态码
- error_code: 错误代码，供前端程序化处理

异常处理器会自动读取这些属性，无需维护映射表。
"""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class TrainingError(DomainError):
    """Base exception for training-related errors."""

    error_code = "TRAINING_ERROR"


class TrainingJobNotFoundError(EntityNotFoundError):
    """Raised when a training job is not found."""

    error_code = "TRAINING_JOB_NOT_FOUND"

    def __init__(self, identifier: str):
        super().__init__("TrainingJob", identifier)
        self.identifier = identifier


class CheckpointNotFoundError(EntityNotFoundError):
    """Raised when a checkpoint is not found."""

    error_code = "CHECKPOINT_NOT_FOUND"

    def __init__(self, identifier: str):
        super().__init__("Checkpoint", identifier)
        self.identifier = identifier


class DuplicateJobNameError(TrainingError):
    """Raised when a job with the same name already exists."""

    http_status = 409
    error_code = "DUPLICATE_JOB_NAME"

    def __init__(self, job_name: str):
        super().__init__(f"Training job with name '{job_name}' already exists")
        self.job_name = job_name


class InvalidJobStateError(TrainingError):
    """Raised when job is in an invalid state for the requested operation."""

    http_status = 409
    error_code = "INVALID_JOB_STATE"

    def __init__(self, job_id: int, current_state: str, operation: str):
        super().__init__(
            f"Cannot {operation} job {job_id} in state {current_state}"
        )
        self.job_id = job_id
        self.current_state = current_state
        self.operation = operation


class CheckpointStorageError(TrainingError):
    """Raised when checkpoint storage operation fails."""

    http_status = 500
    error_code = "CHECKPOINT_STORAGE_ERROR"

    def __init__(self, message: str, job_id: int | None = None):
        super().__init__(message)
        self.job_id = job_id


class CheckpointMigrationError(TrainingError):
    """Raised when checkpoint migration fails."""

    http_status = 500
    error_code = "CHECKPOINT_MIGRATION_ERROR"

    def __init__(self, checkpoint_id: int, source_tier: str, target_tier: str, reason: str):
        super().__init__(
            f"Failed to migrate checkpoint {checkpoint_id} from {source_tier} to {target_tier}: {reason}"
        )
        self.checkpoint_id = checkpoint_id
        self.source_tier = source_tier
        self.target_tier = target_tier
        self.reason = reason


class JobTemplateNotFoundError(EntityNotFoundError):
    """Raised when a job template is not found."""

    error_code = "JOB_TEMPLATE_NOT_FOUND"

    def __init__(self, identifier: int):
        super().__init__("JobTemplate", str(identifier))
        self.identifier = identifier


class JobTemplatePermissionDeniedError(TrainingError):
    """Raised when user doesn't have permission for the template operation."""

    http_status = 403
    error_code = "JOB_TEMPLATE_PERMISSION_DENIED"

    def __init__(self, operation: str, template_id: int):
        super().__init__(
            f"Permission denied: cannot {operation} template {template_id}"
        )
        self.operation = operation
        self.template_id = template_id


# =============================================================================
# HyperPod Client Exceptions
# =============================================================================


class HyperPodSDKUnavailableError(TrainingError):
    """HyperPod SDK 不可用（未安装或导入失败）"""

    http_status = 503
    error_code = "HYPERPOD_SDK_UNAVAILABLE"

    def __init__(self, component: str = "HyperPodPytorchJob"):
        super().__init__(
            f"HyperPod SDK component '{component}' is not available. "
            "Please install sagemaker-hyperpod package."
        )
        self.component = component


class HyperPodPodNotFoundError(TrainingError):
    """HyperPod Pod 不存在"""

    http_status = 404
    error_code = "HYPERPOD_POD_NOT_FOUND"

    def __init__(self, job_name: str, pod_name: str):
        super().__init__(f"Pod '{pod_name}' not found in job '{job_name}'")
        self.job_name = job_name
        self.pod_name = pod_name


class HyperPodOperationError(TrainingError):
    """HyperPod 操作失败（参数错误、状态不匹配等）"""

    http_status = 500
    error_code = "HYPERPOD_OPERATION_ERROR"

    def __init__(self, operation: str, reason: str, job_name: str | None = None):
        message = f"HyperPod operation '{operation}' failed: {reason}"
        if job_name:
            message = f"HyperPod operation '{operation}' on job '{job_name}' failed: {reason}"
        super().__init__(message)
        self.operation = operation
        self.reason = reason
        self.job_name = job_name
