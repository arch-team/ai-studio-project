"""Space module domain exceptions.

使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段。
"""

from dataclasses import dataclass

from src.shared.domain.problem import Problem, problem


@problem(400, "SPACE_ERROR")
@dataclass
class SpaceError(Problem):
    """空间模块基础异常."""

    message: str


@problem(404, "SPACE_NOT_FOUND", "Space not found: {space_id}")
@dataclass
class SpaceNotFoundError(Problem):
    """开发空间未找到."""

    space_id: str
@problem(
    409,
    "DUPLICATE_SPACE_NAME",
    "Space name already exists: {space_name} for owner {owner_id}",
)
@dataclass
class DuplicateSpaceNameError(Problem):
    """空间名称重复."""

    space_name: str
    owner_id: int
@problem(
    409,
    "INVALID_SPACE_STATE",
    "Cannot {operation} space {space_id} in {current_state} state",
)
@dataclass
class InvalidSpaceStateError(Problem):
    """空间状态无效."""

    space_id: str
    current_state: str
    operation: str
@problem(
    429,
    "SPACE_QUOTA_EXCEEDED",
    "Insufficient {resource}: need {required}, have {available}",
)
@dataclass
class SpaceQuotaExceededError(Problem):
    """空间资源配额超限."""

    resource: str
    required: int
    available: int
# =============================================================================
