"""Dataset API dependencies - Dependency injection for services."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import require_engineer
from src.modules.auth.api.permissions import check_resource_owner_or_privileged
from src.modules.datasets.application.services import (
    DatasetService,
    DatasetUploadService,
    FsxSyncService,
)
from src.modules.datasets.domain.entities import Dataset
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.infrastructure.fsx import FsxClient
from src.modules.datasets.infrastructure.repositories import (
    DatasetRepositoryImpl,
    UploadSessionRepositoryImpl,
)
from src.modules.datasets.infrastructure.s3 import S3MultipartClient
from src.shared.infrastructure import get_db, get_settings


async def get_dataset_repository(
    session: AsyncSession = Depends(get_db),
) -> IDatasetRepository:
    """Dependency for IDatasetRepository."""
    return DatasetRepositoryImpl(session)


async def get_dataset_service(
    session: AsyncSession = Depends(get_db),
) -> DatasetService:
    """Dependency for DatasetService."""
    repository = DatasetRepositoryImpl(session)
    return DatasetService(repository=repository)


@lru_cache(maxsize=1)
def get_s3_multipart_client() -> S3MultipartClient:
    """Singleton dependency for S3MultipartClient."""
    settings = get_settings()
    return S3MultipartClient(
        bucket_name=settings.s3_bucket_name,
        region=settings.aws_region,
    )


async def get_dataset_upload_service(
    session: AsyncSession = Depends(get_db),
    s3_client: S3MultipartClient = Depends(get_s3_multipart_client),
) -> DatasetUploadService:
    """Dependency for DatasetUploadService."""
    dataset_repository = DatasetRepositoryImpl(session)
    upload_session_repository = UploadSessionRepositoryImpl(session)
    return DatasetUploadService(
        upload_session_repository=upload_session_repository,
        dataset_repository=dataset_repository,
        s3_client=s3_client,
    )


@lru_cache(maxsize=1)
def get_fsx_client() -> FsxClient:
    """Singleton dependency for FsxClient."""
    settings = get_settings()
    return FsxClient(
        filesystem_id=settings.fsx_filesystem_id,
        region=settings.aws_region,
        mount_path=settings.fsx_mount_path,
        s3_bucket=settings.s3_bucket_name,
    )


async def get_fsx_sync_service(
    session: AsyncSession = Depends(get_db),
    fsx_client: FsxClient = Depends(get_fsx_client),
) -> FsxSyncService:
    """Dependency for FsxSyncService."""
    dataset_repository = DatasetRepositoryImpl(session)
    return FsxSyncService(
        dataset_repository=dataset_repository,
        fsx_client=fsx_client,
    )


# ========== 资源所有权验证依赖 ==========


async def get_owned_dataset(
    dataset_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
) -> Dataset:
    """获取数据集并验证所有权。

    组合 RBAC 权限检查 + 资源所有权验证。
    仅所有者或特权用户（admin/project_manager）可访问。

    Raises:
        DatasetNotFoundError: 数据集不存在
        HTTPException 403: 用户无权限
    """
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(dataset.owner_id, current_user, "dataset", "access")
    return dataset


async def get_owned_dataset_for_upload(
    dataset_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
) -> Dataset:
    """获取数据集并验证上传权限。"""
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(dataset.owner_id, current_user, "dataset", "upload to")
    return dataset


async def get_owned_dataset_for_fsx(
    dataset_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
) -> Dataset:
    """获取数据集并验证 FSx 操作权限。"""
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(dataset.owner_id, current_user, "dataset", "manage FSx")
    return dataset
