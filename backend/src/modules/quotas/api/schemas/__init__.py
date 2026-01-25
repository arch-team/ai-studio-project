"""Quotas API schemas - Pydantic request/response models."""

from .requests import (
    CreateResourceLimitConfigRequest,
    CreateResourceQuotaRequest,
    UpdateResourceLimitConfigRequest,
    UpdateResourceQuotaRequest,
)
from .responses import (
    LimitRoleEnum,
    PriorityDefaultEnum,
    QuotaStatusEnum,
    QuotaTypeEnum,
    ResourceLimitConfigListResponse,
    ResourceLimitConfigResponse,
    ResourceQuotaListResponse,
    ResourceQuotaResponse,
)

__all__ = [
    # Enums
    "LimitRoleEnum",
    "PriorityDefaultEnum",
    "QuotaTypeEnum",
    "QuotaStatusEnum",
    # ResourceLimitConfig Requests
    "CreateResourceLimitConfigRequest",
    "UpdateResourceLimitConfigRequest",
    # ResourceLimitConfig Responses
    "ResourceLimitConfigResponse",
    "ResourceLimitConfigListResponse",
    # ResourceQuota Requests (T058-T060)
    "CreateResourceQuotaRequest",
    "UpdateResourceQuotaRequest",
    # ResourceQuota Responses (T058-T060)
    "ResourceQuotaResponse",
    "ResourceQuotaListResponse",
]
