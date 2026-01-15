"""Audit module specific exceptions."""

from src.shared.domain import DomainError


class AuditLogError(DomainError):
    """Base exception for audit log errors."""

    pass


class AuditLogNotFoundError(AuditLogError):
    """Raised when an audit log is not found."""

    def __init__(self, audit_log_id: int):
        super().__init__(f"Audit log with id '{audit_log_id}' not found")
        self.audit_log_id = audit_log_id
