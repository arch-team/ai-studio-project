"""S3 Adapter - Amazon S3 storage integration.

Implements IStorageService interface for S3 object storage operations.
"""

from src.infrastructure.external.s3.client import S3StorageClient

__all__ = ["S3StorageClient"]
