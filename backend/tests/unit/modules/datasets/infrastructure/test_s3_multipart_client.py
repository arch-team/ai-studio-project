"""测试 S3 Multipart Upload 客户端。

使用 aioboto3 async mock 模式。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestS3MultipartClientInit:
    """测试 S3MultipartClient 初始化。"""

    def test_init_with_bucket_and_region(self) -> None:
        """验证使用 bucket 和 region 初始化。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            assert client._bucket_name == "test-bucket"
            assert client._region == "us-west-2"
            assert client._session == mock_session


class TestS3MultipartClientCreateMultipartUpload:
    """测试 create_multipart_upload 方法。"""

    @pytest.fixture
    def mock_s3_client(self) -> AsyncMock:
        """创建 mock S3 客户端。"""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self, mock_s3_client: AsyncMock) -> MagicMock:
        """创建 mock aioboto3 Session。"""
        mock_session = MagicMock()
        context_manager = AsyncMock()
        context_manager.__aenter__.return_value = mock_s3_client
        context_manager.__aexit__.return_value = None
        mock_session.client.return_value = context_manager
        return mock_session

    @pytest.mark.asyncio
    async def test_create_multipart_upload_success(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证成功创建分片上传。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "upload-123",
            "Bucket": "test-bucket",
            "Key": "datasets/1/data.tar",
        }

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            result = await client.create_multipart_upload(
                key="datasets/1/data.tar",
                content_type="application/x-tar",
                metadata={"filename": "data.tar"},
            )

            assert result["UploadId"] == "upload-123"
            mock_s3_client.create_multipart_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_multipart_upload_with_kms(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证使用 KMS 加密创建分片上传。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "upload-456",
        }

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
                kms_key_id="arn:aws:kms:us-west-2:123456789012:key/xxx",
            )

            await client.create_multipart_upload(
                key="datasets/1/data.tar",
                content_type="application/x-tar",
            )

            call_args = mock_s3_client.create_multipart_upload.call_args
            assert call_args.kwargs.get("ServerSideEncryption") == "aws:kms"


class TestS3MultipartClientGeneratePresignedUrl:
    """测试 generate_presigned_url_for_part 方法。"""

    @pytest.fixture
    def mock_s3_client(self) -> AsyncMock:
        """创建 mock S3 客户端。"""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self, mock_s3_client: AsyncMock) -> MagicMock:
        """创建 mock aioboto3 Session。"""
        mock_session = MagicMock()
        context_manager = AsyncMock()
        context_manager.__aenter__.return_value = mock_s3_client
        context_manager.__aexit__.return_value = None
        mock_session.client.return_value = context_manager
        return mock_session

    @pytest.mark.asyncio
    async def test_generate_presigned_url_for_part(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证生成分片上传预签名 URL。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            url = await client.generate_presigned_url_for_part(
                key="datasets/1/data.tar",
                upload_id="upload-123",
                part_number=1,
                expiration=3600,
            )

            assert url == "https://s3.example.com/presigned"
            mock_s3_client.generate_presigned_url.assert_called_once_with(
                "upload_part",
                Params={
                    "Bucket": "test-bucket",
                    "Key": "datasets/1/data.tar",
                    "UploadId": "upload-123",
                    "PartNumber": 1,
                },
                ExpiresIn=3600,
            )

    @pytest.mark.asyncio
    async def test_generate_presigned_urls_batch(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证批量生成预签名 URL。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            urls = await client.generate_presigned_urls_batch(
                key="datasets/1/data.tar",
                upload_id="upload-123",
                part_numbers=[1, 2, 3],
                expiration=3600,
            )

            assert len(urls) == 3
            assert mock_s3_client.generate_presigned_url.call_count == 3


class TestS3MultipartClientCompleteUpload:
    """测试 complete_multipart_upload 方法。"""

    @pytest.fixture
    def mock_s3_client(self) -> AsyncMock:
        """创建 mock S3 客户端。"""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self, mock_s3_client: AsyncMock) -> MagicMock:
        """创建 mock aioboto3 Session。"""
        mock_session = MagicMock()
        context_manager = AsyncMock()
        context_manager.__aenter__.return_value = mock_s3_client
        context_manager.__aexit__.return_value = None
        mock_session.client.return_value = context_manager
        return mock_session

    @pytest.mark.asyncio
    async def test_complete_multipart_upload_success(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证成功完成分片上传。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        mock_s3_client.complete_multipart_upload.return_value = {
            "Location": "https://test-bucket.s3.amazonaws.com/datasets/1/data.tar",
            "Bucket": "test-bucket",
            "Key": "datasets/1/data.tar",
            "ETag": '"abc123-5"',
        }

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            parts = [
                {"PartNumber": 1, "ETag": '"etag1"'},
                {"PartNumber": 2, "ETag": '"etag2"'},
            ]

            result = await client.complete_multipart_upload(
                key="datasets/1/data.tar",
                upload_id="upload-123",
                parts=parts,
            )

            assert result["ETag"] == '"abc123-5"'
            mock_s3_client.complete_multipart_upload.assert_called_once()


class TestS3MultipartClientAbortUpload:
    """测试 abort_multipart_upload 方法。"""

    @pytest.fixture
    def mock_s3_client(self) -> AsyncMock:
        """创建 mock S3 客户端。"""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self, mock_s3_client: AsyncMock) -> MagicMock:
        """创建 mock aioboto3 Session。"""
        mock_session = MagicMock()
        context_manager = AsyncMock()
        context_manager.__aenter__.return_value = mock_s3_client
        context_manager.__aexit__.return_value = None
        mock_session.client.return_value = context_manager
        return mock_session

    @pytest.mark.asyncio
    async def test_abort_multipart_upload_success(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证成功取消分片上传。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        mock_s3_client.abort_multipart_upload.return_value = {}

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            await client.abort_multipart_upload(
                key="datasets/1/data.tar",
                upload_id="upload-123",
            )

            mock_s3_client.abort_multipart_upload.assert_called_once_with(
                Bucket="test-bucket",
                Key="datasets/1/data.tar",
                UploadId="upload-123",
            )


class TestS3MultipartClientListParts:
    """测试 list_parts 方法。"""

    @pytest.fixture
    def mock_s3_client(self) -> AsyncMock:
        """创建 mock S3 客户端。"""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self, mock_s3_client: AsyncMock) -> MagicMock:
        """创建 mock aioboto3 Session。"""
        mock_session = MagicMock()
        context_manager = AsyncMock()
        context_manager.__aenter__.return_value = mock_s3_client
        context_manager.__aexit__.return_value = None
        mock_session.client.return_value = context_manager
        return mock_session

    @pytest.mark.asyncio
    async def test_list_parts_returns_parts(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证列出已上传分片。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        mock_s3_client.list_parts.return_value = {
            "Parts": [
                {"PartNumber": 1, "ETag": '"etag1"', "Size": 100000000},
                {"PartNumber": 2, "ETag": '"etag2"', "Size": 100000000},
            ],
            "IsTruncated": False,
        }

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            parts = await client.list_parts(
                key="datasets/1/data.tar",
                upload_id="upload-123",
            )

            assert len(parts) == 2
            assert parts[0]["PartNumber"] == 1

    @pytest.mark.asyncio
    async def test_list_parts_handles_pagination(
        self, mock_session: MagicMock, mock_s3_client: AsyncMock
    ) -> None:
        """验证处理分页的分片列表。"""
        from src.modules.datasets.infrastructure.s3 import S3MultipartClient

        # 模拟两次调用（分页）
        mock_s3_client.list_parts.side_effect = [
            {
                "Parts": [{"PartNumber": 1, "ETag": '"etag1"', "Size": 100000000}],
                "IsTruncated": True,
                "NextPartNumberMarker": 1,
            },
            {
                "Parts": [{"PartNumber": 2, "ETag": '"etag2"', "Size": 100000000}],
                "IsTruncated": False,
            },
        ]

        with patch("aioboto3.Session", return_value=mock_session):
            client = S3MultipartClient(
                bucket_name="test-bucket",
                region="us-west-2",
            )

            parts = await client.list_parts(
                key="datasets/1/data.tar",
                upload_id="upload-123",
            )

            assert len(parts) == 2


class TestS3MultipartClientPartSize:
    """测试分片大小常量。"""

    def test_default_part_size(self) -> None:
        """验证默认分片大小为 100MB。"""
        from src.modules.datasets.infrastructure.s3 import (
            DEFAULT_PART_SIZE,
            MAX_PARTS,
            MIN_PART_SIZE,
        )

        assert DEFAULT_PART_SIZE == 100 * 1024 * 1024  # 100MB
        assert MIN_PART_SIZE == 5 * 1024 * 1024  # 5MB (S3 最小)
        assert MAX_PARTS == 10000  # S3 限制
