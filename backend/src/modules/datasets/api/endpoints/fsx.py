"""FSx 同步和缓存管理端点。"""

from fastapi import APIRouter, Depends, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user
from src.modules.auth.api.permissions import check_resource_owner_or_privileged
from src.modules.datasets.api.dependencies import (
    get_dataset_service,
    get_fsx_sync_service,
    get_owned_dataset_for_fsx,
)
from src.modules.datasets.api.schemas import (
    FsxAvailabilityResponse,
    FsxPathResponse,
    FsxSyncResponse,
    FsxSyncStatusResponse,
    PrefetchDatasetRequest,
)
from src.modules.datasets.application.services import DatasetService, FsxSyncService
from src.modules.datasets.domain.entities import Dataset

router = APIRouter()


@router.post("/{dataset_id}/fsx/sync", response_model=FsxSyncResponse, status_code=status.HTTP_201_CREATED)
async def initiate_fsx_sync(
    dataset: Dataset = Depends(get_owned_dataset_for_fsx),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
) -> FsxSyncResponse:
    """发起 S3 到 FSx 同步。"""
    assert dataset.id is not None, "Dataset must have ID"
    result = await fsx_service.initiate_s3_to_fsx_sync(dataset_id=dataset.id)

    return FsxSyncResponse(
        task_id=result["task_id"],
        status=result["status"],
        type=result["type"],
        dataset_id=result["dataset_id"],
        paths=result["paths"],
    )


@router.get("/{dataset_id}/fsx/sync/{task_id}", response_model=FsxSyncStatusResponse)
async def get_fsx_sync_status(
    dataset_id: int,
    task_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
) -> FsxSyncStatusResponse:
    """获取 FSx 同步任务状态。

    查询 Data Repository Task 的执行状态和进度。
    """
    result = await fsx_service.get_sync_status(task_id=task_id)

    return FsxSyncStatusResponse(
        task_id=result["task_id"],
        status=result["status"],
        type=result.get("type"),
        progress=result.get("progress", {}),
        paths=result.get("paths", []),
    )


@router.post("/{dataset_id}/fsx/prefetch", response_model=FsxSyncResponse, status_code=status.HTTP_201_CREATED)
async def prefetch_dataset_to_fsx(
    data: PrefetchDatasetRequest,
    dataset: Dataset = Depends(get_owned_dataset_for_fsx),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
) -> FsxSyncResponse:
    """预热数据集到 FSx 缓存。"""
    assert dataset.id is not None, "Dataset must have ID"
    result = await fsx_service.prefetch_dataset(
        dataset_id=dataset.id,
        paths=data.paths,
    )

    return FsxSyncResponse(
        task_id=result["task_id"],
        status=result["status"],
        type=result["type"],
        dataset_id=result["dataset_id"],
        paths=result["paths"],
    )


@router.delete("/{dataset_id}/fsx/cache", status_code=status.HTTP_204_NO_CONTENT)
async def release_dataset_cache(
    dataset: Dataset = Depends(get_owned_dataset_for_fsx),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
) -> None:
    """释放数据集 FSx 缓存。"""
    assert dataset.id is not None, "Dataset must have ID"
    await fsx_service.release_dataset(dataset_id=dataset.id)
    return None


@router.get("/{dataset_id}/fsx/path", response_model=FsxPathResponse)
async def get_dataset_fsx_path(
    dataset_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> FsxPathResponse:
    """获取数据集的 FSx 路径信息。

    返回数据集在 FSx 文件系统和 S3 上的路径映射。
    """
    dataset = await dataset_service.get_dataset(dataset_id)

    if not dataset.is_accessible_by(current_user.user_id) and not current_user.is_admin:
        check_resource_owner_or_privileged(dataset.owner_id, current_user, "dataset", "view FSx path")

    result = await fsx_service.get_dataset_fsx_path(dataset_id=dataset_id)

    return FsxPathResponse(
        dataset_id=result["dataset_id"],
        fsx_path=result["fsx_path"],
        s3_path=result["s3_path"],
        storage_uri=result.get("storage_uri"),
    )


@router.get("/fsx/health", response_model=FsxAvailabilityResponse)
async def check_fsx_health(
    current_user: CurrentUser = Depends(get_current_active_user),
    fsx_service: FsxSyncService = Depends(get_fsx_sync_service),
) -> FsxAvailabilityResponse:
    """检查 FSx 文件系统可用性。

    返回文件系统的状态、容量和生命周期信息。
    """
    result = await fsx_service.check_fsx_availability()

    return FsxAvailabilityResponse(
        available=result["available"],
        filesystem_id=result.get("filesystem_id"),
        storage_capacity_gb=result.get("storage_capacity_gb"),
        lifecycle=result.get("lifecycle"),
        error=result.get("error"),
    )
