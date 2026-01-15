"""Space domain value objects."""

from .space_enums import (
    INSTANCE_TYPE_RESOURCES,
    SPACE_STATE_TRANSITIONS,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)

__all__ = [
    "SpaceInstanceType",
    "SpaceType",
    "SpaceStatus",
    "SPACE_STATE_TRANSITIONS",
    "INSTANCE_TYPE_RESOURCES",
]
