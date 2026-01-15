"""Checkpoint domain entity for training checkpoint management."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from src.core.utils import utc_now


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


@dataclass
class Checkpoint:
    """Checkpoint domain entity for training checkpoints."""

    # === Required fields ===
    id: int
    training_job_id: int
    checkpoint_name: str
    storage_path: str
    size_bytes: int

    # === Checkpoint type and progress ===
    checkpoint_type: CheckpointType = CheckpointType.EPOCH
    epoch: int | None = None
    step: int | None = None

    # === Integrity verification ===
    checksum: str | None = None  # SHA-256

    # === Training metrics at checkpoint time ===
    loss: Decimal | None = None
    accuracy: Decimal | None = None
    metrics: dict | None = None

    # === Storage tier ===
    storage_tier: StorageTier = StorageTier.FSX
    status: CheckpointStatus = CheckpointStatus.AVAILABLE

    # === Audit fields ===
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    def can_migrate_to(self, target_tier: StorageTier) -> bool:
        """Check if migration to target tier is valid."""
        valid_targets = STORAGE_TIER_HIERARCHY.get(self.storage_tier, [])
        return target_tier in valid_targets

    def migrate_to(self, target_tier: StorageTier) -> None:
        """Migrate to target storage tier.

        Raises:
            ValueError: If migration is not allowed
        """
        if not self.can_migrate_to(target_tier):
            raise ValueError(
                f"Invalid storage tier migration: {self.storage_tier.value} -> {target_tier.value}"
            )
        self.storage_tier = target_tier
        self.updated_at = utc_now()

    def get_next_tier(self) -> StorageTier | None:
        """Get the next tier in the hierarchy."""
        valid_targets = STORAGE_TIER_HIERARCHY.get(self.storage_tier, [])
        return valid_targets[0] if valid_targets else None

    def is_available(self) -> bool:
        """Check if checkpoint is available."""
        return self.status == CheckpointStatus.AVAILABLE

    def is_archived(self) -> bool:
        """Check if checkpoint is archived."""
        return self.status == CheckpointStatus.ARCHIVED

    def is_deleted(self) -> bool:
        """Check if checkpoint is deleted."""
        return self.status == CheckpointStatus.DELETED

    def can_archive(self) -> bool:
        """Check if checkpoint can be archived."""
        return self.status == CheckpointStatus.AVAILABLE

    def can_delete(self) -> bool:
        """Check if checkpoint can be deleted."""
        return self.status != CheckpointStatus.DELETED

    def archive(self) -> None:
        """Archive the checkpoint.

        Raises:
            ValueError: If checkpoint cannot be archived
        """
        if not self.can_archive():
            raise ValueError(f"Cannot archive checkpoint in {self.status.value} status")
        self.status = CheckpointStatus.ARCHIVED
        self.archived_at = utc_now()
        self.updated_at = utc_now()

    def soft_delete(self) -> None:
        """Soft delete the checkpoint.

        Raises:
            ValueError: If checkpoint cannot be deleted
        """
        if not self.can_delete():
            raise ValueError(f"Cannot delete checkpoint in {self.status.value} status")
        self.status = CheckpointStatus.DELETED
        self.deleted_at = utc_now()
        self.updated_at = utc_now()

    def verify_integrity(self, calculated_checksum: str) -> bool:
        """Verify checkpoint integrity against stored checksum."""
        if self.checksum is None:
            return False
        return self.checksum == calculated_checksum
