"""Quotas domain layer - Entities, value objects, and repositories for resource quota management."""

from .entities import ResourceLimitConfig, ResourceQuota
from .exceptions import (
    DuplicateConfigError,
    QuotaError,
    QuotaExceededError,
    QuotaNotFoundError,
)
from .repositories import IResourceLimitConfigRepository
from .value_objects import LimitRole, PriorityDefault, QuotaStatus, QuotaType

__all__ = [
    # Entities
    "ResourceQuota",
    "ResourceLimitConfig",
    # Value Objects
    "QuotaType",
    "QuotaStatus",
    "LimitRole",
    "PriorityDefault",
    # Repositories
    "IResourceLimitConfigRepository",
    # Exceptions
    "QuotaError",
    "QuotaNotFoundError",
    "QuotaExceededError",
    "DuplicateConfigError",
]
