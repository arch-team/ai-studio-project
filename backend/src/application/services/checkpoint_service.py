"""Checkpoint Service - Checkpoint management operations."""

from decimal import Decimal

from src.domain.entities.checkpoint import (
    Checkpoint,
    CheckpointStatus,
    CheckpointType,
    StorageTier,
)
from src.domain.repositories.checkpoint_repository import ICheckpointRepository


class CheckpointService:
    """Service for checkpoint management operations."""

    def __init__(self, checkpoint_repository: ICheckpointRepository):
        self._checkpoint_repo = checkpoint_repository

    async def create_manual_checkpoint(
        self,
        training_job_id: int,
        checkpoint_name: str,
        storage_path: str,
        epoch: int | None = None,
        step: int | None = None,
        loss: Decimal | None = None,
        accuracy: Decimal | None = None,
    ) -> Checkpoint:
        """Create a manual checkpoint for a training job."""
        checkpoint = Checkpoint(
            id=0,  # Will be set by repository
            training_job_id=training_job_id,
            checkpoint_name=checkpoint_name,
            storage_path=storage_path,
            checkpoint_type=CheckpointType.MANUAL,
            epoch=epoch,
            step=step,
            size_bytes=0,  # Will be updated when actual checkpoint is saved
            loss=loss,
            accuracy=accuracy,
            storage_tier=StorageTier.FSX,
            status=CheckpointStatus.AVAILABLE,
        )
        return await self._checkpoint_repo.create(checkpoint)

    async def get_checkpoint(self, checkpoint_id: int) -> Checkpoint | None:
        """Get checkpoint by ID."""
        return await self._checkpoint_repo.get_by_id(checkpoint_id)

    async def get_checkpoints_by_job(self, training_job_id: int) -> list[Checkpoint]:
        """Get all checkpoints for a training job."""
        return await self._checkpoint_repo.get_by_training_job_id(training_job_id)

    async def get_latest_checkpoint(
        self, training_job_id: int
    ) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""
        return await self._checkpoint_repo.get_latest_by_training_job_id(training_job_id)

    async def update_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        """Update a checkpoint."""
        return await self._checkpoint_repo.update(checkpoint)

    async def delete_checkpoint(self, checkpoint_id: int) -> None:
        """Delete a checkpoint."""
        await self._checkpoint_repo.delete(checkpoint_id)
