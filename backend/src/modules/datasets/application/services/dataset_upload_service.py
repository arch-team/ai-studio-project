"""Dataset Upload Service - 数据集上传业务逻辑。

提供 S3 分片上传的完整流程:
- 初始化分片上传
- 生成预签名 URL
- 注册分片完成
- 获取上传进度
- 完成/取消上传

支持断点续传 (通过数据库持久化 UploadSession)。
"""

from datetime import datetime, timedelta
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

        Args:
            dataset_id: 数据集 ID
            filename: 原始文件名
            content_type: MIME 类型
            total_size: 文件总大小 (字节)
            owner_id: 上传者用户 ID
            part_size: 分片大小 (字节)

        Returns:
            创建的上传会话

        Raises:
            DatasetNotFoundError: 数据集不存在
            UploadSessionActiveError: 数据集已有活跃上传会话
        """
        # 验证数据集和会话
        await self._validate_dataset_and_session(dataset_id)

        # 构建 S3 key 并创建分片上传
        s3_key = self._build_s3_key(dataset_id, filename)
        response = await self._s3_client.create_multipart_upload(
            key=s3_key,
            content_type=content_type,
            metadata={"filename": filename, "dataset_id": str(dataset_id)},
        )

        # 创建并持久化会话
        session = self._create_upload_session(
            upload_id=response["UploadId"],
            dataset_id=dataset_id,
            s3_key=s3_key,
            filename=filename,
            content_type=content_type,
            total_size=total_size,
            part_size=part_size,
            owner_id=owner_id,
        )
        return await self._upload_session_repository.add(session)

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

    async def complete_multipart_upload(
        self,
        upload_id: str,
    ) -> dict[str, Any]:
        """完成分片上传。

        Args:
            upload_id: 上传会话 ID

        Returns:
            完成结果 {etag, location, size}

        Raises:
            UploadSessionNotFoundError: 上传会话不存在
            UploadIncompleteError: 上传未完成 (有缺失分片)
        """
        session = await self._get_session_or_raise(upload_id)

        # 验证所有分片都已上传完成
        if not session.is_complete():
            raise UploadIncompleteError(
                upload_id=upload_id,
                missing_parts=session.missing_parts,
            )

        # 更新状态为 COMPLETING
        session.status = UploadStatus.COMPLETING
        await self._upload_session_repository.update(session)

        # 构建分片列表（按分片编号排序）
        parts = [
            {"PartNumber": part.part_number, "ETag": part.etag}
            for part in sorted(
                session.completed_parts.values(),
                key=lambda p: p.part_number,
            )
        ]

        # 调用 S3 完成上传
        response = await self._s3_client.complete_multipart_upload(
            key=session.key,
            upload_id=upload_id,
            parts=parts,
        )

        # 更新会话状态为 COMPLETED
        session.status = UploadStatus.COMPLETED
        await self._upload_session_repository.update(session)

        # 更新数据集状态为 AVAILABLE
        dataset = await self._dataset_repository.get_by_id(session.dataset_id)
        if dataset and dataset.status == DatasetStatus.PREPARING:
            dataset.status = DatasetStatus.AVAILABLE
            dataset.total_size_bytes = session.total_size
            await self._dataset_repository.update(dataset)

        return {
            "etag": response.get("ETag"),
            "location": response.get("Location"),
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

    async def _validate_dataset_and_session(self, dataset_id: int) -> None:
        """验证数据集存在且没有活跃会话。

        Args:
            dataset_id: 数据集 ID

        Raises:
            DatasetNotFoundError: 数据集不存在
            UploadSessionActiveError: 已有活跃上传会话
        """
        # 验证数据集存在
        dataset = await self._dataset_repository.get_by_id(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id=dataset_id)

        # 检查是否有活跃上传会话
        active_session = await self._upload_session_repository.get_active_by_dataset(
            dataset_id
        )
        if active_session is not None:
            raise UploadSessionActiveError(
                dataset_id=dataset_id,
                upload_id=active_session.upload_id,
            )

    def _build_s3_key(self, dataset_id: int, filename: str) -> str:
        """构建 S3 对象键。"""
        return f"datasets/{dataset_id}/{filename}"

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
        """创建上传会话对象。"""
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
