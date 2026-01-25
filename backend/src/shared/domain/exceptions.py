"""Domain Exceptions - Business rule violation errors.

Domain exceptions represent violations of business rules:
- EntityNotFoundError: Requested entity does not exist
- ValidationError: Business validation failed
- DuplicateEntityError: Entity already exists
- InvalidStateTransitionError: Invalid state change attempted
- ResourceQuotaExceededError: Resource limits exceeded

设计说明:
---------
使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段，无需手动维护。

迁移说明:
---------
本模块已从 DomainError 基类迁移到 Problem 基类。
保留 DomainError 作为别名用于向后兼容，新代码应使用 Problem。
"""

from dataclasses import dataclass, field
from typing import Any

from src.shared.domain.problem import Problem, problem


# =============================================================================
# 通用领域异常
# =============================================================================


@problem(404, "ENTITY_NOT_FOUND", "{entity_type} with id '{entity_id}' not found")
@dataclass
class EntityNotFoundError(Problem):
    """实体未找到 - HTTP 404."""

    entity_type: str
    entity_id: str


@problem(422, "VALIDATION_ERROR")
@dataclass
class ValidationError(Problem):
    """业务验证失败 - HTTP 422."""

    message: str = field(default="Validation failed")
    field_name: str | None = None

    def get_details(self) -> dict[str, Any] | None:
        """仅当 field_name 存在时返回详情."""
        if self.field_name:
            return {"field": self.field_name}
        return None


@problem(409, "DUPLICATE_ENTITY", "{entity_type} with identifier '{identifier}' already exists")
@dataclass
class DuplicateEntityError(Problem):
    """重复实体 - HTTP 409."""

    entity_type: str
    identifier: str


@problem(
    409,
    "INVALID_STATE_TRANSITION",
    "Cannot transition {entity_type} from '{current_state}' to '{target_state}'",
)
@dataclass
class InvalidStateTransitionError(Problem):
    """无效状态转换 - HTTP 409."""

    entity_type: str
    current_state: str
    target_state: str


@problem(
    429,
    "RESOURCE_QUOTA_EXCEEDED",
    "{resource_type} quota exceeded: limit={limit}, requested={requested}",
)
@dataclass
class ResourceQuotaExceededError(Problem):
    """资源配额超限 - HTTP 429 Too Many Requests."""

    resource_type: str
    limit: int
    requested: int


# =============================================================================
# 向后兼容别名 (deprecated)
# =============================================================================


# DomainError 作为 Problem 的别名，用于向后兼容
# 新代码应直接继承 Problem
DomainError = Problem
"""[DEPRECATED] 使用 Problem 替代. 将在下个版本移除."""
