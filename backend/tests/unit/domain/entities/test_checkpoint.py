"""Unit tests for Checkpoint domain entity.

Tests cover:
- Enum types validation
- Storage tier migration rules
- Business rules
- Entity creation
"""

from datetime import datetime
from decimal import Decimal

import pytest

from src.modules.training.domain.entities.checkpoint import (
    STORAGE_TIER_HIERARCHY,
    Checkpoint,
    CheckpointStatus,
    CheckpointType,
    StorageTier,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


class TestCheckpointTypeEnum:
    """Tests for CheckpointType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all required checkpoint types are defined."""
        expected_types = {"EPOCH", "STEP", "BEST", "FINAL", "MANUAL"}
        actual_types = {t.name for t in CheckpointType}
        assert actual_types == expected_types

    def test_type_values_match_database(self) -> None:
        """Verify enum values match database enum values."""
        assert CheckpointType.EPOCH.value == "EPOCH"
        assert CheckpointType.STEP.value == "STEP"
        assert CheckpointType.BEST.value == "BEST"
        assert CheckpointType.FINAL.value == "FINAL"
        assert CheckpointType.MANUAL.value == "MANUAL"


class TestStorageTierEnum:
    """Tests for StorageTier enum."""

    def test_all_tiers_defined(self) -> None:
        """Verify all required storage tiers are defined."""
        expected_tiers = {"NVME", "FSX", "S3"}
        actual_tiers = {t.name for t in StorageTier}
        assert actual_tiers == expected_tiers

    def test_tier_values_match_database(self) -> None:
        """Verify enum values match database enum values."""
        assert StorageTier.NVME.value == "NVME"
        assert StorageTier.FSX.value == "FSX"
        assert StorageTier.S3.value == "S3"


class TestCheckpointStatusEnum:
    """Tests for CheckpointStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all required statuses are defined."""
        expected_statuses = {"AVAILABLE", "ARCHIVED", "DELETED"}
        actual_statuses = {s.name for s in CheckpointStatus}
        assert actual_statuses == expected_statuses

    def test_status_values_match_database(self) -> None:
        """Verify enum values match database enum values."""
        assert CheckpointStatus.AVAILABLE.value == "AVAILABLE"
        assert CheckpointStatus.ARCHIVED.value == "ARCHIVED"
        assert CheckpointStatus.DELETED.value == "DELETED"


class TestStorageTierMigration:
    """Tests for storage tier migration rules (NVME -> FSX -> S3)."""

    @pytest.fixture
    def checkpoint(self) -> Checkpoint:
        """Create a basic checkpoint for testing."""
        return Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint-epoch100.pth",
            storage_path="/fsx/checkpoints/job-1/checkpoint-epoch100.pth",
            size_bytes=1073741824,  # 1GB
            storage_tier=StorageTier.NVME,
        )

    def test_nvme_to_fsx_valid(self, checkpoint: Checkpoint) -> None:
        """Test valid migration: NVME -> FSX."""
        assert checkpoint.storage_tier == StorageTier.NVME
        assert checkpoint.can_migrate_to(StorageTier.FSX)
        checkpoint.migrate_to(StorageTier.FSX)
        assert checkpoint.storage_tier == StorageTier.FSX

    def test_nvme_to_s3_valid(self, checkpoint: Checkpoint) -> None:
        """Test valid migration: NVME -> S3 (skip FSX)."""
        assert checkpoint.can_migrate_to(StorageTier.S3)
        checkpoint.migrate_to(StorageTier.S3)
        assert checkpoint.storage_tier == StorageTier.S3

    def test_fsx_to_s3_valid(self, checkpoint: Checkpoint) -> None:
        """Test valid migration: FSX -> S3."""
        checkpoint.storage_tier = StorageTier.FSX
        assert checkpoint.can_migrate_to(StorageTier.S3)
        checkpoint.migrate_to(StorageTier.S3)
        assert checkpoint.storage_tier == StorageTier.S3

    def test_reverse_migration_fsx_to_nvme_invalid(
        self, checkpoint: Checkpoint
    ) -> None:
        """Test invalid reverse migration: FSX -> NVME."""
        checkpoint.storage_tier = StorageTier.FSX
        assert not checkpoint.can_migrate_to(StorageTier.NVME)
        with pytest.raises(InvalidStateTransitionError):
            checkpoint.migrate_to(StorageTier.NVME)

    def test_reverse_migration_s3_to_fsx_invalid(self, checkpoint: Checkpoint) -> None:
        """Test invalid reverse migration: S3 -> FSX."""
        checkpoint.storage_tier = StorageTier.S3
        assert not checkpoint.can_migrate_to(StorageTier.FSX)
        with pytest.raises(InvalidStateTransitionError):
            checkpoint.migrate_to(StorageTier.FSX)

    def test_reverse_migration_s3_to_nvme_invalid(self, checkpoint: Checkpoint) -> None:
        """Test invalid reverse migration: S3 -> NVME."""
        checkpoint.storage_tier = StorageTier.S3
        assert not checkpoint.can_migrate_to(StorageTier.NVME)
        with pytest.raises(InvalidStateTransitionError):
            checkpoint.migrate_to(StorageTier.NVME)

    def test_get_next_tier_from_nvme(self, checkpoint: Checkpoint) -> None:
        """Test get_next_tier from NVME returns FSX."""
        assert checkpoint.get_next_tier() == StorageTier.FSX

    def test_get_next_tier_from_fsx(self, checkpoint: Checkpoint) -> None:
        """Test get_next_tier from FSX returns S3."""
        checkpoint.storage_tier = StorageTier.FSX
        assert checkpoint.get_next_tier() == StorageTier.S3

    def test_get_next_tier_from_s3_returns_none(self, checkpoint: Checkpoint) -> None:
        """Test get_next_tier from S3 returns None (final tier)."""
        checkpoint.storage_tier = StorageTier.S3
        assert checkpoint.get_next_tier() is None

    def test_same_tier_migration_invalid(self, checkpoint: Checkpoint) -> None:
        """Test that migrating to same tier is invalid."""
        assert not checkpoint.can_migrate_to(StorageTier.NVME)


class TestStorageTierHierarchy:
    """Tests for the storage tier hierarchy constant."""

    def test_nvme_can_migrate_to_fsx_and_s3(self) -> None:
        """Verify NVME can migrate to FSX and S3."""
        expected = [StorageTier.FSX, StorageTier.S3]
        assert STORAGE_TIER_HIERARCHY[StorageTier.NVME] == expected

    def test_fsx_can_only_migrate_to_s3(self) -> None:
        """Verify FSX can only migrate to S3."""
        expected = [StorageTier.S3]
        assert STORAGE_TIER_HIERARCHY[StorageTier.FSX] == expected

    def test_s3_is_final_tier(self) -> None:
        """Verify S3 is the final tier with no further migration."""
        assert STORAGE_TIER_HIERARCHY[StorageTier.S3] == []


class TestCheckpointBusinessRules:
    """Tests for Checkpoint business rules."""

    @pytest.fixture
    def checkpoint(self) -> Checkpoint:
        """Create a basic checkpoint for testing."""
        return Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint-epoch100.pth",
            storage_path="/fsx/checkpoints/job-1/checkpoint-epoch100.pth",
            size_bytes=1073741824,
        )

    def test_is_available(self, checkpoint: Checkpoint) -> None:
        """Test is_available() method."""
        assert checkpoint.is_available()
        checkpoint.status = CheckpointStatus.ARCHIVED
        assert not checkpoint.is_available()
        checkpoint.status = CheckpointStatus.DELETED
        assert not checkpoint.is_available()

    def test_is_archived(self, checkpoint: Checkpoint) -> None:
        """Test is_archived() method."""
        assert not checkpoint.is_archived()
        checkpoint.status = CheckpointStatus.ARCHIVED
        assert checkpoint.is_archived()

    def test_is_deleted(self, checkpoint: Checkpoint) -> None:
        """Test is_deleted() method."""
        assert not checkpoint.is_deleted()
        checkpoint.status = CheckpointStatus.DELETED
        assert checkpoint.is_deleted()

    def test_can_archive_when_available(self, checkpoint: Checkpoint) -> None:
        """Test can_archive() returns True when AVAILABLE."""
        assert checkpoint.can_archive()

    def test_cannot_archive_when_archived(self, checkpoint: Checkpoint) -> None:
        """Test can_archive() returns False when already ARCHIVED."""
        checkpoint.status = CheckpointStatus.ARCHIVED
        assert not checkpoint.can_archive()

    def test_cannot_archive_when_deleted(self, checkpoint: Checkpoint) -> None:
        """Test can_archive() returns False when DELETED."""
        checkpoint.status = CheckpointStatus.DELETED
        assert not checkpoint.can_archive()

    def test_archive_sets_status_and_timestamp(self, checkpoint: Checkpoint) -> None:
        """Test archive() sets status to ARCHIVED and sets archived_at."""
        assert checkpoint.archived_at is None
        checkpoint.archive()
        assert checkpoint.status == CheckpointStatus.ARCHIVED
        assert checkpoint.archived_at is not None

    def test_archive_when_not_available_raises_error(
        self, checkpoint: Checkpoint
    ) -> None:
        """Test archive() raises error when not AVAILABLE."""
        checkpoint.status = CheckpointStatus.DELETED
        with pytest.raises(InvalidStateTransitionError):
            checkpoint.archive()

    def test_soft_delete_sets_status_and_timestamp(
        self, checkpoint: Checkpoint
    ) -> None:
        """Test soft_delete() sets status to DELETED and sets deleted_at."""
        assert checkpoint.deleted_at is None
        checkpoint.soft_delete()
        assert checkpoint.status == CheckpointStatus.DELETED
        assert checkpoint.deleted_at is not None

    def test_can_delete_when_available(self, checkpoint: Checkpoint) -> None:
        """Test can_delete() returns True when AVAILABLE."""
        assert checkpoint.can_delete()

    def test_can_delete_when_archived(self, checkpoint: Checkpoint) -> None:
        """Test can_delete() returns True when ARCHIVED."""
        checkpoint.status = CheckpointStatus.ARCHIVED
        assert checkpoint.can_delete()

    def test_cannot_delete_when_deleted(self, checkpoint: Checkpoint) -> None:
        """Test can_delete() returns False when already DELETED."""
        checkpoint.status = CheckpointStatus.DELETED
        assert not checkpoint.can_delete()

    def test_verify_integrity_valid_checksum(self, checkpoint: Checkpoint) -> None:
        """Test verify_integrity() returns True for matching checksum."""
        checkpoint.checksum = "abc123"
        assert checkpoint.verify_integrity("abc123")

    def test_verify_integrity_invalid_checksum(self, checkpoint: Checkpoint) -> None:
        """Test verify_integrity() returns False for mismatched checksum."""
        checkpoint.checksum = "abc123"
        assert not checkpoint.verify_integrity("xyz789")

    def test_verify_integrity_no_stored_checksum(self, checkpoint: Checkpoint) -> None:
        """Test verify_integrity() returns False when no stored checksum."""
        assert checkpoint.checksum is None
        assert not checkpoint.verify_integrity("abc123")


class TestCheckpointCreation:
    """Tests for Checkpoint entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating checkpoint with only required fields."""
        checkpoint = Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint-epoch100.pth",
            storage_path="/fsx/checkpoints/job-1/checkpoint-epoch100.pth",
            size_bytes=1073741824,
        )
        assert checkpoint.id == 1
        assert checkpoint.training_job_id == 1
        assert checkpoint.checkpoint_name == "checkpoint-epoch100.pth"
        assert (
            checkpoint.storage_path == "/fsx/checkpoints/job-1/checkpoint-epoch100.pth"
        )
        assert checkpoint.size_bytes == 1073741824

    def test_default_checkpoint_type_is_epoch(self) -> None:
        """Test default checkpoint_type is EPOCH."""
        checkpoint = Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint.pth",
            storage_path="/fsx/checkpoints/checkpoint.pth",
            size_bytes=1000,
        )
        assert checkpoint.checkpoint_type == CheckpointType.EPOCH

    def test_default_storage_tier_is_fsx(self) -> None:
        """Test default storage_tier is FSX."""
        checkpoint = Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint.pth",
            storage_path="/fsx/checkpoints/checkpoint.pth",
            size_bytes=1000,
        )
        assert checkpoint.storage_tier == StorageTier.FSX

    def test_default_status_is_available(self) -> None:
        """Test default status is AVAILABLE."""
        checkpoint = Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint.pth",
            storage_path="/fsx/checkpoints/checkpoint.pth",
            size_bytes=1000,
        )
        assert checkpoint.status == CheckpointStatus.AVAILABLE

    def test_create_with_all_optional_fields(self) -> None:
        """Test creating checkpoint with all fields."""
        checkpoint = Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="best-model.pth",
            storage_path="/fsx/checkpoints/best-model.pth",
            size_bytes=2147483648,
            checkpoint_type=CheckpointType.BEST,
            epoch=50,
            step=10000,
            checksum="sha256:abcdef123456",
            loss=Decimal("0.001234"),
            accuracy=Decimal("0.9876"),
            metrics={"f1_score": 0.95, "precision": 0.94},
            storage_tier=StorageTier.S3,
            status=CheckpointStatus.ARCHIVED,
        )
        assert checkpoint.checkpoint_type == CheckpointType.BEST
        assert checkpoint.epoch == 50
        assert checkpoint.step == 10000
        assert checkpoint.checksum == "sha256:abcdef123456"
        assert checkpoint.loss == Decimal("0.001234")
        assert checkpoint.accuracy == Decimal("0.9876")
        assert checkpoint.metrics == {"f1_score": 0.95, "precision": 0.94}
        assert checkpoint.storage_tier == StorageTier.S3
        assert checkpoint.status == CheckpointStatus.ARCHIVED

    def test_created_at_set_on_creation(self) -> None:
        """Test created_at is set automatically."""
        checkpoint = Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint.pth",
            storage_path="/fsx/checkpoints/checkpoint.pth",
            size_bytes=1000,
        )
        assert checkpoint.created_at is not None
        assert isinstance(checkpoint.created_at, datetime)

    def test_updated_at_set_on_creation(self) -> None:
        """Test updated_at is set automatically."""
        checkpoint = Checkpoint(
            id=1,
            training_job_id=1,
            checkpoint_name="checkpoint.pth",
            storage_path="/fsx/checkpoints/checkpoint.pth",
            size_bytes=1000,
        )
        assert checkpoint.updated_at is not None
        assert isinstance(checkpoint.updated_at, datetime)
