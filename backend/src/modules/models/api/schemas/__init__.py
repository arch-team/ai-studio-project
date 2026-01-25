"""Model API schemas."""

from .requests import (
    CreateModelRequest,
    ModelFrameworkEnum,
    UpdateModelRequest,
)
from .responses import (
    MetricsDiff,
    ModelDetail,
    ModelErrorResponse,
    ModelListResponse,
    ModelStatusEnum,
    ModelSummary,
    ModelVersionsResponse,
    ModelVersionSummary,
    VersionComparison,
)

__all__ = [
    # Request schemas
    "CreateModelRequest",
    "UpdateModelRequest",
    # Response schemas
    "ModelSummary",
    "ModelDetail",
    "ModelListResponse",
    "ModelVersionSummary",
    "ModelVersionsResponse",
    "VersionComparison",
    "MetricsDiff",
    "ModelErrorResponse",
    # Enums
    "ModelFrameworkEnum",
    "ModelStatusEnum",
]
