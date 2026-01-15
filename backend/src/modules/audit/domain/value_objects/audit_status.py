"""Audit status value object for audit logging."""

from enum import Enum


class AuditStatus(Enum):
    """Audit log operation status."""

    SUCCESS = "success"
    FAILED = "failed"
