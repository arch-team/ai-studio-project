"""Models module - ML model management for AI training platform."""

from .api import router
from .application import ModelService
from .domain import (
    MODEL_STATE_TRANSITIONS,
    DuplicateModelVersionError,
    IModelRepository,
    InvalidModelStateError,
    Model,
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
