"""Model value objects - Enums for model status and framework."""

from enum import Enum


class ModelFramework(Enum):
    """Model framework (matches database modelframework enum)."""

    PYTORCH = "PYTORCH"
    TENSORFLOW = "TENSORFLOW"
    JAX = "JAX"
    OTHER = "OTHER"


class ModelStatus(Enum):
    """Model status (matches database modelstatus enum)."""

    TRAINING = "TRAINING"
    REGISTERED = "REGISTERED"
    DEPLOYED = "DEPLOYED"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"


# Valid state transitions based on model lifecycle
MODEL_STATE_TRANSITIONS = {
    ModelStatus.TRAINING: {ModelStatus.REGISTERED, ModelStatus.FAILED},
    ModelStatus.REGISTERED: {ModelStatus.DEPLOYED, ModelStatus.ARCHIVED},
    ModelStatus.DEPLOYED: {ModelStatus.REGISTERED, ModelStatus.ARCHIVED},
    ModelStatus.ARCHIVED: {ModelStatus.REGISTERED},  # Can restore
    ModelStatus.FAILED: set(),  # Terminal state
}
