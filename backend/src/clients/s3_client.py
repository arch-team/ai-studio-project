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
from typing import BinaryIO, Iterator, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pydantic import BaseModel

from src.core.config import get_settings

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
        self._resource = None

    @property
    def client(self):
        """Get or create boto3 S3 client.

        Returns:
            boto3 S3 client
        """
        if self._client is None:
            config = Config(
                region_name=self.settings.aws_region,
                retries={"max_attempts": 3, "mode": "adaptive"},
                s3={"addressing_style": "path"},  # Use path-style for compatibility
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
            # Auto-detect content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or "application/octet-stream"

            extra_args = {
                "ContentType": content_type,
                "StorageClass": storage_class.value,
                "ServerSideEncryption": "aws:kms",  # SSE-KMS encryption
            }

            if metadata:
                extra_args["Metadata"] = metadata

            # Upload file
            file_size = os.path.getsize(file_path)

            self.client.upload_file(
                file_path,
                bucket,
                key,
                ExtraArgs=extra_args,
            )

            logger.info(f"File uploaded: s3://{bucket}/{key} ({file_size} bytes)")

            # Get object metadata
            head_response = self.client.head_object(Bucket=bucket, Key=key)

            return S3Object(
                key=key,
                bucket=bucket,
                size=file_size,
                last_modified=head_response["LastModified"],
                etag=head_response["ETag"].strip('"'),
                storage_class=storage_class.value,
                content_type=content_type,
            )

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise RuntimeError(f"S3 upload failed: {e}")

    async def upload_fileobj(
        self,
        file_obj: BinaryIO,
        bucket: str,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> S3Object:
        """Upload a file-like object to S3.

        Args:
            file_obj: File-like object to upload
            bucket: Target S3 bucket
            key: S3 object key
            content_type: MIME type
            metadata: Custom metadata dict

        Returns:
            S3Object with upload result
        """
        try:
            extra_args = {
                "ContentType": content_type,
                "ServerSideEncryption": "aws:kms",
            }

            if metadata:
                extra_args["Metadata"] = metadata

            self.client.upload_fileobj(
                file_obj,
                bucket,
                key,
                ExtraArgs=extra_args,
            )

            logger.info(f"File object uploaded: s3://{bucket}/{key}")

            # Get object metadata
            head_response = self.client.head_object(Bucket=bucket, Key=key)

            return S3Object(
                key=key,
                bucket=bucket,
                size=head_response["ContentLength"],
                last_modified=head_response["LastModified"],
                etag=head_response["ETag"].strip('"'),
                storage_class=head_response.get("StorageClass", "STANDARD"),
                content_type=content_type,
            )

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise RuntimeError(f"S3 upload failed: {e}")

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

            self.client.download_file(bucket, key, file_path)

            logger.info(f"File downloaded: s3://{bucket}/{key} -> {file_path}")
            return file_path

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise RuntimeError(f"Object not found: s3://{bucket}/{key}")
            logger.error(f"S3 download failed: {e}")
            raise RuntimeError(f"S3 download failed: {e}")

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
        delimiter: Optional[str] = None,
    ) -> Iterator[S3Object]:
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
            logger.error(f"S3 list failed: {e}")
            raise RuntimeError(f"S3 list failed: {e}")

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
            logger.error(f"S3 delete failed: {e}")
            raise RuntimeError(f"S3 delete failed: {e}")

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

            for i in range(0, len(keys), 1000):
                batch = keys[i : i + 1000]
                response = self.client.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": [{"Key": k} for k in batch]},
                )
                deleted_count += len(response.get("Deleted", []))

            logger.info(f"Deleted {deleted_count} objects from s3://{bucket}")
            return deleted_count

        except ClientError as e:
            logger.error(f"S3 batch delete failed: {e}")
            raise RuntimeError(f"S3 batch delete failed: {e}")

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
            client_method = "get_object" if method.upper() == "GET" else "put_object"

            params = {"Bucket": bucket, "Key": key}

            if method.upper() == "PUT" and content_type:
                params["ContentType"] = content_type

            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params=params,
                ExpiresIn=expires_in,
            )

            return PresignedUrl(
                url=url,
                expires_in=expires_in,
                method=method.upper(),
                bucket=bucket,
                key=key,
            )

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise RuntimeError(f"Failed to generate presigned URL: {e}")

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

            return S3Object(
                key=key,
                bucket=bucket,
                size=response["ContentLength"],
                last_modified=response["LastModified"],
                etag=response["ETag"].strip('"'),
                storage_class=response.get("StorageClass", "STANDARD"),
                content_type=response.get("ContentType"),
            )

        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                raise RuntimeError(f"Object not found: s3://{bucket}/{key}")
            raise RuntimeError(f"Failed to get object metadata: {e}")

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

            self.client.copy(
                copy_source,
                dest_bucket,
                dest_key,
                ExtraArgs=extra_args,
            )

            logger.info(f"Object copied: s3://{source_bucket}/{source_key} -> s3://{dest_bucket}/{dest_key}")

            return await self.get_object_metadata(dest_bucket, dest_key)

        except ClientError as e:
            logger.error(f"S3 copy failed: {e}")
            raise RuntimeError(f"S3 copy failed: {e}")


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
