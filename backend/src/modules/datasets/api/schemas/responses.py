"""Dataset API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema

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


class DatasetSummary(EntitySchema["Dataset"]):
    """Dataset summary for list view.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

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


class DatasetDetail(DatasetSummary):
    """Dataset detailed view - inherits DatasetSummary.

    自动继承父类枚举映射。
    """

    storage_uri: str
    data_format: str | None = None
    tags: list[str] | None = None
    owner_id: int
    updated_at: datetime
    last_accessed_at: datetime | None = None


class DatasetListResponse(BaseModel):
    """Paginated list of datasets."""

    items: list[DatasetSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
