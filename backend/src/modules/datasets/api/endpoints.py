"""Datasets API endpoints - CRUD operations for datasets."""

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.auth.api.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.modules.datasets.api.dependencies import (
    get_dataset_service,
    get_dataset_upload_service,
    get_fsx_sync_service,
)
from src.modules.datasets.api.schemas import (
    CompleteUploadResponse,
    CreateDatasetRequest,
    CreateDatasetVersionRequest,
    DatasetDetail,
    DatasetListResponse,
    DatasetStatusEnum,
    DatasetStorageTypeEnum,
    DatasetSummary,
    DatasetTypeEnum,
    DatasetVisibilityEnum,
    FsxAvailabilityResponse,
    FsxPathResponse,
    FsxSyncResponse,
    FsxSyncStatusResponse,
    GeneratePresignedUrlsRequest,
    InitiateUploadRequest,
    InitiateUploadResponse,
    PrefetchDatasetRequest,
    PresignedUrlItem,
    PresignedUrlsResponse,
    RegisterPartRequest,
    UpdateDatasetRequest,
    UploadProgressResponse,
    UploadStatusEnum,
)
from src.modules.datasets.application.services import (
    DatasetService,
    DatasetUploadService,
    FsxSyncService,
)
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetType,
    DatasetVisibility,
)
from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)
from src.shared.utils import EnumMapper

router = APIRouter()


@router.post(
    "",
    response_model=DatasetDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset(
    data: CreateDatasetRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Create a new dataset.

    Registers a new dataset with the specified storage location and metadata.
    """
    dataset_data = data.model_dump(mode="json")
    dataset = await service.create_dataset(
        owner_id=current_user.user_id,
        data=dataset_data,
    )
    return DatasetDetail.from_entity(dataset)


@router.get(
    "",
    response_model=DatasetListResponse,
)
async def list_datasets(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    dataset_type: DatasetTypeEnum | None = Query(
        default=None, description="Filter by dataset type"
    ),
    storage_type: DatasetStorageTypeEnum | None = Query(
        default=None, description="Filter by storage type"
    ),
    visibility: DatasetVisibilityEnum | None = Query(
        default=None, description="Filter by visibility"
    ),
    status_filter: DatasetStatusEnum | None = Query(
        default=None, alias="status", description="Filter by status"
    ),
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """List datasets with pagination and filters.

    Returns datasets owned by the current user, or all datasets if admin.
    """
    owner_id = get_owner_filter(current_user)

    datasets, total = await service.list_datasets(
        owner_id=owner_id,
        status=EnumMapper.to_domain(status_filter, DatasetStatus),
        dataset_type=EnumMapper.to_domain(dataset_type, DatasetType),
        visibility=EnumMapper.to_domain(visibility, DatasetVisibility),
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )

    return DatasetListResponse(
        **build_paginated_response(
            items=[DatasetSummary.from_entity(ds) for ds in datasets],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetDetail,
)
async def get_dataset(
    dataset_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """Get dataset details by ID.

    Returns detailed information about a specific dataset.
    """
    dataset = await service.get_dataset(dataset_id)

    # Check access - owner, admin, or public dataset
    if not dataset.is_accessible_by(current_user.user_id) and not current_user.is_admin:
        check_resource_owner_or_privileged(
            dataset.owner_id, current_user, "dataset", "view"
        )

    # Update access time
    dataset.update_access_time()

    return DatasetDetail.from_entity(dataset)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetDetail,
)
async def update_dataset(
    dataset_id: int,
    data: UpdateDatasetRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Update dataset metadata.

    Only description, tags, and visibility can be updated.
    """
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "update"
    )

    dataset = await service.update_dataset(
        dataset_id=dataset_id,
        data=data.model_dump(exclude_unset=True, mode="json"),
    )
    return DatasetDetail.from_entity(dataset)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset(
    dataset_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Delete (archive) a dataset.

    Soft-deletes the dataset by setting its status to ARCHIVED.
    """
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "delete"
    )

    await service.delete_dataset(dataset_id)
    return None


@router.post(
    "/{dataset_id}/versions",
    response_model=DatasetDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset_version(
    dataset_id: int,
    data: CreateDatasetVersionRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Create a new version of a dataset.

    Creates a new dataset entry with the same name but different version.
    """
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "create version of"
    )

    new_dataset = await service.create_version(
        dataset_id=dataset_id,
        version=data.version,
        storage_uri=data.storage_uri,
        description=data.description,
    )
    return DatasetDetail.from_entity(new_dataset)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# ========== 上传端点 ==========


@router.post(
    "/{dataset_id}/upload/initiate",
    response_model=InitiateUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_upload(
    dataset_id: int,
    data: InitiateUploadRequest,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """初始化分片上传。

    开始一个新的 S3 分片上传会话。返回 upload_id 供后续操作使用。
    """
    # 检查数据集权限
    dataset = await dataset_service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "upload to"
    )

    session = await upload_service.initiate_multipart_upload(
        dataset_id=dataset_id,
        filename=data.filename,
        content_type=data.content_type,
        total_size=data.total_size,
        owner_id=current_user.user_id,
        part_size=data.part_size,
    )

    return InitiateUploadResponse(
        upload_id=session.upload_id,
        dataset_id=session.dataset_id,
        bucket=session.bucket,
        key=session.key,
        expected_part_count=session.expected_part_count,
        part_size=session.part_size,
    )


@router.post(
    "/{dataset_id}/upload/{upload_id}/presigned-urls",
    response_model=PresignedUrlsResponse,
)
async def generate_presigned_urls(
    dataset_id: int,
    upload_id: str,
    data: GeneratePresignedUrlsRequest,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
):
    """生成分片上传预签名 URL。

    批量生成用于上传分片的预签名 URL。客户端使用这些 URL 直接上传到 S3。
    """
    urls = await upload_service.generate_presigned_urls(
        upload_id=upload_id,
        part_numbers=data.part_numbers,
        expiration=data.expiration,
    )

    return PresignedUrlsResponse(
        upload_id=upload_id,
        urls=[PresignedUrlItem(**url) for url in urls],
        expiration=data.expiration,
    )


@router.post(
    "/{dataset_id}/upload/{upload_id}/parts",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def register_part_completion(
    dataset_id: int,
    upload_id: str,
    data: RegisterPartRequest,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
):
    """注册分片完成。

    客户端上传分片到 S3 后，调用此端点注册完成。
    """
    await upload_service.register_part_completion(
        upload_id=upload_id,
        part_number=data.part_number,
        etag=data.etag,
        size_bytes=data.size_bytes,
        md5_checksum=data.md5_checksum,
    )
    return None


@router.get(
    "/{dataset_id}/upload/{upload_id}/progress",
    response_model=UploadProgressResponse,
)
async def get_upload_progress(
    dataset_id: int,
    upload_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
):
    """获取上传进度。

    返回当前上传会话的进度信息，包括已完成和缺失的分片列表（用于断点续传）。
    """
    progress = await upload_service.get_upload_progress(upload_id=upload_id)

    return UploadProgressResponse(
        upload_id=progress["upload_id"],
        dataset_id=progress["dataset_id"],
        filename=progress["filename"],
        total_size=progress["total_size"],
        uploaded_bytes=progress["uploaded_bytes"],
        progress_percentage=progress["progress_percentage"],
        expected_part_count=progress["expected_part_count"],
        completed_part_count=progress["completed_part_count"],
        missing_parts=progress["missing_parts"],
        status=UploadStatusEnum(progress["status"]),
        created_at=progress["created_at"],
        updated_at=progress["updated_at"],
    )


@router.post(
    "/{dataset_id}/upload/{upload_id}/complete",
    response_model=CompleteUploadResponse,
)
async def complete_upload(
    dataset_id: int,
    upload_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
):
    """完成分片上传。

    所有分片上传完成后调用。将触发 S3 合并分片，并更新数据集状态为 AVAILABLE。
    """
    result = await upload_service.complete_multipart_upload(upload_id=upload_id)

    return CompleteUploadResponse(
        etag=result["etag"],
        location=result.get("location"),
        bucket=result["bucket"],
        key=result["key"],
        size=result["size"],
    )


@router.delete(
    "/{dataset_id}/upload/{upload_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def abort_upload(
    dataset_id: int,
    upload_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
):
    """取消分片上传。

    取消正在进行的上传会话，清理 S3 上已上传的分片。
    """
    await upload_service.abort_multipart_upload(upload_id=upload_id)
    return None


# ========== FSx 端点 ==========


@router.post(
    "/{dataset_id}/fsx/sync",
    response_model=FsxSyncResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_fsx_sync(
    dataset_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """发起 S3 → FSx 同步。

    创建 FSx Data Repository Task 将数据集从 S3 同步到 FSx。
    """
    dataset = await dataset_service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "sync to FSx"
    )

    result = await fsx_service.initiate_s3_to_fsx_sync(dataset_id=dataset_id)

    return FsxSyncResponse(
        task_id=result["task_id"],
        status=result["status"],
        type=result["type"],
        dataset_id=result["dataset_id"],
        paths=result["paths"],
    )


@router.get(
    "/{dataset_id}/fsx/sync/{task_id}",
    response_model=FsxSyncStatusResponse,
)
async def get_fsx_sync_status(
    dataset_id: int,
    task_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
):
    """获取 FSx 同步任务状态。"""
    result = await fsx_service.get_sync_status(task_id=task_id)

    return FsxSyncStatusResponse(
        task_id=result["task_id"],
        status=result["status"],
        type=result.get("type"),
        progress=result.get("progress", {}),
        paths=result.get("paths", []),
    )


@router.post(
    "/{dataset_id}/fsx/prefetch",
    response_model=FsxSyncResponse,
    status_code=status.HTTP_201_CREATED,
)
async def prefetch_dataset_to_fsx(
    dataset_id: int,
    data: PrefetchDatasetRequest,
    current_user: CurrentUser = Depends(require_engineer),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """预热数据集到 FSx 缓存。

    为训练任务预先加载数据集到 FSx，减少首次访问延迟。
    """
    dataset = await dataset_service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "prefetch to FSx"
    )

    result = await fsx_service.prefetch_dataset(
        dataset_id=dataset_id,
        paths=data.paths,
    )

    return FsxSyncResponse(
        task_id=result["task_id"],
        status=result["status"],
        type=result["type"],
        dataset_id=result["dataset_id"],
        paths=result["paths"],
    )


@router.delete(
    "/{dataset_id}/fsx/cache",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def release_dataset_cache(
    dataset_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """释放数据集 FSx 缓存。

    释放数据集在 FSx 上占用的存储空间，数据仍保留在 S3。
    """
    dataset = await dataset_service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "release FSx cache"
    )

    await fsx_service.release_dataset(dataset_id=dataset_id)
    return None


@router.get(
    "/{dataset_id}/fsx/path",
    response_model=FsxPathResponse,
)
async def get_dataset_fsx_path(
    dataset_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """获取数据集的 FSx 路径信息。"""
    dataset = await dataset_service.get_dataset(dataset_id)

    if not dataset.is_accessible_by(current_user.user_id) and not current_user.is_admin:
        check_resource_owner_or_privileged(
            dataset.owner_id, current_user, "dataset", "view FSx path"
        )

    result = await fsx_service.get_dataset_fsx_path(dataset_id=dataset_id)

    return FsxPathResponse(
        dataset_id=result["dataset_id"],
        fsx_path=result["fsx_path"],
        s3_path=result["s3_path"],
        storage_uri=result.get("storage_uri"),
    )


@router.get(
    "/fsx/health",
    response_model=FsxAvailabilityResponse,
)
async def check_fsx_health(
    current_user: CurrentUser = Depends(get_current_active_user),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
):
    """检查 FSx 文件系统可用性。"""
    result = await fsx_service.check_fsx_availability()

    return FsxAvailabilityResponse(
        available=result["available"],
        filesystem_id=result.get("filesystem_id"),
        storage_capacity_gb=result.get("storage_capacity_gb"),
        lifecycle=result.get("lifecycle"),
        error=result.get("error"),
    )
