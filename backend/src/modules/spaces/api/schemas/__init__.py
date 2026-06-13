"""Space API schemas."""

from .requests import (
    CreateSpaceRequest,
    SpaceBackendEnum,
    SpaceInstanceTypeEnum,
    SpaceTypeEnum,
    UpdateSpaceRequest,
)
from .responses import (
    SpaceAccessUrlResponse,
    SpaceDetail,
    SpaceErrorResponse,
    SpaceListResponse,
    SpaceStatusEnum,
    SpaceSummary,
)

__all__ = [
    # Request schemas
    "CreateSpaceRequest",
    "UpdateSpaceRequest",
    # Response schemas
    "SpaceSummary",
    "SpaceDetail",
    "SpaceListResponse",
    "SpaceAccessUrlResponse",
    "SpaceErrorResponse",
    # Enums
    "SpaceInstanceTypeEnum",
    "SpaceTypeEnum",
    "SpaceBackendEnum",
    "SpaceStatusEnum",
]
