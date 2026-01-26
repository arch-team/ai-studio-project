"""Checkpoint Repository Implementation - SQLAlchemy data access."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import Checkpoint
from ...domain.repositories import ICheckpointRepository
from ...domain.value_objects import CheckpointStatus, StorageTier
from ..models import CheckpointModel


class CheckpointRepository(PydanticRepository[Checkpoint, CheckpointModel, int], ICheckpointRepository):
    """SQLAlchemy implementation of Checkpoint repository."""

    _entity_class = Checkpoint
    _updatable_fields = [
        "storage_tier",
        "status",
        "archived_at",
        "deleted_at",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, CheckpointModel)

    # ========== ICheckpointRepository 接口方法 ==========

    async def get_by_training_job_id(self, training_job_id: int) -> list[Checkpoint]:
        """Get all checkpoints for a training job."""
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .order_by(CheckpointModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def delete(self, checkpoint_id: int) -> None:
        """Delete a checkpoint by ID."""
        await super().delete(checkpoint_id)

    async def get_latest_by_training_job_id(self, training_job_id: int) -> Checkpoint | None:
        """Get the latest checkpoint for a training job."""
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .order_by(CheckpointModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def count_by_training_job_id(self, training_job_id: int) -> int:
        """Count checkpoints for a training job."""
        result = await self._session.execute(
            select(func.count(CheckpointModel.id))
            .where(CheckpointModel.training_job_id == training_job_id)
            .where(CheckpointModel.status != CheckpointStatus.DELETED)
        )
        return result.scalar_one()

    async def get_by_storage_tier(self, storage_tier: StorageTier, limit: int = 100) -> list[Checkpoint]:
        """Get checkpoints by storage tier for migration."""
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.storage_tier == storage_tier)
            .where(CheckpointModel.status == CheckpointStatus.AVAILABLE)
            .order_by(CheckpointModel.created_at.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_checkpoints_for_migration(
        self,
        training_job_id: int,
        exclude_latest_count: int = 3,
    ) -> list[Checkpoint]:
        """Get checkpoints eligible for migration (excluding latest N)."""
        latest_ids_subquery = (
            select(CheckpointModel.id)
            .where(CheckpointModel.training_job_id == training_job_id)
            .where(CheckpointModel.status == CheckpointStatus.AVAILABLE)
            .order_by(CheckpointModel.created_at.desc())
            .limit(exclude_latest_count)
        ).scalar_subquery()

        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .where(CheckpointModel.status == CheckpointStatus.AVAILABLE)
            .where(CheckpointModel.id.not_in(latest_ids_subquery))
            .order_by(CheckpointModel.created_at.asc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_oldest_checkpoints(
        self,
        training_job_id: int,
        hours_threshold: int = 72,
    ) -> list[Checkpoint]:
        """Get checkpoints older than threshold for archival."""
        threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)
        result = await self._session.execute(
            select(CheckpointModel)
            .where(CheckpointModel.training_job_id == training_job_id)
            .where(CheckpointModel.status == CheckpointStatus.AVAILABLE)
            .where(CheckpointModel.created_at < threshold_time)
            .order_by(CheckpointModel.created_at.asc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
