"""Training domain layer - Entities, value objects, and repositories."""

from .entities import Checkpoint, TrainingJob
from .exceptions import (
    CheckpointNotFoundError,
    DuplicateJobNameError,
    InvalidJobStateError,
    TrainingError,
    TrainingJobNotFoundError,
)
from .repositories import ICheckpointRepository, ITrainingJobRepository
from .value_objects import (
    CheckpointStatus,
    CheckpointType,
    DistributionStrategy,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
    StorageTier,
    TrainingMetrics,
)

__all__ = [
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
