"""Training module - Training job and checkpoint management for AI training platform."""

from .api import router
from .application import CheckpointService, IHyperPodClient, TrainingJobService
from .domain import (
    Checkpoint,
    CheckpointNotFoundError,
    CheckpointStatus,
    CheckpointType,
    DistributionStrategy,
    DuplicateJobNameError,
    ICheckpointRepository,
    InvalidJobStateError,
    ITrainingJobRepository,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
    StorageTier,
    TrainingError,
    TrainingJob,
    TrainingJobNotFoundError,
    TrainingMetrics,
)

__all__ = [
    # Router
    "router",
    # Services
    "TrainingJobService",
    "CheckpointService",
    # Interfaces
    "IHyperPodClient",
    # Entities
    "TrainingJob",
    "Checkpoint",
    # Value Objects
    "JobStatus",
    "JobPriority",
    "DistributionStrategy",
    "SpotInterruptionBehavior",
    "CheckpointType",
    "CheckpointStatus",
    "StorageTier",
    "TrainingMetrics",
    # Repositories
    "ITrainingJobRepository",
    "ICheckpointRepository",
    # Exceptions
    "TrainingError",
    "TrainingJobNotFoundError",
    "CheckpointNotFoundError",
    "DuplicateJobNameError",
    "InvalidJobStateError",
]
