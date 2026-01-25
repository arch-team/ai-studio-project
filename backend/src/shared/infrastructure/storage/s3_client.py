"""S3 Storage Client - Amazon S3 storage integration.

Implements IStorageService interface using aioboto3 for native async operations.
"""

from collections.abc import AsyncIterator
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from src.shared.infrastructure.storage.interface import IStorageService


class S3StorageClient(IStorageService):
    """S3 storage client implementation using aioboto3.

    Uses aioboto3 for native async operations without thread pool overhead.
    Each operation creates a short-lived client (aioboto3 recommended pattern).
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        kms_key_id: str | None = None,
    ) -> None:
        """Initialize S3 storage client.

        Args:
            bucket_name: Default S3 bucket name.
            region: AWS region for the client.
            kms_key_id: Optional KMS key ID for SSE-KMS encryption.
        """
        self._bucket_name = bucket_name
        self._region = region
        self._kms_key_id = kms_key_id
        self._session = aioboto3.Session()

    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload a file to S3."""
        extra_args: dict[str, Any] = {}

        if metadata:
            extra_args["Metadata"] = metadata

        if self._kms_key_id:
            extra_args["ServerSideEncryption"] = "aws:kms"
            extra_args["SSEKMSKeyId"] = self._kms_key_id

        async with self._session.client("s3", region_name=self._region) as s3:
            await s3.upload_file(
                local_path,
                self._bucket_name,
                remote_path,
                ExtraArgs=extra_args if extra_args else None,
            )
        return remote_path

    async def download_file(self, remote_path: str, local_path: str) -> str:
        """Download a file from S3."""
        async with self._session.client("s3", region_name=self._region) as s3:
            await s3.download_file(self._bucket_name, remote_path, local_path)
        return local_path

    async def delete_file(self, remote_path: str) -> bool:
        """Delete a file from S3."""
        async with self._session.client("s3", region_name=self._region) as s3:
            await s3.delete_object(Bucket=self._bucket_name, Key=remote_path)
        return True

    async def list_files(self, prefix: str, max_results: int = 1000) -> list[dict[str, Any]]:
        """List files with a given prefix in S3."""
        async with self._session.client("s3", region_name=self._region) as s3:
            response = await s3.list_objects_v2(Bucket=self._bucket_name, Prefix=prefix, MaxKeys=max_results)
        return response.get("Contents", [])

    async def get_file_metadata(self, remote_path: str) -> dict[str, Any]:
        """Get metadata for a file in S3."""
        async with self._session.client("s3", region_name=self._region) as s3:
            return await s3.head_object(Bucket=self._bucket_name, Key=remote_path)

    async def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in S3."""
        try:
            async with self._session.client("s3", region_name=self._region) as s3:
                await s3.head_object(Bucket=self._bucket_name, Key=remote_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    async def generate_presigned_url(
        self,
        remote_path: str,
        expiration: int = 3600,
        operation: str = "get",
    ) -> str:
        """Generate a presigned URL for direct access."""
        client_method = "get_object" if operation == "get" else "put_object"
        async with self._session.client("s3", region_name=self._region) as s3:
            return await s3.generate_presigned_url(
                client_method,
                Params={"Bucket": self._bucket_name, "Key": remote_path},
                ExpiresIn=expiration,
            )

    async def copy_file(self, source_path: str, dest_path: str) -> str:
        """Copy a file within S3."""
        async with self._session.client("s3", region_name=self._region) as s3:
            await s3.copy_object(
                Bucket=self._bucket_name,
                CopySource={"Bucket": self._bucket_name, "Key": source_path},
                Key=dest_path,
            )
        return dest_path

    async def stream_file(self, remote_path: str, chunk_size: int = 8192) -> AsyncIterator[bytes]:
        """Stream file contents from S3."""
        async with self._session.client("s3", region_name=self._region) as s3:
            response = await s3.get_object(Bucket=self._bucket_name, Key=remote_path)
            stream = response["Body"]
            async for chunk in stream.iter_chunks(chunk_size):
                yield chunk
