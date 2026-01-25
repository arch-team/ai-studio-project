"""Audit module specific exceptions.

设计说明:
---------
每个异常类包含以下类属性：
- http_status: 对应的 HTTP 状态码
- error_code: 错误代码，供前端程序化处理

异常处理器会自动读取这些属性，无需维护映射表。
"""

from src.shared.domain import DomainError


class AuditLogError(DomainError):
    """Base exception for audit log errors."""

    error_code = "AUDIT_LOG_ERROR"


class AuditLogNotFoundError(AuditLogError):
    """Raised when an audit log is not found."""

    http_status = 404
    error_code = "AUDIT_LOG_NOT_FOUND"

    def __init__(self, audit_log_id: int):
        super().__init__(f"Audit log with id '{audit_log_id}' not found")
        self.audit_log_id = audit_log_id
