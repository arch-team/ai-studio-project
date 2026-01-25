"""Domain Exceptions - Business rule violation errors.

Domain exceptions represent violations of business rules:
- EntityNotFoundError: Requested entity does not exist
- ValidationError: Business validation failed
- DuplicateEntityError: Entity already exists
- InvalidStateTransitionError: Invalid state change attempted
- ResourceQuotaExceededError: Resource limits exceeded

设计说明:
---------
每个异常类包含以下类属性：
- http_status: 对应的 HTTP 状态码
- error_code: 错误代码，供前端程序化处理

异常处理器会自动读取这些属性，无需维护映射表。
新增异常只需定义这两个属性即可。

异常还可以实现 get_details() 方法返回结构化详情:
- 返回 dict 包含与错误相关的上下文信息
- 用于前端显示更详细的错误信息
"""

from typing import Any


class DomainError(Exception):
    """Base exception for all domain errors.

    Attributes:
        http_status: HTTP 状态码，默认 400
        error_code: 错误代码，默认 DOMAIN_ERROR
        message: 错误消息
    """

    http_status: int = 400
    error_code: str = "DOMAIN_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def get_details(self) -> dict[str, Any] | None:
        """返回结构化错误详情。子类可重写以提供更多上下文。"""
        return None


class EntityNotFoundError(DomainError):
    """Raised when a requested entity is not found."""

    http_status = 404
    error_code = "ENTITY_NOT_FOUND"

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(f"{entity_type} with id '{entity_id}' not found")
        self.entity_type = entity_type
        self.entity_id = entity_id

    def get_details(self) -> dict[str, Any]:
        return {"entity_type": self.entity_type, "entity_id": self.entity_id}


class ValidationError(DomainError):
    """Raised when business validation fails."""

    http_status = 422
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field

    def get_details(self) -> dict[str, Any] | None:
        if self.field:
            return {"field": self.field}
        return None


class DuplicateEntityError(DomainError):
    """Raised when attempting to create a duplicate entity."""

    http_status = 409
    error_code = "DUPLICATE_ENTITY"

    def __init__(self, entity_type: str, identifier: str):
        super().__init__(f"{entity_type} with identifier '{identifier}' already exists")
        self.entity_type = entity_type
        self.identifier = identifier

    def get_details(self) -> dict[str, Any]:
        return {"entity_type": self.entity_type, "identifier": self.identifier}


class InvalidStateTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""

    http_status = 409
    error_code = "INVALID_STATE_TRANSITION"

    def __init__(self, entity_type: str, current_state: str, target_state: str):
        super().__init__(
            f"Cannot transition {entity_type} from '{current_state}' to '{target_state}'"
        )
        self.entity_type = entity_type
        self.current_state = current_state
        self.target_state = target_state

    def get_details(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "current_state": self.current_state,
            "target_state": self.target_state,
        }


class ResourceQuotaExceededError(DomainError):
    """Raised when resource quota is exceeded."""

    http_status = 429
    error_code = "RESOURCE_QUOTA_EXCEEDED"

    def __init__(self, resource_type: str, limit: int, requested: int):
        super().__init__(
            f"{resource_type} quota exceeded: limit={limit}, requested={requested}"
        )
        self.resource_type = resource_type
        self.limit = limit
        self.requested = requested

    def get_details(self) -> dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "limit": self.limit,
            "requested": self.requested,
        }
