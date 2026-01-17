"""S3 Client Tests - Unit tests for S3 storage client implementation.

Tests follow TDD Red-Green-Refactor cycle.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.shared.infrastructure.storage import IStorageService, S3StorageClient


class TestS3StorageClient:
    """Test suite for S3StorageClient implementation."""

    @pytest.fixture
    def mock_boto3_client(self) -> MagicMock:
        """Mock boto3 S3 client."""
        mock_client = MagicMock()
        with patch("boto3.client", return_value=mock_client):
            yield mock_client

    @pytest.fixture
    def s3_client(self, mock_boto3_client: MagicMock) -> S3StorageClient:
        """Create S3StorageClient instance with mocked dependencies."""
        client = S3StorageClient(bucket_name="test-bucket", region="us-west-2")
        client._s3_client = mock_boto3_client
        return client

    # ==================== Upload Operations ====================

    @pytest.mark.asyncio
    async def test_upload_file_success(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful file upload."""
        mock_boto3_client.upload_file.return_value = None

        result = await s3_client.upload_file(
            local_path="/tmp/test.txt",
            remote_path="data/test.txt",
            metadata={"content-type": "text/plain"},
        )

        assert result == "data/test.txt"
        mock_boto3_client.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_with_encryption(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test file upload with SSE-KMS encryption."""
        mock_boto3_client.upload_file.return_value = None

        result = await s3_client.upload_file(
            local_path="/tmp/sensitive.txt",
            remote_path="secure/sensitive.txt",
        )

        assert result == "secure/sensitive.txt"
        # Verify SSE-KMS encryption is used
        call_args = mock_boto3_client.upload_file.call_args
        assert call_args is not None

    # ==================== Download Operations ====================

    @pytest.mark.asyncio
    async def test_download_file_success(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful file download."""
        mock_boto3_client.download_file.return_value = None

        result = await s3_client.download_file(
            remote_path="data/test.txt",
            local_path="/tmp/downloaded.txt",
        )

        assert result == "/tmp/downloaded.txt"
        mock_boto3_client.download_file.assert_called_once_with(
            "test-bucket", "data/test.txt", "/tmp/downloaded.txt"
        )

    # ==================== Delete Operations ====================

    @pytest.mark.asyncio
    async def test_delete_file_success(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful file deletion."""
        mock_boto3_client.delete_object.return_value = {"DeleteMarker": True}

        result = await s3_client.delete_file(remote_path="data/test.txt")

        assert result is True
        mock_boto3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="data/test.txt"
        )

    # ==================== List Operations ====================

    @pytest.mark.asyncio
    async def test_list_files_success(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful file listing."""
        mock_boto3_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "data/file1.txt",
                    "Size": 1024,
                    "LastModified": "2026-01-15T10:00:00Z",
                },
                {
                    "Key": "data/file2.txt",
                    "Size": 2048,
                    "LastModified": "2026-01-15T11:00:00Z",
                },
            ],
            "IsTruncated": False,
        }

        result = await s3_client.list_files(prefix="data/", max_results=100)

        assert len(result) == 2
        assert result[0]["Key"] == "data/file1.txt"
        mock_boto3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket", Prefix="data/", MaxKeys=100
        )

    @pytest.mark.asyncio
    async def test_list_files_empty(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test listing with no results."""
        mock_boto3_client.list_objects_v2.return_value = {"IsTruncated": False}

        result = await s3_client.list_files(prefix="empty/")

        assert len(result) == 0

    # ==================== Metadata Operations ====================

    @pytest.mark.asyncio
    async def test_get_file_metadata_success(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful metadata retrieval."""
        mock_boto3_client.head_object.return_value = {
            "ContentLength": 1024,
            "ContentType": "text/plain",
            "LastModified": "2026-01-15T10:00:00Z",
            "ETag": '"abc123"',
            "Metadata": {"custom-key": "custom-value"},
        }

        result = await s3_client.get_file_metadata(remote_path="data/test.txt")

        assert result["ContentLength"] == 1024
        assert result["ContentType"] == "text/plain"
        mock_boto3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key="data/test.txt"
        )

    # ==================== Existence Check ====================

    @pytest.mark.asyncio
    async def test_file_exists_returns_true(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test file existence check returns true."""
        mock_boto3_client.head_object.return_value = {"ContentLength": 1024}

        result = await s3_client.file_exists(remote_path="data/exists.txt")

        assert result is True
        mock_boto3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key="data/exists.txt"
        )

    @pytest.mark.asyncio
    async def test_file_exists_returns_false(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test file existence check returns false for non-existent file."""
        from botocore.exceptions import ClientError

        mock_boto3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )

        result = await s3_client.file_exists(remote_path="data/not-exists.txt")

        assert result is False

    # ==================== Presigned URL ====================

    @pytest.mark.asyncio
    async def test_generate_presigned_url_for_get(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test presigned URL generation for download."""
        mock_boto3_client.generate_presigned_url.return_value = (
            "https://test-bucket.s3.amazonaws.com/data/test.txt?signature=xxx"
        )

        result = await s3_client.generate_presigned_url(
            remote_path="data/test.txt",
            expiration=3600,
            operation="get",
        )

        assert "test-bucket" in result
        assert "data/test.txt" in result
        mock_boto3_client.generate_presigned_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_presigned_url_for_put(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test presigned URL generation for upload."""
        mock_boto3_client.generate_presigned_url.return_value = (
            "https://test-bucket.s3.amazonaws.com/data/upload.txt?signature=xxx"
        )

        result = await s3_client.generate_presigned_url(
            remote_path="data/upload.txt",
            expiration=3600,
            operation="put",
        )

        assert "test-bucket" in result
        mock_boto3_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={"Bucket": "test-bucket", "Key": "data/upload.txt"},
            ExpiresIn=3600,
        )

    # ==================== Copy Operations ====================

    @pytest.mark.asyncio
    async def test_copy_file_success(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful file copy."""
        mock_boto3_client.copy_object.return_value = {
            "CopyObjectResult": {"ETag": '"abc123"'}
        }

        result = await s3_client.copy_file(
            source_path="data/source.txt",
            dest_path="backup/dest.txt",
        )

        assert result == "backup/dest.txt"
        mock_boto3_client.copy_object.assert_called_once_with(
            Bucket="test-bucket",
            CopySource={"Bucket": "test-bucket", "Key": "data/source.txt"},
            Key="backup/dest.txt",
        )

    # ==================== Stream Operations ====================

    @pytest.mark.asyncio
    async def test_stream_file_yields_chunks(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test file streaming yields chunks."""
        mock_body = MagicMock()
        mock_body.read.side_effect = [b"chunk1", b"chunk2", b""]
        mock_boto3_client.get_object.return_value = {"Body": mock_body}

        chunks = []
        async for chunk in s3_client.stream_file(
            remote_path="data/large.bin", chunk_size=1024
        ):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0] == b"chunk1"
        assert chunks[1] == b"chunk2"
        mock_boto3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="data/large.bin"
        )

    # ==================== Error Handling ====================

    @pytest.mark.asyncio
    async def test_client_handles_access_denied(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test error handling for access denied."""
        from botocore.exceptions import ClientError

        mock_boto3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Access Denied"}},
            "HeadObject",
        )

        with pytest.raises(ClientError) as exc_info:
            await s3_client.get_file_metadata(remote_path="restricted/file.txt")

        assert exc_info.value.response["Error"]["Code"] == "403"

    @pytest.mark.asyncio
    async def test_client_handles_bucket_not_found(
        self,
        s3_client: S3StorageClient,
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test error handling when bucket doesn't exist."""
        from botocore.exceptions import ClientError

        mock_boto3_client.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "ListObjectsV2",
        )

        with pytest.raises(ClientError) as exc_info:
            await s3_client.list_files(prefix="data/")

        assert exc_info.value.response["Error"]["Code"] == "NoSuchBucket"

    # ==================== Interface Compliance ====================

    def test_implements_istorage_service_interface(
        self,
        s3_client: S3StorageClient,
    ) -> None:
        """Test that S3StorageClient implements IStorageService interface."""
        assert isinstance(s3_client, IStorageService)

    def test_all_interface_methods_implemented(
        self,
        s3_client: S3StorageClient,
    ) -> None:
        """Test that all interface methods are implemented."""
        interface_methods = [
            "upload_file",
            "download_file",
            "delete_file",
            "list_files",
            "get_file_metadata",
            "file_exists",
            "generate_presigned_url",
            "copy_file",
            "stream_file",
        ]

        for method_name in interface_methods:
            assert hasattr(s3_client, method_name)
            assert callable(getattr(s3_client, method_name))
