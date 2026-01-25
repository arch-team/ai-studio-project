"""Quotas application services."""

from .resource_limit_config_service import ResourceLimitConfigService
from .resource_quota_service import ResourceQuotaService

__all__ = [
    "ResourceLimitConfigService",
    "ResourceQuotaService",
]
