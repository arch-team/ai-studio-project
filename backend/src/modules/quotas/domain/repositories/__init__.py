"""Quotas domain repository interfaces."""

from .resource_limit_config_repository import IResourceLimitConfigRepository
from .resource_quota_repository import IResourceQuotaRepository

__all__ = [
    "IResourceLimitConfigRepository",
    "IResourceQuotaRepository",
]
