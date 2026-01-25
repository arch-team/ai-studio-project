"""Quotas infrastructure repository implementations."""

from .resource_limit_config_repository_impl import ResourceLimitConfigRepository
from .resource_quota_repository_impl import ResourceQuotaRepository

__all__ = [
    "ResourceLimitConfigRepository",
    "ResourceQuotaRepository",
]
