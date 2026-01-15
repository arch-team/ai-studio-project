"""Models module - ML model management for AI training platform."""

from .api import router
from .application import ModelService
from .domain import (
    DuplicateModelVersionError,
    IModelRepository,
    InvalidModelStateError,
    Model,
    MODEL_STATE_TRANSITIONS,
    ModelError,
    ModelFramework,
    ModelNotFoundError,
    ModelStatus,
)

__all__ = [
    # Router
    "router",
    # Services
    "ModelService",
    # Entities
    "Model",
    # Value Objects
    "ModelFramework",
    "ModelStatus",
    "MODEL_STATE_TRANSITIONS",
    # Repositories
    "IModelRepository",
    # Exceptions
    "ModelError",
    "ModelNotFoundError",
    "DuplicateModelVersionError",
    "InvalidModelStateError",
]
