"""S3 Multipart Upload Client - 分片上传客户端。

提供 S3 分片上传的完整功能:
- 初始化分片上传
- 生成分片上传预签名 URL
- 完成分片上传
- 取消分片上传
- 列出已上传分片

支持 FR-006 (≥100MB/s 上传速度) 和 FR-007 (≥10TB 数据集)。
使用 aioboto3 原生异步，与 S3StorageClient 保持一致。
"""

import asyncio
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

# 分片大小常量（用于优化上传性能）
DEFAULT_PART_SIZE = 100 * 1024 * 1024  # 100MB (满足 FR-006：≥100MB/s 上传速度)
MIN_PART_SIZE = 5 * 1024 * 1024  # 5MB (S3 最小分片大小限制)
MAX_PARTS = 10000  # S3 最大分片数限制 → 支持最大 1PB 文件 (100MB × 10000)


class S3MultipartUploadError(Exception):
    """S3 分片上传错误基类。"""

    pass


class S3MultipartClient:
    """S3 分片上传客户端。

    封装 aioboto3 S3 客户端，提供原生异步分片上传操作。
    每个操作使用 async with 创建临时客户端 (aioboto3 推荐模式)。
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-west-2",
        kms_key_id: str | None = None,
    ) -> None:
        """初始化 S3 分片上传客户端。

        Args:
            bucket_name: S3 桶名
            region: AWS 区域
            kms_key_id: 可选的 KMS 密钥 ID (用于 SSE-KMS 加密)
        """
        self._bucket_name = bucket_name
        self._region = region
        self._kms_key_id = kms_key_id
        self._session = aioboto3.Session()

    async def create_multipart_upload(
        self,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """初始化分片上传。

        Args:
            key: S3 对象键
            content_type: MIME 类型
            metadata: 可选的用户元数据

        Returns:
            包含 UploadId 的响应字典

        Raises:
            S3MultipartUploadError: 创建失败时
        """
        params = self._build_upload_params(key, content_type, metadata)

        try:
            async with self._session.client("s3", region_name=self._region) as s3:
                return await s3.create_multipart_upload(**params)
        except ClientError as e:
            raise S3MultipartUploadError(f"Failed to create multipart upload: {e}") from e

    async def generate_presigned_url_for_part(
        self,
        key: str,
        upload_id: str,
        part_number: int,
        expiration: int = 3600,
    ) -> str:
        """生成单个分片上传的预签名 URL。

        Args:
            key: S3 对象键
            upload_id: 分片上传 ID
            part_number: 分片编号 (1-10000)
            expiration: URL 过期时间 (秒)

        Returns:
            预签名 URL
        """
        async with self._session.client("s3", region_name=self._region) as s3:
            return await s3.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": self._bucket_name,
                    "Key": key,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=expiration,
            )

    async def generate_presigned_urls_batch(
        self,
        key: str,
        upload_id: str,
        part_numbers: list[int],
        expiration: int = 3600,
    ) -> list[dict[str, Any]]:
        """批量生成分片上传预签名 URL。

        Args:
            key: S3 对象键
            upload_id: 分片上传 ID
            part_numbers: 分片编号列表
            expiration: URL 过期时间 (秒)

        Returns:
            包含 part_number 和 presigned_url 的字典列表
        """
        tasks = [
            self.generate_presigned_url_for_part(key, upload_id, pn, expiration)
            for pn in part_numbers
        ]
        urls = await asyncio.gather(*tasks)

        return [
            {"part_number": pn, "presigned_url": url}
            for pn, url in zip(part_numbers, urls)
        ]

    async def complete_multipart_upload(
        self,
        key: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """完成分片上传。

        Args:
            key: S3 对象键
            upload_id: 分片上传 ID
            parts: 已完成分片列表，每项包含 PartNumber 和 ETag

        Returns:
            完成响应，包含 Location, Bucket, Key, ETag

        Raises:
            S3MultipartUploadError: 完成失败时
        """
        # 按分片编号排序（S3 API 要求分片必须按顺序提交）
        sorted_parts = sorted(parts, key=lambda x: x["PartNumber"])

        try:
            async with self._session.client("s3", region_name=self._region) as s3:
                return await s3.complete_multipart_upload(
                    Bucket=self._bucket_name,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": sorted_parts},
                )
        except ClientError as e:
            raise S3MultipartUploadError(f"Failed to complete multipart upload: {e}") from e

    async def abort_multipart_upload(
        self,
        key: str,
        upload_id: str,
    ) -> None:
        """取消分片上传。

        Args:
            key: S3 对象键
            upload_id: 分片上传 ID

        Raises:
            S3MultipartUploadError: 取消失败时
        """
        try:
            async with self._session.client("s3", region_name=self._region) as s3:
                await s3.abort_multipart_upload(
                    Bucket=self._bucket_name,
                    Key=key,
                    UploadId=upload_id,
                )
        except ClientError as e:
            raise S3MultipartUploadError(f"Failed to abort multipart upload: {e}") from e

    async def list_parts(
        self,
        key: str,
        upload_id: str,
        max_parts: int = 1000,
    ) -> list[dict[str, Any]]:
        """列出已上传的分片。

        自动处理分页，返回所有分片。

        Args:
            key: S3 对象键
            upload_id: 分片上传 ID
            max_parts: 每次请求的最大分片数

        Returns:
            分片列表，每项包含 PartNumber, ETag, Size 等

        Raises:
            S3MultipartUploadError: 列表失败时
        """
        all_parts: list[dict[str, Any]] = []
        part_number_marker: int | None = None

        try:
            async with self._session.client("s3", region_name=self._region) as s3:
                # 循环获取所有分页结果
                while True:
                    params: dict[str, Any] = {
                        "Bucket": self._bucket_name,
                        "Key": key,
                        "UploadId": upload_id,
                        "MaxParts": max_parts,
                    }

                    if part_number_marker is not None:
                        params["PartNumberMarker"] = part_number_marker

                    response = await s3.list_parts(**params)
                    all_parts.extend(response.get("Parts", []))

                    if not response.get("IsTruncated", False):
                        break

                    part_number_marker = response.get("NextPartNumberMarker")

        except ClientError as e:
            raise S3MultipartUploadError(f"Failed to list parts: {e}") from e

        return all_parts

    async def head_object(self, key: str) -> dict[str, Any]:
        """获取对象元数据 (用于验证上传完成)。

        Args:
            key: S3 对象键

        Returns:
            对象元数据

        Raises:
            S3MultipartUploadError: 对象不存在或请求失败时
        """
        try:
            async with self._session.client("s3", region_name=self._region) as s3:
                return await s3.head_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )
        except ClientError as e:
            raise S3MultipartUploadError(f"Failed to get object metadata: {e}") from e

    # ========== 私有辅助方法 ==========

    def _build_upload_params(
        self,
        key: str,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """构建上传参数。"""
        params: dict[str, Any] = {
            "Bucket": self._bucket_name,
            "Key": key,
            "ContentType": content_type,
        }

        if metadata:
            params["Metadata"] = metadata

        if self._kms_key_id:
            params["ServerSideEncryption"] = "aws:kms"
            params["SSEKMSKeyId"] = self._kms_key_id

        return params
