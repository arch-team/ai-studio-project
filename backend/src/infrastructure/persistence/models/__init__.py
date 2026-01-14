"""SQLAlchemy ORM Models.

Database models for the AI Training Platform:
- UserModel: User and authentication data
- ResourceQuotaModel: Resource quota definitions
- ResourceLimitConfigModel: Per-job resource limits
- AuditLogModel: Audit trail records
- DevelopmentSpaceModel: SageMaker Spaces records
"""

from src.core.database import Base
from src.infrastructure.persistence.models.audit_log_model import (
    AuditLogModel,
    AuditStatus,
    OperationType,
    ResourceType,
)
from src.infrastructure.persistence.models.base import SoftDeleteMixin, TimestampMixin
from src.infrastructure.persistence.models.development_space_model import (
    DevelopmentSpaceModel,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.infrastructure.persistence.models.resource_limit_config_model import (
    LimitRole,
    PriorityDefault,
    ResourceLimitConfigModel,
)
from src.infrastructure.persistence.models.resource_quota_model import (
    QuotaStatus,
    QuotaType,
    ResourceQuotaModel,
)
from src.infrastructure.persistence.models.user_model import (
    UserModel,
    UserRole,
    UserStatus,
)

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    # User
    "UserModel",
    "UserStatus",
    "UserRole",
    # ResourceQuota
    "ResourceQuotaModel",
    "QuotaType",
    "QuotaStatus",
    # ResourceLimitConfig
    "ResourceLimitConfigModel",
    "LimitRole",
    "PriorityDefault",
    # AuditLog
    "AuditLogModel",
    "OperationType",
    "ResourceType",
    "AuditStatus",
    # DevelopmentSpace
    "DevelopmentSpaceModel",
    "SpaceInstanceType",
    "SpaceType",
    "SpaceStatus",
]
