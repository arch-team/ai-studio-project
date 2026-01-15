"""Model domain layer - Entities, value objects, and repository interfaces."""

from .entities import Model
from .exceptions import (
    DuplicateModelVersionError,
    InvalidModelStateError,
    ModelError,
    ModelNotFoundError,
)
from .repositories import IModelRepository
from .value_objects import (
    MODEL_STATE_TRANSITIONS,
    ModelFramework,
    ModelStatus,
)

__all__ = [
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
