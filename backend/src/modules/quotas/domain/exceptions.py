"""Quotas domain exceptions.

设计说明:
---------
每个异常类包含以下类属性：
- http_status: 对应的 HTTP 状态码
- error_code: 错误代码，供前端程序化处理

异常处理器会自动读取这些属性，无需维护映射表。
"""

from src.shared.domain.exceptions import DomainError, DuplicateEntityError, EntityNotFoundError


class QuotaError(DomainError):
    """Base exception for quota-related errors."""

    error_code = "QUOTA_ERROR"


class QuotaNotFoundError(EntityNotFoundError):
    """Raised when a quota is not found."""

    error_code = "QUOTA_NOT_FOUND"

    def __init__(self, identifier: str):
        super().__init__("ResourceLimitConfig", identifier)
        self.identifier = identifier


class QuotaExceededError(QuotaError):
    """Raised when resource quota is exceeded."""

    http_status = 429
    error_code = "QUOTA_EXCEEDED"

    def __init__(self, resource: str, requested: int, limit: int):
        super().__init__(
            f"{resource} quota exceeded: requested {requested}, limit {limit}"
        )
        self.resource = resource
        self.requested = requested
        self.limit = limit


class DuplicateConfigError(DuplicateEntityError):
    """Raised when config with same role+project already exists."""

    error_code = "DUPLICATE_CONFIG"

    def __init__(self, role: str, scope: str):
        super().__init__("ResourceLimitConfig", f"role={role}, scope={scope}")
        self.role = role
        self.scope = scope
