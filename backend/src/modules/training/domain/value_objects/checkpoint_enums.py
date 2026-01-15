"""Checkpoint related enums."""

from enum import Enum


class CheckpointType(Enum):
    """Checkpoint type (matches database checkpointtype enum)."""

    EPOCH = "EPOCH"
    STEP = "STEP"
    BEST = "BEST"
    FINAL = "FINAL"
    MANUAL = "MANUAL"


class StorageTier(Enum):
    """Storage tier for tiered storage (NVMe -> FSx -> S3)."""

    NVME = "NVME"
    FSX = "FSX"
    S3 = "S3"


class CheckpointStatus(Enum):
    """Checkpoint status."""

    AVAILABLE = "AVAILABLE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


# Storage tier migration hierarchy (one-way only: hot -> cold)
STORAGE_TIER_HIERARCHY = {
    StorageTier.NVME: [StorageTier.FSX, StorageTier.S3],
    StorageTier.FSX: [StorageTier.S3],
    StorageTier.S3: [],  # Final tier
}
