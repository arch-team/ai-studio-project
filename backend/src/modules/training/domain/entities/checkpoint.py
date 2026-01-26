"""Checkpoint domain entity for training checkpoint management."""

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.shared.domain import PydanticEntity
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.utils import utc_now

from ..value_objects import (
    CheckpointStatus,
    CheckpointTriggerType,
    CheckpointType,
    StorageTier,
)
from ..value_objects.checkpoint_enums import STORAGE_TIER_HIERARCHY


class Checkpoint(PydanticEntity):
    """Checkpoint domain entity for training checkpoints."""

    # === Required fields ===
    training_job_id: int
    checkpoint_name: str = Field(min_length=1, max_length=255)
    storage_path: str
    size_bytes: int

    # === Checkpoint type and trigger ===
    checkpoint_type: CheckpointType = CheckpointType.EPOCH
    trigger_type: CheckpointTriggerType = CheckpointTriggerType.SCHEDULED
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
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    # ========== 业务方法 ==========

    def can_migrate_to(self, target_tier: StorageTier) -> bool:
        """Check if migration to target tier is valid."""
        valid_targets = STORAGE_TIER_HIERARCHY.get(self.storage_tier, [])
        return target_tier in valid_targets

    def migrate_to(self, target_tier: StorageTier) -> None:
        """Migrate to target storage tier."""
        if not self.can_migrate_to(target_tier):
            raise InvalidStateTransitionError("Checkpoint.storage_tier", self.storage_tier.value, target_tier.value)
        self.storage_tier = target_tier
        self.touch()

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
        """Archive the checkpoint."""
        if not self.can_archive():
            raise InvalidStateTransitionError("Checkpoint", self.status.value, CheckpointStatus.ARCHIVED.value)
        self.status = CheckpointStatus.ARCHIVED
        self.archived_at = utc_now()
        self.touch()

    def soft_delete(self) -> None:
        """Soft delete the checkpoint."""
        if not self.can_delete():
            raise InvalidStateTransitionError("Checkpoint", self.status.value, CheckpointStatus.DELETED.value)
        self.status = CheckpointStatus.DELETED
        self.deleted_at = utc_now()
        self.touch()

    def verify_integrity(self, calculated_checksum: str) -> bool:
        """Verify checkpoint integrity against stored checksum."""
        if self.checksum is None:
            return False
        return self.checksum == calculated_checksum
