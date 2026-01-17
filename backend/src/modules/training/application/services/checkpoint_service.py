"""Checkpoint Service - Business logic for checkpoint management."""

from decimal import Decimal

from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.exceptions import CheckpointNotFoundError
from src.modules.training.domain.repositories import ICheckpointRepository
from src.modules.training.domain.value_objects import CheckpointType
from src.shared.application import BaseService


class CheckpointService(BaseService[Checkpoint, int]):
    """Service for managing training checkpoints."""

    _not_found_error_factory = CheckpointNotFoundError

    def __init__(self, repository: ICheckpointRepository):
        super().__init__(repository, "Checkpoint")

    async def get_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """Get checkpoint by ID."""
        return await self._get_or_raise(checkpoint_id)

    async def get_checkpoints_for_job(self, training_job_id: int) -> list[Checkpoint]:
        """Get all checkpoints for a training job."""
        return await self._repository.get_by_training_job_id(training_job_id)

    async def get_latest_checkpoint(self, training_job_id: int) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""
        return await self._repository.get_latest_by_training_job_id(training_job_id)

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
        """Create a manual checkpoint."""
        checkpoint = Checkpoint(
            id=0,
            training_job_id=training_job_id,
            checkpoint_name=checkpoint_name,
            storage_path=storage_path,
            size_bytes=0,  # Will be updated when actual checkpoint is saved
            checkpoint_type=CheckpointType.MANUAL,
            epoch=epoch,
            step=step,
            loss=loss,
            accuracy=accuracy,
        )
        return await self._repository.create(checkpoint)

    async def archive_checkpoint(self, checkpoint_id: int) -> Checkpoint:
        """Archive a checkpoint (move to cold storage)."""
        checkpoint = await self.get_checkpoint(checkpoint_id)
        checkpoint.archive()
        return await self._repository.update(checkpoint)

    async def delete_checkpoint(self, checkpoint_id: int) -> None:
        """Soft delete a checkpoint."""
        checkpoint = await self.get_checkpoint(checkpoint_id)
        checkpoint.soft_delete()
        await self._repository.update(checkpoint)
