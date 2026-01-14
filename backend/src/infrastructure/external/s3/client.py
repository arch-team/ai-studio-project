"""S3 Storage Client - Amazon S3 storage integration.

Implements IStorageService interface using boto3 for object storage operations.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.application.interfaces.storage_service import IStorageService


class S3StorageClient(IStorageService):
    """S3 storage client implementation.

    Wraps boto3 S3 client for object storage operations.
    All operations are async for FastAPI compatibility.
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-west-2",
        kms_key_id: Optional[str] = None,
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
        self._s3_client = boto3.client("s3", region_name=region)

    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload a file to S3."""
        loop = asyncio.get_event_loop()

        def _upload() -> str:
            extra_args: Dict[str, Any] = {}

            if metadata:
                extra_args["Metadata"] = metadata

            if self._kms_key_id:
                extra_args["ServerSideEncryption"] = "aws:kms"
                extra_args["SSEKMSKeyId"] = self._kms_key_id

            self._s3_client.upload_file(
                local_path,
                self._bucket_name,
                remote_path,
                ExtraArgs=extra_args if extra_args else None,
            )
            return remote_path

        return await loop.run_in_executor(None, _upload)

    async def download_file(self, remote_path: str, local_path: str) -> str:
        """Download a file from S3."""
        loop = asyncio.get_event_loop()

        def _download() -> str:
            self._s3_client.download_file(self._bucket_name, remote_path, local_path)
            return local_path

        return await loop.run_in_executor(None, _download)

    async def delete_file(self, remote_path: str) -> bool:
        """Delete a file from S3."""
        loop = asyncio.get_event_loop()

        def _delete() -> bool:
            self._s3_client.delete_object(Bucket=self._bucket_name, Key=remote_path)
            return True

        return await loop.run_in_executor(None, _delete)

    async def list_files(
        self, prefix: str, max_results: int = 1000
    ) -> List[Dict[str, Any]]:
        """List files with a given prefix in S3."""
        loop = asyncio.get_event_loop()

        def _list() -> List[Dict[str, Any]]:
            response = self._s3_client.list_objects_v2(
                Bucket=self._bucket_name, Prefix=prefix, MaxKeys=max_results
            )
            return response.get("Contents", [])

        return await loop.run_in_executor(None, _list)

    async def get_file_metadata(self, remote_path: str) -> Dict[str, Any]:
        """Get metadata for a file in S3."""
        loop = asyncio.get_event_loop()

        def _get_metadata() -> Dict[str, Any]:
            return self._s3_client.head_object(
                Bucket=self._bucket_name, Key=remote_path
            )

        return await loop.run_in_executor(None, _get_metadata)

    async def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in S3."""
        loop = asyncio.get_event_loop()

        def _exists() -> bool:
            try:
                self._s3_client.head_object(Bucket=self._bucket_name, Key=remote_path)
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                    return False
                raise

        return await loop.run_in_executor(None, _exists)

    async def generate_presigned_url(
        self,
        remote_path: str,
        expiration: int = 3600,
        operation: str = "get",
    ) -> str:
        """Generate a presigned URL for direct access."""
        loop = asyncio.get_event_loop()

        def _generate_url() -> str:
            client_method = "get_object" if operation == "get" else "put_object"
            return self._s3_client.generate_presigned_url(
                client_method,
                Params={"Bucket": self._bucket_name, "Key": remote_path},
                ExpiresIn=expiration,
            )

        return await loop.run_in_executor(None, _generate_url)

    async def copy_file(self, source_path: str, dest_path: str) -> str:
        """Copy a file within S3."""
        loop = asyncio.get_event_loop()

        def _copy() -> str:
            self._s3_client.copy_object(
                Bucket=self._bucket_name,
                CopySource={"Bucket": self._bucket_name, "Key": source_path},
                Key=dest_path,
            )
            return dest_path

        return await loop.run_in_executor(None, _copy)

    async def stream_file(
        self, remote_path: str, chunk_size: int = 8192
    ) -> AsyncIterator[bytes]:
        """Stream file contents from S3."""
        loop = asyncio.get_event_loop()

        def _get_body() -> Any:
            response = self._s3_client.get_object(
                Bucket=self._bucket_name, Key=remote_path
            )
            return response["Body"]

        body = await loop.run_in_executor(None, _get_body)

        def _read_chunk() -> bytes:
            return body.read(chunk_size)

        while True:
            chunk = await loop.run_in_executor(None, _read_chunk)
            if not chunk:
                break
            yield chunk
