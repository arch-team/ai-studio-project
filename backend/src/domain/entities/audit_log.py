"""AuditLog domain entity - Audit trail for platform operations."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


class OperationType(Enum):
    """Operation type for audit logging."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"


class ResourceType(Enum):
    """Resource type being audited."""

    TRAINING_JOB = "training_job"
    DATASET = "dataset"
    MODEL = "model"
    USER = "user"
    QUOTA = "quota"
    SPACE = "space"


class AuditStatus(Enum):
    """Audit log operation status."""

    SUCCESS = "success"
    FAILED = "failed"


# Default retention period in days
AUDIT_LOG_RETENTION_DAYS = 90


@dataclass
class AuditLog:
    """Audit log domain entity for tracking platform operations.

    Automatically sets expiration date based on retention policy.
    """

    id: int
    operation_type: OperationType
    resource_type: ResourceType
    status: AuditStatus = AuditStatus.SUCCESS

    # User and resource info
    user_id: Optional[int] = None
    resource_id: Optional[str] = None

    # Request/Response data
    request_data: Optional[dict[str, Any]] = None
    response_data: Optional[dict[str, Any]] = None

    # Client info
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default=None)  # type: ignore

    def __post_init__(self) -> None:
        """Set expires_at if not provided."""
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(days=AUDIT_LOG_RETENTION_DAYS)

    def is_expired(self) -> bool:
        """Check if audit log has expired."""
        return datetime.utcnow() > self.expires_at

    def days_until_expiration(self) -> int:
        """Get number of days until expiration."""
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def mark_as_failed(self, error_message: Optional[str] = None) -> None:
        """Mark operation as failed with optional error message."""
        self.status = AuditStatus.FAILED
        if error_message and self.response_data is None:
            self.response_data = {}
        if error_message:
            self.response_data["error"] = error_message  # type: ignore

    @staticmethod
    def create_login_log(
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
    ) -> "AuditLog":
        """Factory method for login audit logs."""
        return AuditLog(
            id=0,
            operation_type=OperationType.LOGIN,
            resource_type=ResourceType.USER,
            status=AuditStatus.SUCCESS if success else AuditStatus.FAILED,
            user_id=user_id,
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def create_resource_log(
        operation: OperationType,
        resource_type: ResourceType,
        resource_id: str,
        user_id: Optional[int] = None,
        request_data: Optional[dict[str, Any]] = None,
        response_data: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> "AuditLog":
        """Factory method for resource operation audit logs."""
        return AuditLog(
            id=0,
            operation_type=operation,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            request_data=request_data,
            response_data=response_data,
            ip_address=ip_address,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "operation_type": self.operation_type.value,
            "resource_type": self.resource_type.value,
            "status": self.status.value,
            "user_id": self.user_id,
            "resource_id": self.resource_id,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }
