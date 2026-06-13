"""Space domain value objects."""

from .space_enums import (
    INSTANCE_TYPE_RESOURCES,
    SPACE_STATE_TRANSITIONS,
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from .workspace_status import map_workspace_status

__all__ = [
    "INSTANCE_TYPE_RESOURCES",
    "SPACE_STATE_TRANSITIONS",
    "SpaceBackend",
    "SpaceInstanceType",
    "SpaceStatus",
    "SpaceType",
    "map_workspace_status",
]
