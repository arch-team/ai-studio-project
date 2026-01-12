"""AWS Client Wrappers.

This module provides client wrappers for AWS services used by the AI Training Platform.
"""

from src.clients.hyperpod_client import (
    get_hyperpod_client,
    HyperPodClient,
    InstanceType,
    TrainingConfig,
    TrainingJobInfo,
    TrainingJobStatus,
)
from src.clients.s3_client import (
    BucketType,
    get_s3_client,
    PresignedUrl,
    S3Client,
    S3Object,
    StorageTier,
)

__all__ = [
    # HyperPod Client
    "get_hyperpod_client",
    "HyperPodClient",
    "InstanceType",
    "TrainingConfig",
    "TrainingJobInfo",
    "TrainingJobStatus",
    # S3 Client
    "BucketType",
    "get_s3_client",
    "PresignedUrl",
    "S3Client",
    "S3Object",
    "StorageTier",
]
