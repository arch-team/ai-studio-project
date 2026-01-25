"""Dataset API schemas."""

from .requests import (
    CreateDatasetRequest,
    CreateDatasetVersionRequest,
    DatasetStorageTypeEnum,
    DatasetTypeEnum,
    DatasetVisibilityEnum,
    UpdateDatasetRequest,
)
from .responses import (
    DatasetDetail,
    DatasetListResponse,
    DatasetStatusEnum,
    DatasetSummary,
)
from .upload_schemas import (
    CompleteUploadResponse,
    GeneratePresignedUrlsRequest,
    InitiateUploadRequest,
    InitiateUploadResponse,
    PresignedUrlItem,
    PresignedUrlsResponse,
    RegisterPartRequest,
    UploadProgressResponse,
    UploadStatusEnum,
)
from .fsx_schemas import (
    FsxAvailabilityResponse,
    FsxPathResponse,
    FsxSyncResponse,
    FsxSyncStatusResponse,
    FsxTaskStatusEnum,
    PrefetchDatasetRequest,
)

__all__ = [
    # Request schemas
    "CreateDatasetRequest",
    "CreateDatasetVersionRequest",
    "UpdateDatasetRequest",
    # Response schemas
    "DatasetSummary",
    "DatasetDetail",
    "DatasetListResponse",
    # Enums (re-export from responses for consistency)
    "DatasetStorageTypeEnum",
    "DatasetTypeEnum",
    "DatasetVisibilityEnum",
    "DatasetStatusEnum",
    # Upload schemas
    "InitiateUploadRequest",
    "InitiateUploadResponse",
    "GeneratePresignedUrlsRequest",
    "PresignedUrlItem",
    "PresignedUrlsResponse",
    "RegisterPartRequest",
    "UploadProgressResponse",
    "CompleteUploadResponse",
    "UploadStatusEnum",
    # FSx schemas
    "PrefetchDatasetRequest",
    "FsxSyncResponse",
    "FsxSyncStatusResponse",
    "FsxPathResponse",
    "FsxAvailabilityResponse",
    "FsxTaskStatusEnum",
]
