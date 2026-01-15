"""Checkpoint Repository Interface - Data access contract for checkpoints."""

from abc import ABC, abstractmethod

from src.domain.entities.checkpoint import Checkpoint


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
    async def delete(self, checkpoint_id: int) -> None:
        """Delete a checkpoint by ID."""

    @abstractmethod
    async def get_latest_by_training_job_id(
        self, training_job_id: int
    ) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""
