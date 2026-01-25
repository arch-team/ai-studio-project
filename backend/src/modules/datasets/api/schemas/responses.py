"""Dataset API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from src.shared.api.schemas import AutoMappingEntitySchema

if TYPE_CHECKING:
    from src.modules.datasets.domain.entities import Dataset  # noqa: F401


class DatasetStorageTypeEnum(str, Enum):
    """Dataset storage type for API."""

    FSX = "fsx"
    S3 = "s3"
    EFS = "efs"


class DatasetTypeEnum(str, Enum):
    """Dataset type for API."""

    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    TABULAR = "tabular"
    CUSTOM = "custom"


class DatasetVisibilityEnum(str, Enum):
    """Dataset visibility for API."""

    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class DatasetStatusEnum(str, Enum):
    """Dataset status for API."""

    AVAILABLE = "available"
    PREPARING = "preparing"
    ARCHIVED = "archived"
    ERROR = "error"


class DatasetSummary(AutoMappingEntitySchema["Dataset"]):
    """Dataset summary for list view."""

    id: int
    name: str
    version: str
    description: str | None = None
    storage_type: DatasetStorageTypeEnum
    dataset_type: DatasetTypeEnum
    total_size_bytes: int | None = None
    file_count: int | None = None
    visibility: DatasetVisibilityEnum
    status: DatasetStatusEnum
    created_at: datetime

    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
        "storage_type": DatasetStorageTypeEnum,
        "dataset_type": DatasetTypeEnum,
        "visibility": DatasetVisibilityEnum,
        "status": DatasetStatusEnum,
    }


class DatasetDetail(DatasetSummary):
    """Dataset detailed view - inherits DatasetSummary."""

    storage_uri: str
    data_format: str | None = None
    tags: list[str] | None = None
    owner_id: int
    updated_at: datetime
    last_accessed_at: datetime | None = None

    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
        **DatasetSummary._enum_mappings,
    }


class DatasetListResponse(BaseModel):
    """Paginated list of datasets."""

    items: list[DatasetSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
