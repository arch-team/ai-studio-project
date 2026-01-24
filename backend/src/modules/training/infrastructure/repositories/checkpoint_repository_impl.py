"""Checkpoint Repository Implementation - SQLAlchemy data access."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.repositories import ICheckpointRepository
from src.modules.training.domain.value_objects import (
    CheckpointStatus,
    CheckpointTriggerType,
    CheckpointType,
    StorageTier,
)
from src.modules.training.infrastructure.models import CheckpointModel
from src.shared.infrastructure.repository_base import EnhancedBaseRepository


class CheckpointRepository(EnhancedBaseRepository[Checkpoint, CheckpointModel, int], ICheckpointRepository):
    """SQLAlchemy implementation of Checkpoint repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CheckpointModel)

    def _to_entity(self, model: CheckpointModel) -> Checkpoint:
        """Convert ORM model to domain entity."""
        return Checkpoint(
            id=model.id,
            training_job_id=model.training_job_id,
            checkpoint_name=model.checkpoint_name,
            storage_path=model.storage_path,
            size_bytes=model.size_bytes,
            checkpoint_type=CheckpointType(model.checkpoint_type.value),
            trigger_type=CheckpointTriggerType(model.trigger_type.value),
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

    def _to_model(self, entity: Checkpoint) -> CheckpointModel:
        """Convert domain entity to ORM model."""
        return CheckpointModel(
            id=entity.id if entity.id else None,
            training_job_id=entity.training_job_id,
            checkpoint_name=entity.checkpoint_name,
            storage_path=entity.storage_path,
            size_bytes=entity.size_bytes,
            checkpoint_type=entity.checkpoint_type,
            trigger_type=entity.trigger_type,
            epoch=entity.epoch,
            step=entity.step,
            checksum=entity.checksum,
            loss=entity.loss,
            accuracy=entity.accuracy,
            metrics=entity.metrics,
            storage_tier=entity.storage_tier,
            status=entity.status,
            archived_at=entity.archived_at,
            deleted_at=entity.deleted_at,
        )

    def _update_model(self, model: CheckpointModel, entity: Checkpoint) -> None:
        """Update ORM model fields from entity."""
        model.storage_tier = entity.storage_tier
        model.status = entity.status
        model.archived_at = entity.archived_at
        model.deleted_at = entity.deleted_at

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

    async def count_by_training_job_id(self, training_job_id: int) -> int:
        """Count checkpoints for a training job."""
        result = await self._session.execute(
            select(func.count(CheckpointModel.id))
            .where(CheckpointModel.training_job_id == training_job_id)
            .where(CheckpointModel.status != CheckpointStatus.DELETED)
        )
        return result.scalar_one()

    async def get_by_storage_tier(
        self, storage_tier: StorageTier, limit: int = 100
    ) -> list[Checkpoint]:
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
        # 子查询: 获取最新 N 个检查点的 ID
        latest_ids_subquery = (
            select(CheckpointModel.id)
            .where(CheckpointModel.training_job_id == training_job_id)
            .where(CheckpointModel.status == CheckpointStatus.AVAILABLE)
            .order_by(CheckpointModel.created_at.desc())
            .limit(exclude_latest_count)
        ).scalar_subquery()

        # 主查询: 排除最新 N 个
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
