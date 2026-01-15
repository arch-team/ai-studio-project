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
    ModelFrameworkEnum,
    ModelListResponse,
    ModelStatusEnum,
    ModelSummary,
    ModelVersionSummary,
    ModelVersionsResponse,
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
