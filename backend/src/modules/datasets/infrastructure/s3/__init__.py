"""S3 分片上传基础设施。"""

from .multipart_upload_client import (
    DEFAULT_PART_SIZE,
    MAX_PARTS,
    MIN_PART_SIZE,
    S3MultipartClient,
)

__all__ = [
    "S3MultipartClient",
    "DEFAULT_PART_SIZE",
    "MIN_PART_SIZE",
    "MAX_PARTS",
]
