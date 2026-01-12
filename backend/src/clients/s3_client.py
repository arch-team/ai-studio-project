"""S3 Client wrapper.

Task: T015 - S3 客户端封装
封装 boto3 S3 操作 (upload_file, download_file, list_objects),
支持 presigned URLs,继承 T008b 配置的 SSE-KMS 默认加密
"""

import logging
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, AsyncGenerator, BinaryIO, NoReturn, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pydantic import BaseModel

from src.core.config import get_settings
from src.core.exceptions import (
    S3DeleteError,
    S3DownloadError,
    S3Error,
    S3NotFoundError,
    S3PermissionError,
    S3UploadError,
)

logger = logging.getLogger(__name__)


class StorageTier(str, Enum):
    """S3 storage class for objects."""

    STANDARD = "STANDARD"
    INTELLIGENT_TIERING = "INTELLIGENT_TIERING"
    GLACIER = "GLACIER"
    GLACIER_IR = "GLACIER_IR"  # Instant Retrieval
    DEEP_ARCHIVE = "DEEP_ARCHIVE"


class BucketType(str, Enum):
    """Predefined bucket types for the platform."""

    DATASETS = "datasets"
    MODELS = "models"
    CHECKPOINTS = "checkpoints"


@dataclass
class S3Object:
    """S3 object metadata."""

    key: str
    bucket: str
    size: int
    last_modified: datetime
    etag: str
    storage_class: str
    content_type: Optional[str] = None


class PresignedUrl(BaseModel):
    """Presigned URL response."""

    url: str
    expires_in: int
    method: str  # GET or PUT
    bucket: str
    key: str


class S3Client:
    """Client for AWS S3 operations with SSE-KMS encryption support.

    This client provides a high-level interface for S3 operations used by the
    AI Training Platform, including dataset uploads, model storage, and
    checkpoint management.
    """

    def __init__(self):
        """Initialize S3 client with configuration."""
        self.settings = get_settings()
        self._client = None
        self._client_lock = Lock()  # 线程安全锁

    @property
    def client(self) -> Any:
        """Get or create boto3 S3 client with thread safety.

        Returns:
            boto3 S3 client
        """
        if self._client is None:
            with self._client_lock:
                # 双重检查锁定模式
                if self._client is None:
                    config = Config(
                        region_name=self.settings.aws_region,
                        retries={"max_attempts": 3, "mode": "adaptive"},
                        s3={
                            "addressing_style": "path"
                        },  # Use path-style for compatibility
                    )

                    session_kwargs = {}
                    if self.settings.aws_profile:
                        session_kwargs["profile_name"] = self.settings.aws_profile

                    session = boto3.Session(**session_kwargs)
                    self._client = session.client("s3", config=config)

        return self._client

    def get_bucket_name(self, bucket_type: BucketType) -> str:
        """Get bucket name for a given bucket type.

        Args:
            bucket_type: Type of bucket (datasets, models, checkpoints)

        Returns:
            Bucket name from configuration

        Raises:
            ValueError: If bucket not configured
        """
        bucket_mapping = {
            BucketType.DATASETS: self.settings.s3_datasets_bucket,
            BucketType.MODELS: self.settings.s3_models_bucket,
            BucketType.CHECKPOINTS: self.settings.s3_checkpoints_bucket,
        }

        bucket = bucket_mapping.get(bucket_type)
        if not bucket:
            raise ValueError(f"Bucket not configured for type: {bucket_type}")

        return bucket

    def _create_s3_object_from_response(
        self,
        bucket: str,
        key: str,
        head_response: dict,
        content_type: Optional[str] = None,
    ) -> S3Object:
        """Create S3Object from head_object response.

        Args:
            bucket: S3 bucket name
            key: S3 object key
            head_response: Response from head_object
            content_type: Optional content type override

        Returns:
            S3Object with metadata
        """
        return S3Object(
            key=key,
            bucket=bucket,
            size=head_response.get("ContentLength", 0),
            last_modified=head_response["LastModified"],
            etag=head_response["ETag"].strip('"'),
            storage_class=head_response.get("StorageClass", "STANDARD"),
            content_type=content_type or head_response.get("ContentType"),
        )

    def _prepare_upload_args(
        self,
        content_type: str,
        storage_class: Optional[StorageTier] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Prepare ExtraArgs for S3 upload operations.

        Args:
            content_type: MIME content type
            storage_class: Optional storage tier
            metadata: Optional metadata dictionary

        Returns:
            Dictionary of extra arguments for upload
        """
        extra_args: dict[str, Any] = {
            "ContentType": content_type,
            "ServerSideEncryption": "aws:kms",  # SSE-KMS encryption
        }

        if storage_class:
            extra_args["StorageClass"] = storage_class.value

        if metadata:
            extra_args["Metadata"] = metadata

        return extra_args

    def _handle_client_error(
        self,
        error: ClientError,
        operation: str,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
    ) -> NoReturn:
        """Handle ClientError with appropriate logging and re-raise typed exception.

        Args:
            error: The ClientError exception
            operation: Name of the S3 operation that failed
            bucket: Optional bucket name for context
            key: Optional object key for context

        Raises:
            S3NotFoundError: If object not found (404)
            S3PermissionError: If access denied (403)
            S3UploadError: If upload operation fails
            S3DownloadError: If download operation fails
            S3DeleteError: If delete operation fails
            S3Error: For all other S3 errors
        """
        error_code = error.response.get("Error", {}).get("Code", "")
        error_message = error.response.get("Error", {}).get("Message", str(error))
        s3_path = f"s3://{bucket}/{key}" if bucket and key else ""

        # Structured logging
        logger.error(
            "s3_operation_failed",
            operation=operation,
            error_code=error_code,
            error_message=error_message,
            bucket=bucket,
            key=key,
        )

        details = {
            "operation": operation,
            "error_code": error_code,
            "bucket": bucket,
            "key": key,
        }

        # Map error codes to specific exceptions with exception chaining
        if error_code in ("404", "NoSuchKey", "NoSuchBucket"):
            raise S3NotFoundError(
                message=f"Object not found: {s3_path}" if s3_path else error_message,
                code=error_code,
                details=details,
            ) from error

        if error_code in ("403", "AccessDenied"):
            raise S3PermissionError(
                message=f"Access denied: {s3_path}" if s3_path else error_message,
                code=error_code,
                details=details,
            ) from error

        # Map operation to specific exception type with exception chaining
        operation_lower = operation.lower()
        if "upload" in operation_lower:
            raise S3UploadError(
                message=f"Upload failed: {error_message}",
                code=error_code,
                details=details,
            ) from error
        if "download" in operation_lower:
            raise S3DownloadError(
                message=f"Download failed: {error_message}",
                code=error_code,
                details=details,
            ) from error
        if "delete" in operation_lower:
            raise S3DeleteError(
                message=f"Delete failed: {error_message}",
                code=error_code,
                details=details,
            ) from error

        # Generic S3 error for all other cases with exception chaining
        raise S3Error(
            message=f"S3 {operation} failed: {error_message}",
            code=error_code,
            details=details,
        ) from error

    async def upload_file(
        self,
        file_path: str,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        storage_class: StorageTier = StorageTier.STANDARD,
    ) -> S3Object:
        """Upload a file to S3 with SSE-KMS encryption.

        Args:
            file_path: Local file path to upload
            bucket: Target S3 bucket
            key: S3 object key
            content_type: MIME type (auto-detected if not provided)
            metadata: Custom metadata dict
            storage_class: S3 storage class

        Returns:
            S3Object with upload result

        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Auto-detect content type if not provided
            if not content_type:
                detected_type, _ = mimetypes.guess_type(file_path)
                content_type = detected_type or "application/octet-stream"

            # Prepare upload arguments
            extra_args = self._prepare_upload_args(
                content_type, storage_class, metadata
            )

            # Upload file
            file_size = os.path.getsize(file_path)
            self.client.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
            logger.info(f"File uploaded: s3://{bucket}/{key} ({file_size} bytes)")

            # Get and return object metadata
            head_response = self.client.head_object(Bucket=bucket, Key=key)
            return self._create_s3_object_from_response(
                bucket, key, head_response, content_type
            )

        except ClientError as e:
            self._handle_client_error(e, "upload", bucket, key)

    async def upload_fileobj(
        self,
        file_obj: BinaryIO,
        bucket: str,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
        storage_class: StorageTier = StorageTier.STANDARD,
    ) -> S3Object:
        """Upload a file-like object to S3.

        Args:
            file_obj: File-like object to upload
            bucket: Target S3 bucket
            key: S3 object key
            content_type: MIME type
            metadata: Custom metadata dict
            storage_class: S3 storage class

        Returns:
            S3Object with upload result
        """
        try:
            # Prepare upload arguments
            extra_args = self._prepare_upload_args(
                content_type, storage_class, metadata
            )

            # Upload file object
            self.client.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra_args)
            logger.info(f"File object uploaded: s3://{bucket}/{key}")

            # Get and return object metadata
            head_response = self.client.head_object(Bucket=bucket, Key=key)
            return self._create_s3_object_from_response(
                bucket, key, head_response, content_type
            )

        except ClientError as e:
            self._handle_client_error(e, "upload", bucket, key)

    async def download_file(
        self,
        bucket: str,
        key: str,
        file_path: str,
    ) -> str:
        """Download a file from S3.

        Args:
            bucket: Source S3 bucket
            key: S3 object key
            file_path: Local destination path

        Returns:
            Local file path

        Raises:
            RuntimeError: If download fails
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Download file
            self.client.download_file(bucket, key, file_path)
            logger.info(f"File downloaded: s3://{bucket}/{key} -> {file_path}")
            return file_path

        except ClientError as e:
            self._handle_client_error(e, "download", bucket, key)

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
        delimiter: Optional[str] = None,
    ) -> AsyncGenerator[S3Object, None]:
        """List objects in S3 bucket with pagination.

        Args:
            bucket: S3 bucket name
            prefix: Key prefix filter
            max_keys: Maximum keys per page
            delimiter: Delimiter for hierarchy (e.g., "/" for folders)

        Yields:
            S3Object for each matching object
        """
        try:
            paginator = self.client.get_paginator("list_objects_v2")

            page_config = {
                "Bucket": bucket,
                "Prefix": prefix,
                "MaxKeys": max_keys,
            }

            if delimiter:
                page_config["Delimiter"] = delimiter

            for page in paginator.paginate(**page_config):
                for obj in page.get("Contents", []):
                    yield S3Object(
                        key=obj["Key"],
                        bucket=bucket,
                        size=obj["Size"],
                        last_modified=obj["LastModified"],
                        etag=obj["ETag"].strip('"'),
                        storage_class=obj.get("StorageClass", "STANDARD"),
                    )

        except ClientError as e:
            self._handle_client_error(e, "list", bucket)

    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from S3.

        Args:
            bucket: S3 bucket name
            key: Object key to delete

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Object deleted: s3://{bucket}/{key}")
            return True

        except ClientError as e:
            self._handle_client_error(e, "delete", bucket, key)

    async def delete_objects(self, bucket: str, keys: list[str]) -> int:
        """Delete multiple objects from S3.

        Args:
            bucket: S3 bucket name
            keys: List of object keys to delete

        Returns:
            Number of objects deleted
        """
        if not keys:
            return 0

        try:
            # S3 delete_objects supports up to 1000 keys per request
            deleted_count = 0
            batch_size = 1000

            for i in range(0, len(keys), batch_size):
                batch = keys[i : i + batch_size]
                response = self.client.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": [{"Key": k} for k in batch]},
                )
                deleted_count += len(response.get("Deleted", []))

            logger.info(f"Deleted {deleted_count} objects from s3://{bucket}")
            return deleted_count

        except ClientError as e:
            self._handle_client_error(e, "batch delete", bucket)

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        method: str = "GET",
        expires_in: int = 3600,
        content_type: Optional[str] = None,
    ) -> PresignedUrl:
        """Generate a presigned URL for S3 object access.

        Args:
            bucket: S3 bucket name
            key: Object key
            method: HTTP method (GET for download, PUT for upload)
            expires_in: URL expiration time in seconds
            content_type: Content type for PUT uploads

        Returns:
            PresignedUrl with the generated URL
        """
        try:
            normalized_method = method.upper()
            client_method = "get_object" if normalized_method == "GET" else "put_object"

            params = {"Bucket": bucket, "Key": key}
            if normalized_method == "PUT" and content_type:
                params["ContentType"] = content_type

            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params=params,
                ExpiresIn=expires_in,
            )

            return PresignedUrl(
                url=url,
                expires_in=expires_in,
                method=normalized_method,
                bucket=bucket,
                key=key,
            )

        except ClientError as e:
            self._handle_client_error(e, "generate presigned URL", bucket, key)

    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in S3.

        Args:
            bucket: S3 bucket name
            key: Object key

        Returns:
            True if object exists
        """
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise

    async def get_object_metadata(self, bucket: str, key: str) -> S3Object:
        """Get metadata for an S3 object.

        Args:
            bucket: S3 bucket name
            key: Object key

        Returns:
            S3Object with metadata

        Raises:
            RuntimeError: If object not found
        """
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return self._create_s3_object_from_response(bucket, key, response)

        except ClientError as e:
            self._handle_client_error(e, "get object metadata", bucket, key)

    async def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        storage_class: Optional[StorageTier] = None,
    ) -> S3Object:
        """Copy an object within S3.

        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key
            storage_class: Optional storage class for destination

        Returns:
            S3Object with destination object metadata
        """
        try:
            copy_source = {"Bucket": source_bucket, "Key": source_key}
            extra_args = {"ServerSideEncryption": "aws:kms"}

            if storage_class:
                extra_args["StorageClass"] = storage_class.value

            self.client.copy(copy_source, dest_bucket, dest_key, ExtraArgs=extra_args)
            logger.info(
                f"Object copied: s3://{source_bucket}/{source_key} -> "
                f"s3://{dest_bucket}/{dest_key}"
            )

            return await self.get_object_metadata(dest_bucket, dest_key)

        except ClientError as e:
            self._handle_client_error(e, "copy", dest_bucket, dest_key)


# Singleton instance
_s3_client: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    """Get or create S3 client singleton.

    Returns:
        S3Client instance
    """
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
