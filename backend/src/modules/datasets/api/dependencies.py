"""Dataset API dependencies - Dependency injection for services."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.datasets.application.services import (
    DatasetService,
    DatasetUploadService,
    FsxSyncService,
)
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.infrastructure.repositories import (
    DatasetRepositoryImpl,
    UploadSessionRepositoryImpl,
)
from src.modules.datasets.infrastructure.fsx import FsxClient
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
