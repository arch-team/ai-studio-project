"""Space domain layer - Entities, value objects, and repository interfaces."""

from .entities import Space
from .exceptions import (
    DuplicateSpaceNameError,
    HyperPodSpaceBackendError,
    InvalidSpaceStateError,
    SpaceBackendUnavailableError,
    SpaceError,
    SpaceNotFoundError,
    SpaceQuotaExceededError,
)
from .repositories import ISpaceRepository
from .value_objects import (
    INSTANCE_TYPE_RESOURCES,
    SPACE_STATE_TRANSITIONS,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)

__all__ = [
    # Entities
    "Space",
    # Value Objects
    "SpaceInstanceType",
    "SpaceType",
    "SpaceStatus",
    "SPACE_STATE_TRANSITIONS",
    "INSTANCE_TYPE_RESOURCES",
    # Repositories
    "ISpaceRepository",
    # Exceptions
    "SpaceError",
    "SpaceNotFoundError",
    "DuplicateSpaceNameError",
    "InvalidSpaceStateError",
    "SpaceQuotaExceededError",
    "HyperPodSpaceBackendError",
    "SpaceBackendUnavailableError",
]
