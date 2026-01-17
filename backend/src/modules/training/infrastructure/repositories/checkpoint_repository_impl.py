"""Checkpoint Repository Implementation - SQLAlchemy data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.repositories import ICheckpointRepository
from src.modules.training.domain.value_objects import (
    CheckpointStatus,
    CheckpointType,
    StorageTier,
)
from src.modules.training.infrastructure.models import CheckpointModel
from src.shared.domain.exceptions import EntityNotFoundError


class CheckpointRepository(ICheckpointRepository):
    """SQLAlchemy implementation of Checkpoint repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: CheckpointModel) -> Checkpoint:
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

    async def get_by_id(self, checkpoint_id: int) -> Checkpoint | None:
        """Get checkpoint by ID."""
        result = await self._session.execute(
            select(CheckpointModel).where(CheckpointModel.id == checkpoint_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_training_job_id(self, training_job_id: int) -> list[Checkpoint]:
        """Get all checkpoints for a training job."""
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .order_by(CheckpointModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def create(self, checkpoint: Checkpoint) -> Checkpoint:
        """Create a new checkpoint."""
        model = CheckpointModel(
            training_job_id=checkpoint.training_job_id,
            checkpoint_name=checkpoint.checkpoint_name,
            storage_path=checkpoint.storage_path,
            size_bytes=checkpoint.size_bytes,
            checkpoint_type=checkpoint.checkpoint_type,
            epoch=checkpoint.epoch,
            step=checkpoint.step,
            checksum=checkpoint.checksum,
            loss=checkpoint.loss,
            accuracy=checkpoint.accuracy,
            metrics=checkpoint.metrics,
            storage_tier=checkpoint.storage_tier,
            status=checkpoint.status,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, checkpoint: Checkpoint) -> Checkpoint:
        """Update an existing checkpoint."""
        result = await self._session.execute(
            select(CheckpointModel).where(CheckpointModel.id == checkpoint.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise EntityNotFoundError("Checkpoint", str(checkpoint.id))

        # Update fields
        model.storage_tier = checkpoint.storage_tier
        model.status = checkpoint.status
        model.archived_at = checkpoint.archived_at
        model.deleted_at = checkpoint.deleted_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, checkpoint_id: int) -> None:
        """Delete a checkpoint by ID."""
        result = await self._session.execute(
            select(CheckpointModel).where(CheckpointModel.id == checkpoint_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def get_latest_by_training_job_id(
        self, training_job_id: int
    ) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .order_by(CheckpointModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)
