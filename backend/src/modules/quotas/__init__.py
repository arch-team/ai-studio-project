"""Quotas module - Resource quota management for AI training platform.

This module handles resource limit configurations and quotas for users/teams.
"""

from .api import router
from .application import ResourceLimitConfigService
from .domain import (
    DuplicateConfigError,
    IResourceLimitConfigRepository,
    LimitRole,
    PriorityDefault,
    QuotaError,
    QuotaExceededError,
    QuotaNotFoundError,
    QuotaStatus,
    QuotaType,
    ResourceLimitConfig,
    ResourceQuota,
)

__all__ = [
    # Router
    "router",
    # Services
    "ResourceLimitConfigService",
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
