"""Spaces module - Development space management for AI training platform."""

from .api import router
from .application import SpaceService
from .domain import (
    INSTANCE_TYPE_RESOURCES,
    SPACE_STATE_TRANSITIONS,
    DuplicateSpaceNameError,
    InvalidSpaceStateError,
    ISpaceRepository,
    Space,
    SpaceError,
    SpaceInstanceType,
    SpaceNotFoundError,
    SpaceQuotaExceededError,
    SpaceStatus,
    SpaceType,
)

__all__ = [
    # Router
    "router",
    # Services
    "SpaceService",
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
]
