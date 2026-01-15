"""S3 Integration Tests - Real AWS environment validation.

These tests require actual AWS credentials and S3 bucket access.
Run with: pytest -m aws_integration tests/integration/aws/test_s3_integration.py -v
"""

import os
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio

from src.infrastructure.external.s3.client import S3StorageClient

pytestmark = [
    pytest.mark.aws_integration,
    pytest.mark.slow,
]


def aws_credentials_available() -> bool:
    """Check if AWS credentials are configured."""
    import boto3

    try:
        boto3.client("sts").get_caller_identity()
        return True
    except Exception:
        return False


def s3_test_bucket_configured() -> bool:
    """Check if S3 test bucket is configured."""
    return bool(os.environ.get("S3_TEST_BUCKET"))


skip_without_aws = pytest.mark.skipif(
    not aws_credentials_available(), reason="AWS credentials not available"
)

skip_without_bucket = pytest.mark.skipif(
    not s3_test_bucket_configured(), reason="S3_TEST_BUCKET not configured"
)


@pytest.fixture
def test_bucket_name() -> str:
    """Get test bucket name from environment."""
    return os.environ.get("S3_TEST_BUCKET", "ai-training-platform-integration-test")


@pytest.fixture
def test_prefix() -> str:
    """Generate unique test prefix to avoid conflicts."""
    unique_id = uuid.uuid4().hex[:8]
    return f"integration-tests/{unique_id}/"


@pytest.fixture
def kms_key_id() -> str | None:
    """Get KMS key ID for encryption tests."""
    return os.environ.get("S3_TEST_KMS_KEY_ID")


@pytest_asyncio.fixture
async def s3_client(test_bucket_name: str, kms_key_id: str | None) -> S3StorageClient:
    """Create S3 client for integration tests."""
    region = os.environ.get("AWS_REGION", "us-west-2")
    return S3StorageClient(
        bucket_name=test_bucket_name,
        region=region,
        kms_key_id=kms_key_id,
    )


@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    """Create sample text file for upload tests."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Hello, AWS S3 Integration Test!")
    return file_path


@pytest.fixture
def sample_binary_file(tmp_path: Path) -> Path:
    """Create sample binary file for upload tests."""
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(os.urandom(1024 * 10))
    return file_path


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_files(
    s3_client: S3StorageClient, test_prefix: str
) -> AsyncGenerator[None, None]:
    """Auto-cleanup: remove all test files after each test."""
    yield

    try:
        files = await s3_client.list_files(prefix=test_prefix, max_results=1000)
        for file_info in files:
            key = file_info.get("Key")
            if key:
                await s3_client.delete_file(key)
    except Exception as e:
        print(f"Warning: cleanup failed: {e}")


class TestS3Upload:
    """Test S3 file upload operations."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_upload_text_file_success(
        self,
        s3_client: S3StorageClient,
        sample_text_file: Path,
        test_prefix: str,
    ) -> None:
        """Test uploading a text file to S3."""
        remote_path = f"{test_prefix}text-file.txt"

        result = await s3_client.upload_file(
            local_path=str(sample_text_file),
            remote_path=remote_path,
            metadata={"content-type": "text/plain", "test-run": "true"},
        )

        assert result == remote_path
        exists = await s3_client.file_exists(remote_path)
        assert exists is True

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_upload_binary_file_success(
        self,
        s3_client: S3StorageClient,
        sample_binary_file: Path,
        test_prefix: str,
    ) -> None:
        """Test uploading a binary file to S3."""
        remote_path = f"{test_prefix}binary-file.bin"

        result = await s3_client.upload_file(
            local_path=str(sample_binary_file),
            remote_path=remote_path,
        )

        assert result == remote_path
        metadata = await s3_client.get_file_metadata(remote_path)
        assert metadata["ContentLength"] == sample_binary_file.stat().st_size

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_upload_with_sse_kms_encryption(
        self,
        s3_client: S3StorageClient,
        sample_text_file: Path,
        test_prefix: str,
        kms_key_id: str | None,
    ) -> None:
        """Test uploading with SSE-KMS encryption."""
        if not kms_key_id:
            pytest.skip("KMS key not configured")

        remote_path = f"{test_prefix}encrypted-file.txt"

        result = await s3_client.upload_file(
            local_path=str(sample_text_file),
            remote_path=remote_path,
        )

        assert result == remote_path
        metadata = await s3_client.get_file_metadata(remote_path)
        assert metadata.get("ServerSideEncryption") == "aws:kms"


class TestS3Download:
    """Test S3 file download operations."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_download_file_success(
        self,
        s3_client: S3StorageClient,
        sample_text_file: Path,
        test_prefix: str,
        tmp_path: Path,
    ) -> None:
        """Test downloading a file from S3."""
        remote_path = f"{test_prefix}download-test.txt"

        await s3_client.upload_file(
            local_path=str(sample_text_file),
            remote_path=remote_path,
        )

        local_download_path = tmp_path / "downloaded.txt"
        result = await s3_client.download_file(
            remote_path=remote_path,
            local_path=str(local_download_path),
        )

        assert result == str(local_download_path)
        assert local_download_path.exists()
        assert local_download_path.read_text() == sample_text_file.read_text()

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_download_preserves_binary_content(
        self,
        s3_client: S3StorageClient,
        sample_binary_file: Path,
        test_prefix: str,
        tmp_path: Path,
    ) -> None:
        """Test binary file integrity after round-trip."""
        remote_path = f"{test_prefix}binary-download.bin"
        original_content = sample_binary_file.read_bytes()

        await s3_client.upload_file(
            local_path=str(sample_binary_file),
            remote_path=remote_path,
        )

        local_download_path = tmp_path / "downloaded.bin"
        await s3_client.download_file(
            remote_path=remote_path,
            local_path=str(local_download_path),
        )

        downloaded_content = local_download_path.read_bytes()
        assert downloaded_content == original_content


class TestS3Delete:
    """Test S3 file deletion operations."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_delete_file_success(
        self,
        s3_client: S3StorageClient,
        sample_text_file: Path,
        test_prefix: str,
    ) -> None:
        """Test deleting a file from S3."""
        remote_path = f"{test_prefix}to-delete.txt"

        await s3_client.upload_file(
            local_path=str(sample_text_file),
            remote_path=remote_path,
        )

        assert await s3_client.file_exists(remote_path) is True

        result = await s3_client.delete_file(remote_path)
        assert result is True

        assert await s3_client.file_exists(remote_path) is False

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_idempotent(
        self,
        s3_client: S3StorageClient,
        test_prefix: str,
    ) -> None:
        """Test deleting a non-existent file (should be idempotent)."""
        remote_path = f"{test_prefix}nonexistent-file.txt"

        result = await s3_client.delete_file(remote_path)
        assert result is True


class TestS3List:
    """Test S3 file listing operations."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_list_files_with_prefix(
        self,
        s3_client: S3StorageClient,
        sample_text_file: Path,
        test_prefix: str,
    ) -> None:
        """Test listing files with a prefix."""
        files_to_upload = ["file1.txt", "file2.txt", "subdir/file3.txt"]

        for filename in files_to_upload:
            remote_path = f"{test_prefix}{filename}"
            await s3_client.upload_file(
                local_path=str(sample_text_file),
                remote_path=remote_path,
            )

        result = await s3_client.list_files(prefix=test_prefix, max_results=100)

        assert len(result) == 3
        listed_keys = [f["Key"] for f in result]
        for filename in files_to_upload:
            assert f"{test_prefix}{filename}" in listed_keys

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_list_empty_prefix_returns_empty(
        self,
        s3_client: S3StorageClient,
        test_prefix: str,
    ) -> None:
        """Test listing with no matching files."""
        result = await s3_client.list_files(
            prefix=f"{test_prefix}nonexistent/", max_results=100
        )

        assert len(result) == 0


class TestS3PresignedUrl:
    """Test S3 presigned URL generation."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_presigned_url_for_download(
        self,
        s3_client: S3StorageClient,
        sample_text_file: Path,
        test_prefix: str,
    ) -> None:
        """Test generating presigned URL for download."""
        import httpx

        remote_path = f"{test_prefix}presigned-download.txt"
        original_content = sample_text_file.read_text()

        await s3_client.upload_file(
            local_path=str(sample_text_file),
            remote_path=remote_path,
        )

        url = await s3_client.generate_presigned_url(
            remote_path=remote_path,
            expiration=300,
            operation="get",
        )

        assert url.startswith("https://")
        # URL may use V2 (Signature) or V4 (X-Amz-Signature) signing
        assert "Signature" in url or "X-Amz-Signature" in url

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url)
            assert response.status_code == 200
            assert response.text == original_content

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_presigned_url_for_upload(
        self,
        s3_client: S3StorageClient,
        test_prefix: str,
    ) -> None:
        """Test generating presigned URL for upload."""
        import httpx

        remote_path = f"{test_prefix}presigned-upload.txt"
        test_content = "Uploaded via presigned URL"

        url = await s3_client.generate_presigned_url(
            remote_path=remote_path,
            expiration=300,
            operation="put",
        )

        assert url.startswith("https://")

        async with httpx.AsyncClient() as http_client:
            response = await http_client.put(url, content=test_content.encode())
            assert response.status_code == 200

        assert await s3_client.file_exists(remote_path) is True


class TestS3Copy:
    """Test S3 file copy operations."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_copy_file_success(
        self,
        s3_client: S3StorageClient,
        sample_text_file: Path,
        test_prefix: str,
    ) -> None:
        """Test copying a file within S3."""
        source_path = f"{test_prefix}source.txt"
        dest_path = f"{test_prefix}destination.txt"

        await s3_client.upload_file(
            local_path=str(sample_text_file),
            remote_path=source_path,
        )

        result = await s3_client.copy_file(
            source_path=source_path,
            dest_path=dest_path,
        )

        assert result == dest_path
        assert await s3_client.file_exists(source_path) is True
        assert await s3_client.file_exists(dest_path) is True


class TestS3Stream:
    """Test S3 file streaming operations."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_stream_file_yields_chunks(
        self,
        s3_client: S3StorageClient,
        sample_binary_file: Path,
        test_prefix: str,
    ) -> None:
        """Test streaming file contents in chunks."""
        remote_path = f"{test_prefix}stream-test.bin"
        original_content = sample_binary_file.read_bytes()

        await s3_client.upload_file(
            local_path=str(sample_binary_file),
            remote_path=remote_path,
        )

        chunks = []
        async for chunk in s3_client.stream_file(
            remote_path=remote_path, chunk_size=1024
        ):
            chunks.append(chunk)

        streamed_content = b"".join(chunks)
        assert streamed_content == original_content
        assert len(chunks) > 1


class TestS3ErrorHandling:
    """Test S3 error handling scenarios."""

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_download_nonexistent_file_raises_error(
        self,
        s3_client: S3StorageClient,
        test_prefix: str,
        tmp_path: Path,
    ) -> None:
        """Test downloading non-existent file raises ClientError."""
        from botocore.exceptions import ClientError

        remote_path = f"{test_prefix}does-not-exist.txt"
        local_path = tmp_path / "download.txt"

        with pytest.raises(ClientError) as exc_info:
            await s3_client.download_file(
                remote_path=remote_path,
                local_path=str(local_path),
            )

        assert exc_info.value.response["Error"]["Code"] in ("404", "NoSuchKey")

    @skip_without_aws
    @skip_without_bucket
    @pytest.mark.asyncio
    async def test_file_exists_returns_false_for_missing(
        self,
        s3_client: S3StorageClient,
        test_prefix: str,
    ) -> None:
        """Test file_exists returns False for missing file."""
        remote_path = f"{test_prefix}missing-file.txt"

        result = await s3_client.file_exists(remote_path)

        assert result is False
