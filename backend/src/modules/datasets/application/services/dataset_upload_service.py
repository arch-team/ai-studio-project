"""Dataset Upload Service - 数据集上传业务逻辑。

提供 S3 分片上传的完整流程:
- 初始化分片上传
- 生成预签名 URL
- 注册分片完成
- 获取上传进度
- 完成/取消上传

支持断点续传 (通过数据库持久化 UploadSession)。
"""

from typing import Any

from src.modules.datasets.domain.exceptions import (
    DatasetNotFoundError,
    UploadIncompleteError,
    UploadSessionActiveError,
    UploadSessionNotFoundError,
)
from src.modules.datasets.domain.repositories import (
    IDatasetRepository,
    IUploadSessionRepository,
)
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    UploadPart,
    UploadSession,
    UploadStatus,
)
from src.modules.datasets.infrastructure.s3 import (
    DEFAULT_PART_SIZE,
    S3MultipartClient,
)
from src.shared.utils import utc_now


class DatasetUploadService:
    """数据集上传服务 - 管理 S3 分片上传生命周期。"""

    # 上传会话默认过期时间（7天后自动过期）
    DEFAULT_SESSION_EXPIRY_DAYS = 7

    def __init__(
        self,
        upload_session_repository: IUploadSessionRepository,
        dataset_repository: IDatasetRepository,
        s3_client: S3MultipartClient,
    ) -> None:
        """初始化上传服务。

        Args:
            upload_session_repository: 上传会话仓库
            dataset_repository: 数据集仓库
            s3_client: S3 分片上传客户端
        """
        self._upload_session_repository = upload_session_repository
        self._dataset_repository = dataset_repository
        self._s3_client = s3_client

    async def initiate_multipart_upload(
        self,
        dataset_id: int,
        filename: str,
        content_type: str,
        total_size: int,
        owner_id: int,
        part_size: int = DEFAULT_PART_SIZE,
    ) -> UploadSession:
        """初始化分片上传。

        Raises:
            DatasetNotFoundError: 数据集不存在
            UploadSessionActiveError: 数据集已有活跃上传会话
        """
        # 验证前置条件
        await self._validate_upload_prerequisites(dataset_id)

        # 创建 S3 分片上传
        s3_key = f"datasets/{dataset_id}/{filename}"
        s3_response = await self._create_s3_multipart_upload(s3_key, content_type, dataset_id, filename)

        # 创建上传会话
        session = self._create_upload_session(
            upload_id=s3_response["UploadId"],
            dataset_id=dataset_id,
            s3_key=s3_key,
            filename=filename,
            content_type=content_type,
            total_size=total_size,
            part_size=part_size,
            owner_id=owner_id,
        )

        return await self._upload_session_repository.add(session)

    async def _validate_upload_prerequisites(self, dataset_id: int) -> None:
        """验证上传前置条件."""
        # 验证数据集存在
        dataset = await self._dataset_repository.get_by_id(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id=dataset_id)

        # 检查是否有活跃上传会话
        active_session = await self._upload_session_repository.get_active_by_dataset(dataset_id)
        if active_session is not None:
            raise UploadSessionActiveError(dataset_id=dataset_id, upload_id=active_session.upload_id)

    async def _create_s3_multipart_upload(
        self, s3_key: str, content_type: str, dataset_id: int, filename: str
    ) -> dict:
        """创建 S3 分片上传."""
        return await self._s3_client.create_multipart_upload(
            key=s3_key,
            content_type=content_type,
            metadata={"filename": filename, "dataset_id": str(dataset_id)},
        )

    def _create_upload_session(
        self,
        upload_id: str,
        dataset_id: int,
        s3_key: str,
        filename: str,
        content_type: str,
        total_size: int,
        part_size: int,
        owner_id: int,
    ) -> UploadSession:
        """创建上传会话实体."""
        now = utc_now()
        return UploadSession(
            upload_id=upload_id,
            dataset_id=dataset_id,
            bucket=self._s3_client._bucket_name,
            key=s3_key,
            filename=filename,
            content_type=content_type,
            total_size=total_size,
            part_size=part_size,
            status=UploadStatus.INITIATED,
            owner_id=owner_id,
            created_at=now,
            updated_at=now,
        )

    async def generate_presigned_urls(
        self,
        upload_id: str,
        part_numbers: list[int],
        expiration: int = 3600,
    ) -> list[dict[str, Any]]:
        """生成分片上传预签名 URL。

        Args:
            upload_id: 上传会话 ID
            part_numbers: 需要上传的分片编号列表
            expiration: URL 过期时间 (秒)

        Returns:
            预签名 URL 列表 [{part_number, presigned_url}]

        Raises:
            UploadSessionNotFoundError: 上传会话不存在
        """
        session = await self._get_session_or_raise(upload_id)

        # 如果状态还是 INITIATED，更新为 IN_PROGRESS
        if session.status == UploadStatus.INITIATED:
            session.status = UploadStatus.IN_PROGRESS
            await self._upload_session_repository.update(session)

        return await self._s3_client.generate_presigned_urls_batch(
            key=session.key,
            upload_id=upload_id,
            part_numbers=part_numbers,
            expiration=expiration,
        )

    async def register_part_completion(
        self,
        upload_id: str,
        part_number: int,
        etag: str,
        size_bytes: int,
        md5_checksum: str = "",
    ) -> None:
        """注册分片完成。

        Args:
            upload_id: 上传会话 ID
            part_number: 分片编号
            etag: S3 返回的 ETag
            size_bytes: 分片大小
            md5_checksum: MD5 校验和

        Raises:
            UploadSessionNotFoundError: 上传会话不存在
        """
        session = await self._get_session_or_raise(upload_id)

        # 创建分片记录
        part = UploadPart(
            part_number=part_number,
            etag=etag,
            size_bytes=size_bytes,
            md5_checksum=md5_checksum,
            uploaded_at=utc_now(),
        )

        # 添加分片到会话
        session.add_part(part)

        # 更新会话状态
        await self._upload_session_repository.update(session)

    async def get_upload_progress(
        self,
        upload_id: str,
    ) -> dict[str, Any]:
        """获取上传进度。

        Args:
            upload_id: 上传会话 ID

        Returns:
            上传进度信息字典

        Raises:
            UploadSessionNotFoundError: 上传会话不存在
        """
        session = await self._get_session_or_raise(upload_id)

        return {
            "upload_id": session.upload_id,
            "dataset_id": session.dataset_id,
            "filename": session.filename,
            "total_size": session.total_size,
            "uploaded_bytes": session.uploaded_bytes,
            "progress_percentage": session.progress_percentage,
            "expected_part_count": session.expected_part_count,
            "completed_part_count": len(session.completed_parts),
            "missing_parts": session.missing_parts,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    async def complete_multipart_upload(self, upload_id: str) -> dict[str, Any]:
        """完成分片上传。

        Raises:
            UploadSessionNotFoundError: 上传会话不存在
            UploadIncompleteError: 上传未完成 (有缺失分片)
        """
        session = await self._get_session_or_raise(upload_id)

        # 验证完整性
        if not session.is_complete():
            raise UploadIncompleteError(upload_id=upload_id, missing_parts=session.missing_parts)

        # 标记为正在完成
        await self._update_session_status(session, UploadStatus.COMPLETING)

        # 完成 S3 上传
        response = await self._complete_s3_upload(session, upload_id)

        # 标记为已完成
        await self._update_session_status(session, UploadStatus.COMPLETED)

        # 更新数据集状态
        await self._update_dataset_status(session)

        return self._build_completion_response(session, response)

    async def _update_session_status(self, session: UploadSession, status: UploadStatus) -> None:
        """更新上传会话状态."""
        session.status = status
        await self._upload_session_repository.update(session)

    async def _complete_s3_upload(self, session: UploadSession, upload_id: str) -> dict:
        """完成 S3 分片上传."""
        parts = [
            {"PartNumber": part.part_number, "ETag": part.etag}
            for part in sorted(session.completed_parts.values(), key=lambda p: p.part_number)
        ]

        return await self._s3_client.complete_multipart_upload(
            key=session.key,
            upload_id=upload_id,
            parts=parts,
        )

    async def _update_dataset_status(self, session: UploadSession) -> None:
        """更新数据集状态为可用."""
        dataset = await self._dataset_repository.get_by_id(session.dataset_id)
        if dataset and dataset.status == DatasetStatus.PREPARING:
            dataset.status = DatasetStatus.AVAILABLE
            dataset.total_size_bytes = session.total_size
            await self._dataset_repository.update(dataset)

    def _build_completion_response(self, session: UploadSession, s3_response: dict) -> dict[str, Any]:
        """构建完成响应."""
        return {
            "etag": s3_response.get("ETag"),
            "location": s3_response.get("Location"),
            "bucket": session.bucket,
            "key": session.key,
            "size": session.total_size,
        }

    async def abort_multipart_upload(
        self,
        upload_id: str,
    ) -> None:
        """取消分片上传。

        Args:
            upload_id: 上传会话 ID

        Raises:
            UploadSessionNotFoundError: 上传会话不存在
        """
        session = await self._get_session_or_raise(upload_id)

        # 调用 S3 取消上传
        await self._s3_client.abort_multipart_upload(
            key=session.key,
            upload_id=upload_id,
        )

        # 更新会话状态
        session.status = UploadStatus.ABORTED
        await self._upload_session_repository.update(session)

    async def _get_session_or_raise(self, upload_id: str) -> UploadSession:
        """获取上传会话或抛出异常。"""
        session = await self._upload_session_repository.get_by_upload_id(upload_id)
        if session is None:
            raise UploadSessionNotFoundError(upload_id=upload_id)
        return session
