"""Space API schemas."""

from .requests import (
    CreateSpaceRequest,
    SpaceInstanceTypeEnum,
    SpaceTypeEnum,
    UpdateSpaceRequest,
)
from .responses import (
    SpaceDetail,
    SpaceErrorResponse,
    SpaceInstanceTypeEnum,
    SpaceListResponse,
    SpaceStatusEnum,
    SpaceSummary,
    SpaceTypeEnum,
)

__all__ = [
    # Request schemas
    "CreateSpaceRequest",
    "UpdateSpaceRequest",
    # Response schemas
    "SpaceSummary",
    "SpaceDetail",
    "SpaceListResponse",
    "SpaceErrorResponse",
    # Enums
    "SpaceInstanceTypeEnum",
    "SpaceTypeEnum",
    "SpaceStatusEnum",
]
