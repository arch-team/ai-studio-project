"""Dataset API request schemas."""

from enum import Enum

from pydantic import BaseModel, Field


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


class CreateDatasetRequest(BaseModel):
    """Request body for creating a dataset."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=128,
        description="Dataset name",
    )
    version: str = Field(
        default="v1",
        max_length=32,
        description="Dataset version",
    )
    description: str | None = Field(None, description="Dataset description")
    storage_type: DatasetStorageTypeEnum = Field(
        ...,
        description="Storage type (fsx, s3, efs)",
    )
    storage_uri: str = Field(
        ...,
        max_length=512,
        description="Storage URI (e.g., s3://bucket/path)",
    )
    dataset_type: DatasetTypeEnum = Field(
        ...,
        description="Dataset type (image, text, etc.)",
    )
    data_format: str | None = Field(
        None,
        max_length=64,
        description="Data format (e.g., imagenet, jsonl)",
    )
    tags: list[str] | None = Field(None, description="Tags for categorization")
    visibility: DatasetVisibilityEnum = Field(
        default=DatasetVisibilityEnum.PRIVATE,
        description="Visibility scope",
    )


class UpdateDatasetRequest(BaseModel):
    """Request body for updating a dataset."""

    description: str | None = Field(None, description="Dataset description")
    tags: list[str] | None = Field(None, description="Tags for categorization")
    visibility: DatasetVisibilityEnum | None = Field(
        None, description="Visibility scope"
    )


class CreateDatasetVersionRequest(BaseModel):
    """Request body for creating a new dataset version."""

    version: str = Field(
        ...,
        max_length=32,
        description="Version identifier (e.g., v2, 2.0.0)",
    )
    storage_uri: str | None = Field(
        None,
        max_length=512,
        description="Storage URI for new version (optional, defaults to parent)",
    )
    description: str | None = Field(None, description="Version description")
