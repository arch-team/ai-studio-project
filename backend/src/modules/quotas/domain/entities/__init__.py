"""Quotas domain entities."""

from .resource_limit_config import ResourceLimitConfig
from .resource_quota import ResourceQuota

__all__ = [
    "ResourceQuota",
    "ResourceLimitConfig",
]
