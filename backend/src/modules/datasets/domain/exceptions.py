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
