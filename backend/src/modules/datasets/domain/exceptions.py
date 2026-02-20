"""Dataset domain exceptions.

使用 @problem 装饰器和 @dataclass 简化异常定义。
"""

from dataclasses import dataclass

from src.shared.domain.problem import Problem, problem


@problem(404, "DATASET_NOT_FOUND", "Dataset '{dataset_id}' not found")
@dataclass
class DatasetNotFoundError(Problem):
    """数据集未找到."""

    dataset_id: int | str


@problem(
    409,
    "DUPLICATE_DATASET_VERSION",
    "Dataset '{name}' version '{version}' already exists",
)
@dataclass
class DuplicateDatasetVersionError(Problem):
    """数据集版本重复."""

    name: str
    version: str


@problem(
    409,
    "INVALID_DATASET_STATE",
    "Cannot {operation} dataset {dataset_id} in state '{current_state}'",
)
@dataclass
class InvalidDatasetStateError(Problem):
    """数据集状态无效."""

    dataset_id: int
    current_state: str
    operation: str


@problem(
    403,
    "DATASET_ACCESS_DENIED",
    "Access denied: user {user_id} cannot access dataset {dataset_id}",
)
@dataclass
class DatasetAccessDeniedError(Problem):
    """数据集访问被拒绝."""

    user_id: int
    dataset_id: int


@problem(
    500,
    "DATASET_STORAGE_ERROR",
    "Storage operation failed for dataset {dataset_id}: {reason}",
)
@dataclass
class DatasetStorageError(Problem):
    """数据集存储操作失败."""

    dataset_id: int | None = None
    reason: str = "Unknown error"


# ========== 上传相关异常 ==========
@problem(
    409,
    "UPLOAD_SESSION_ACTIVE",
    "Dataset {dataset_id} already has an active upload session: {upload_id}",
)
@dataclass
class UploadSessionActiveError(Problem):
    """数据集已有活跃上传会话."""

    dataset_id: int
    upload_id: str


@problem(
    404,
    "UPLOAD_SESSION_NOT_FOUND",
    "Upload session '{upload_id}' not found",
)
@dataclass
class UploadSessionNotFoundError(Problem):
    """上传会话未找到."""

    upload_id: str


@problem(
    409,
    "UPLOAD_INCOMPLETE",
    "Upload {upload_id} is incomplete: missing parts {missing_parts}",
)
@dataclass
class UploadIncompleteError(Problem):
    """上传未完成."""

    upload_id: str
    missing_parts: list[int]


# ========== FSx 相关异常 ==========
@problem(
    404,
    "FSX_SYNC_TASK_NOT_FOUND",
    "FSx sync task '{task_id}' not found",
)
@dataclass
class FsxSyncTaskNotFoundError(Problem):
    """FSx 同步任务未找到."""

    task_id: str


@problem(
    500,
    "FSX_SYNC_FAILED",
    "FSx sync failed for dataset {dataset_id}: {reason}",
)
@dataclass
class FsxSyncFailedError(Problem):
    """FSx 同步失败."""

    dataset_id: int | None = None
    reason: str = "Unknown error"
