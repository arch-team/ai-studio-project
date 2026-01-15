"""SQLAlchemy ORM Models.

Database models for the AI Training Platform:
- UserModel: User and authentication data
- ResourceQuotaModel: Resource quota definitions
- ResourceLimitConfigModel: Per-job resource limits
- AuditLogModel: Audit trail records
- DevelopmentSpaceModel: SageMaker Spaces records
- PasswordHistoryModel: Password change history
- LoginAttemptModel: Login attempt records
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
from src.infrastructure.persistence.models.login_attempt_model import LoginAttemptModel
from src.infrastructure.persistence.models.password_history_model import (
    PasswordHistoryModel,
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
from src.infrastructure.persistence.models.checkpoint_model import CheckpointModel
from src.infrastructure.persistence.models.model_model import ModelModel
from src.infrastructure.persistence.models.training_job_model import TrainingJobModel
from src.infrastructure.persistence.models.user_model import (
    AuthType,
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
    "AuthType",
    # Authentication
    "PasswordHistoryModel",
    "LoginAttemptModel",
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
    # TrainingJob
    "TrainingJobModel",
    # Checkpoint
    "CheckpointModel",
    # Model
    "ModelModel",
]
