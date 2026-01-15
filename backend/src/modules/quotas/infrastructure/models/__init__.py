"""Quotas infrastructure ORM models."""

from .resource_limit_config_model import ResourceLimitConfigModel
from .resource_quota_model import ResourceQuotaModel

__all__ = [
    "ResourceQuotaModel",
    "ResourceLimitConfigModel",
]
