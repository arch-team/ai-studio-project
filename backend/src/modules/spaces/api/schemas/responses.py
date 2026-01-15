"""Space API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema
from src.shared.utils import EnumMapper

if TYPE_CHECKING:
    from src.modules.spaces.domain.entities import Space


class SpaceInstanceTypeEnum(str, Enum):
    """Space instance type enum for API."""

    ML_T3_MEDIUM = "ml.t3.medium"
    ML_T3_LARGE = "ml.t3.large"
    ML_G4DN_XLARGE = "ml.g4dn.xlarge"
    ML_G5_XLARGE = "ml.g5.xlarge"
    ML_G5_2XLARGE = "ml.g5.2xlarge"


class SpaceTypeEnum(str, Enum):
    """Space IDE type enum for API."""

    JUPYTER = "jupyter"
    VSCODE = "vscode"
    RSTUDIO = "rstudio"


class SpaceStatusEnum(str, Enum):
    """Space status enum for API."""

    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETED = "deleted"


class SpaceSummary(EntitySchema["Space"]):
    """Space summary for list responses."""

    id: str
    space_name: str
    owner_id: int
    instance_type: SpaceInstanceTypeEnum
    space_type: SpaceTypeEnum
    status: SpaceStatusEnum
    created_at: datetime

    @classmethod
    def _map_entity_fields(cls, entity: "Space") -> dict:
        """Map Space entity to summary schema fields."""
        return {
            "id": entity.id,
            "space_name": entity.space_name,
            "owner_id": entity.owner_id,
            "instance_type": EnumMapper.to_api(entity.instance_type, SpaceInstanceTypeEnum),
            "space_type": EnumMapper.to_api(entity.space_type, SpaceTypeEnum),
            "status": EnumMapper.to_api(entity.status, SpaceStatusEnum),
            "created_at": entity.created_at,
        }


class SpaceDetail(EntitySchema["Space"]):
    """Space detail response."""

    id: str
    space_name: str
    owner_id: int
    instance_type: SpaceInstanceTypeEnum
    space_type: SpaceTypeEnum
    storage_size_gb: int
    status: SpaceStatusEnum
    lifecycle_config_arn: str | None = None
    sagemaker_space_arn: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @classmethod
    def _map_entity_fields(cls, entity: "Space") -> dict:
        """Map Space entity to detail schema fields."""
        return {
            "id": entity.id,
            "space_name": entity.space_name,
            "owner_id": entity.owner_id,
            "instance_type": EnumMapper.to_api(entity.instance_type, SpaceInstanceTypeEnum),
            "space_type": EnumMapper.to_api(entity.space_type, SpaceTypeEnum),
            "storage_size_gb": entity.storage_size_gb,
            "status": EnumMapper.to_api(entity.status, SpaceStatusEnum),
            "lifecycle_config_arn": entity.lifecycle_config_arn,
            "sagemaker_space_arn": entity.sagemaker_space_arn,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "deleted_at": entity.deleted_at,
        }


class SpaceListResponse(BaseModel):
    """Paginated list of spaces."""

    items: list[SpaceSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class SpaceErrorResponse(BaseModel):
    """Space operation error response."""

    code: str
    message: str
    details: dict | None = None
