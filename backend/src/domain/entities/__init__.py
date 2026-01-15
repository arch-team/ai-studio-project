"""Domain Entities - Core business objects with identity.

Entities represent the core business concepts of the AI Training Platform:
- User: Platform user with permissions
- ResourceQuota: Resource allocation and limits
- ResourceLimitConfig: Per-job resource limits by role
- AuditLog: Audit trail for platform operations
- Space: SageMaker Spaces for development environments
"""

from src.domain.entities.audit_log import (
    AuditLog,
    AuditStatus,
    OperationType,
    ResourceType,
)
from src.domain.entities.resource_limit_config import (
    LimitRole,
    PriorityDefault,
    ResourceLimitConfig,
)
from src.domain.entities.resource_quota import QuotaStatus, QuotaType, ResourceQuota
from src.domain.entities.checkpoint import (
    Checkpoint,
    CheckpointStatus,
    CheckpointType,
    STORAGE_TIER_HIERARCHY,
    StorageTier,
)
from src.domain.entities.model import (
    Model,
    ModelFramework,
    ModelStatus,
    MODEL_STATE_TRANSITIONS,
)
from src.domain.entities.space import Space, SpaceInstanceType, SpaceStatus, SpaceType
from src.domain.entities.training_job import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
    TRAINING_JOB_STATE_TRANSITIONS,
    TrainingJob,
)
from src.domain.entities.user import User, UserRole, UserStatus

__all__ = [
    # User
    "User",
    "UserStatus",
    "UserRole",
    # ResourceQuota
    "ResourceQuota",
    "QuotaType",
    "QuotaStatus",
    # ResourceLimitConfig
    "ResourceLimitConfig",
    "LimitRole",
    "PriorityDefault",
    # AuditLog
    "AuditLog",
    "OperationType",
    "ResourceType",
    "AuditStatus",
    # Space
    "Space",
    "SpaceInstanceType",
    "SpaceType",
    "SpaceStatus",
    # TrainingJob
    "TrainingJob",
    "JobStatus",
    "DistributionStrategy",
    "JobPriority",
    "SpotInterruptionBehavior",
    "TRAINING_JOB_STATE_TRANSITIONS",
    # Checkpoint
    "Checkpoint",
    "CheckpointType",
    "StorageTier",
    "CheckpointStatus",
    "STORAGE_TIER_HIERARCHY",
    # Model
    "Model",
    "ModelFramework",
    "ModelStatus",
    "MODEL_STATE_TRANSITIONS",
]
