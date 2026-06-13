"""Checkpoint Repository Interface - Data access contract for checkpoints."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..entities import Checkpoint

if TYPE_CHECKING:
    from ..value_objects import StorageTier


class ICheckpointRepository(ABC):
    """Abstract repository interface for Checkpoint entity."""

    @abstractmethod
    async def get_by_id(self, checkpoint_id: int) -> Checkpoint | None:
        """Get checkpoint by ID."""

    @abstractmethod
    async def get_by_training_job_id(self, training_job_id: int) -> list[Checkpoint]:
        """Get all checkpoints for a training job."""

    @abstractmethod
    async def create(self, checkpoint: Checkpoint) -> Checkpoint:
        """Create a new checkpoint."""

    @abstractmethod
    async def update(self, checkpoint: Checkpoint) -> Checkpoint:
        """Update an existing checkpoint."""

    @abstractmethod
    async def delete(self, checkpoint_id: int) -> bool:
        """Delete a checkpoint by ID. Returns True if deleted, False otherwise."""

    @abstractmethod
    async def get_latest_by_training_job_id(self, training_job_id: int) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""

    @abstractmethod
    async def count_by_training_job_id(self, training_job_id: int) -> int:
        """Count checkpoints for a training job."""

    @abstractmethod
    async def get_by_storage_tier(self, storage_tier: "StorageTier", limit: int = 100) -> list[Checkpoint]:
        """Get checkpoints by storage tier for migration."""

    @abstractmethod
    async def get_checkpoints_for_migration(
        self,
        training_job_id: int,
        exclude_latest_count: int = 3,
    ) -> list[Checkpoint]:
        """Get checkpoints eligible for migration (excluding latest N)."""

    @abstractmethod
    async def get_oldest_checkpoints(
        self,
        training_job_id: int | None = None,
        hours_threshold: int = 72,
    ) -> list[Checkpoint]:
        """Get checkpoints older than threshold for archival.

        training_job_id 为 None 时跨所有任务归档（用于定时迁移周期）。
        """
