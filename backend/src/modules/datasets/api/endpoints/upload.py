"""数据集分片上传端点。"""

from fastapi import APIRouter, Depends, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.datasets.api.dependencies import (
    get_dataset_upload_service,
    get_owned_dataset_for_upload,
)
from src.modules.datasets.api.schemas import (
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
from src.modules.datasets.application.services import DatasetUploadService
from src.modules.datasets.domain.entities import Dataset

router = APIRouter()


@router.post(
    "/initiate",
    response_model=InitiateUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_upload(
    data: InitiateUploadRequest,
    dataset: Dataset = Depends(get_owned_dataset_for_upload),
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
) -> InitiateUploadResponse:
    """初始化分片上传。"""
    assert dataset.id is not None, "Dataset must have ID"
    session = await upload_service.initiate_multipart_upload(
        dataset_id=dataset.id,
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


@router.post("/{upload_id}/presigned-urls", response_model=PresignedUrlsResponse)
async def generate_presigned_urls(
    upload_id: str,
    data: GeneratePresignedUrlsRequest,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
) -> PresignedUrlsResponse:
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


@router.post("/{upload_id}/parts", status_code=status.HTTP_204_NO_CONTENT)
async def register_part_completion(
    upload_id: str,
    data: RegisterPartRequest,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
) -> None:
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


@router.get("/{upload_id}/progress", response_model=UploadProgressResponse)
async def get_upload_progress(
    upload_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
) -> UploadProgressResponse:
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


@router.post("/{upload_id}/complete", response_model=CompleteUploadResponse)
async def complete_upload(
    upload_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
) -> CompleteUploadResponse:
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


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def abort_upload(
    upload_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    upload_service: DatasetUploadService = Depends(get_dataset_upload_service),
) -> None:
    """取消分片上传。

    取消正在进行的上传会话，清理 S3 上已上传的分片。
    """
    await upload_service.abort_multipart_upload(upload_id=upload_id)
    return None
