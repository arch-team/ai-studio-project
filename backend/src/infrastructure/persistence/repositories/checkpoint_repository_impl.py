"""Checkpoint Repository Implementation - SQLAlchemy data access for checkpoints."""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.checkpoint import (
    Checkpoint,
    CheckpointStatus,
    CheckpointType,
    StorageTier,
)
from src.domain.repositories.checkpoint_repository import ICheckpointRepository
from src.infrastructure.persistence.models.checkpoint_model import CheckpointModel


class CheckpointRepository(ICheckpointRepository):
    """SQLAlchemy implementation of Checkpoint repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _model_to_entity(self, model: CheckpointModel) -> Checkpoint:
        """Convert ORM model to domain entity."""
        return Checkpoint(
            id=model.id,
            training_job_id=model.training_job_id,
            checkpoint_name=model.checkpoint_name,
            storage_path=model.storage_path,
            size_bytes=model.size_bytes,
            checkpoint_type=CheckpointType(model.checkpoint_type.value),
            epoch=model.epoch,
            step=model.step,
            checksum=model.checksum,
            loss=model.loss,
            accuracy=model.accuracy,
            metrics=model.metrics,
            storage_tier=StorageTier(model.storage_tier.value),
            status=CheckpointStatus(model.status.value),
            created_at=model.created_at,
            updated_at=model.updated_at,
            archived_at=model.archived_at,
            deleted_at=model.deleted_at,
        )

    def _entity_to_model(self, entity: Checkpoint) -> CheckpointModel:
        """Convert domain entity to ORM model."""
        return CheckpointModel(
            id=entity.id if entity.id else None,
            training_job_id=entity.training_job_id,
            checkpoint_name=entity.checkpoint_name,
            storage_path=entity.storage_path,
            size_bytes=entity.size_bytes,
            checkpoint_type=CheckpointType(entity.checkpoint_type.value),
            epoch=entity.epoch,
            step=entity.step,
            checksum=entity.checksum,
            loss=entity.loss,
            accuracy=entity.accuracy,
            metrics=entity.metrics,
            storage_tier=StorageTier(entity.storage_tier.value),
            status=CheckpointStatus(entity.status.value),
            archived_at=entity.archived_at,
            deleted_at=entity.deleted_at,
        )

    async def get_by_id(self, checkpoint_id: int) -> Checkpoint | None:
        """Get checkpoint by ID."""
        result = await self._session.execute(
            select(CheckpointModel).where(CheckpointModel.id == checkpoint_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_training_job_id(self, training_job_id: int) -> list[Checkpoint]:
        """Get all checkpoints for a training job."""
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .order_by(desc(CheckpointModel.created_at))
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def create(self, checkpoint: Checkpoint) -> Checkpoint:
        """Create a new checkpoint."""
        model = self._entity_to_model(checkpoint)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def update(self, checkpoint: Checkpoint) -> Checkpoint:
        """Update an existing checkpoint."""
        result = await self._session.execute(
            select(CheckpointModel).where(CheckpointModel.id == checkpoint.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Checkpoint with id {checkpoint.id} not found")

        # Update fields
        model.checkpoint_name = checkpoint.checkpoint_name
        model.storage_path = checkpoint.storage_path
        model.size_bytes = checkpoint.size_bytes
        model.checkpoint_type = CheckpointType(checkpoint.checkpoint_type.value)
        model.epoch = checkpoint.epoch
        model.step = checkpoint.step
        model.checksum = checkpoint.checksum
        model.loss = checkpoint.loss
        model.accuracy = checkpoint.accuracy
        model.metrics = checkpoint.metrics
        model.storage_tier = StorageTier(checkpoint.storage_tier.value)
        model.status = CheckpointStatus(checkpoint.status.value)
        model.archived_at = checkpoint.archived_at
        model.deleted_at = checkpoint.deleted_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def delete(self, checkpoint_id: int) -> None:
        """Delete a checkpoint by ID."""
        result = await self._session.execute(
            select(CheckpointModel).where(CheckpointModel.id == checkpoint_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_latest_by_training_job_id(
        self, training_job_id: int
    ) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .order_by(desc(CheckpointModel.created_at))
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)


async def get_checkpoint_repository(session: AsyncSession) -> CheckpointRepository:
    """Factory function for dependency injection."""
    return CheckpointRepository(session)
