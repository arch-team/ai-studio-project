"""Training Job Repository Implementation - SQLAlchemy data access."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.training_job import (
    JobPriority,
    JobStatus,
    TrainingJob,
)
from src.domain.repositories.training_job_repository import ITrainingJobRepository
from src.infrastructure.persistence.models.training_job_model import TrainingJobModel


class TrainingJobRepository(ITrainingJobRepository):
    """SQLAlchemy implementation of training job repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _model_to_entity(self, model: TrainingJobModel) -> TrainingJob:
        """Convert ORM model to domain entity."""
        return TrainingJob(
            id=model.id,
            job_name=model.job_name,
            owner_id=model.owner_id,
            image_uri=model.image_uri,
            instance_type=model.instance_type,
            entrypoint_command=model.entrypoint_command,
            display_name=model.display_name,
            description=model.description,
            node_count=model.node_count,
            tasks_per_node=model.tasks_per_node,
            hyperparameters=model.hyperparameters,
            max_epochs=model.max_epochs,
            batch_size=model.batch_size,
            learning_rate=float(model.learning_rate) if model.learning_rate else None,
            environment_variables=model.environment_variables,
            distribution_strategy=model.distribution_strategy,
            mixed_precision=model.mixed_precision,
            use_spot_instances=model.use_spot_instances,
            spot_interruption_behavior=model.spot_interruption_behavior,
            priority=model.priority,
            status=model.status,
            dataset_id=model.dataset_id,
            data_mount_path=model.data_mount_path,
            checkpoint_mount_path=model.checkpoint_mount_path,
            checkpoint_interval=model.checkpoint_interval,
            hyperpod_status=model.hyperpod_status,
            kueue_workload_name=model.kueue_workload_name,
            kueue_status=model.kueue_status,
            total_pods=model.total_pods,
            running_pods=model.running_pods,
            failed_pods=model.failed_pods,
            preemption_count=model.preemption_count,
            current_epoch=model.current_epoch,
            current_step=model.current_step,
            latest_loss=model.latest_loss,
            latest_accuracy=model.latest_accuracy,
            submitted_at=model.submitted_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            duration_seconds=model.duration_seconds,
            total_gpu_hours=model.total_gpu_hours,
            estimated_cost_usd=model.estimated_cost_usd,
            error_message=model.error_message,
            failure_reason=model.failure_reason,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: TrainingJob) -> TrainingJobModel:
        """Convert domain entity to ORM model."""
        return TrainingJobModel(
            id=entity.id if entity.id else None,
            job_name=entity.job_name,
            owner_id=entity.owner_id,
            image_uri=entity.image_uri,
            instance_type=entity.instance_type,
            entrypoint_command=entity.entrypoint_command,
            display_name=entity.display_name,
            description=entity.description,
            node_count=entity.node_count,
            tasks_per_node=entity.tasks_per_node,
            hyperparameters=entity.hyperparameters,
            max_epochs=entity.max_epochs,
            batch_size=entity.batch_size,
            learning_rate=entity.learning_rate,
            environment_variables=entity.environment_variables,
            distribution_strategy=entity.distribution_strategy,
            mixed_precision=entity.mixed_precision,
            use_spot_instances=entity.use_spot_instances,
            spot_interruption_behavior=entity.spot_interruption_behavior,
            priority=entity.priority,
            status=entity.status,
            dataset_id=entity.dataset_id,
            data_mount_path=entity.data_mount_path,
            checkpoint_mount_path=entity.checkpoint_mount_path,
            checkpoint_interval=entity.checkpoint_interval,
            hyperpod_status=entity.hyperpod_status,
            kueue_workload_name=entity.kueue_workload_name,
            kueue_status=entity.kueue_status,
            total_pods=entity.total_pods,
            running_pods=entity.running_pods,
            failed_pods=entity.failed_pods,
            preemption_count=entity.preemption_count,
            current_epoch=entity.current_epoch,
            current_step=entity.current_step,
            latest_loss=entity.latest_loss,
            latest_accuracy=entity.latest_accuracy,
            submitted_at=entity.submitted_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            duration_seconds=entity.duration_seconds,
            total_gpu_hours=entity.total_gpu_hours,
            estimated_cost_usd=entity.estimated_cost_usd,
            error_message=entity.error_message,
            failure_reason=entity.failure_reason,
        )

    async def get_by_id(self, job_id: int) -> TrainingJob | None:
        """Get training job by ID."""
        result = await self._session.execute(
            select(TrainingJobModel)
            .options(selectinload(TrainingJobModel.owner))
            .where(TrainingJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_name(self, job_name: str) -> TrainingJob | None:
        """Get training job by unique name."""
        result = await self._session.execute(
            select(TrainingJobModel)
            .options(selectinload(TrainingJobModel.owner))
            .where(TrainingJobModel.job_name == job_name)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_jobs(
        self,
        owner_id: int | None = None,
        status: JobStatus | None = None,
        priority: JobPriority | None = None,
        submitted_after: datetime | None = None,
        submitted_before: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[TrainingJob], int]:
        """List training jobs with pagination and filters."""
        # Build base query
        query = select(TrainingJobModel).options(selectinload(TrainingJobModel.owner))
        count_query = select(func.count(TrainingJobModel.id))

        # Apply filters
        if owner_id is not None:
            query = query.where(TrainingJobModel.owner_id == owner_id)
            count_query = count_query.where(TrainingJobModel.owner_id == owner_id)

        if status is not None:
            query = query.where(TrainingJobModel.status == status)
            count_query = count_query.where(TrainingJobModel.status == status)

        if priority is not None:
            query = query.where(TrainingJobModel.priority == priority)
            count_query = count_query.where(TrainingJobModel.priority == priority)

        if submitted_after is not None:
            query = query.where(TrainingJobModel.submitted_at >= submitted_after)
            count_query = count_query.where(
                TrainingJobModel.submitted_at >= submitted_after
            )

        if submitted_before is not None:
            query = query.where(TrainingJobModel.submitted_at <= submitted_before)
            count_query = count_query.where(
                TrainingJobModel.submitted_at <= submitted_before
            )

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(TrainingJobModel, sort_by, TrainingJobModel.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._model_to_entity(m) for m in models], total

    async def create(self, job: TrainingJob) -> TrainingJob:
        """Create a new training job."""
        model = self._entity_to_model(job)
        model.submitted_at = datetime.utcnow()
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def update(self, job: TrainingJob) -> TrainingJob:
        """Update an existing training job."""
        result = await self._session.execute(
            select(TrainingJobModel).where(TrainingJobModel.id == job.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"TrainingJob with id {job.id} not found")

        # Update fields
        model.status = job.status
        model.hyperpod_status = job.hyperpod_status
        model.kueue_workload_name = job.kueue_workload_name
        model.kueue_status = job.kueue_status
        model.total_pods = job.total_pods
        model.running_pods = job.running_pods
        model.failed_pods = job.failed_pods
        model.preemption_count = job.preemption_count
        model.current_epoch = job.current_epoch
        model.current_step = job.current_step
        model.latest_loss = job.latest_loss
        model.latest_accuracy = job.latest_accuracy
        model.started_at = job.started_at
        model.completed_at = job.completed_at
        model.duration_seconds = job.duration_seconds
        model.total_gpu_hours = job.total_gpu_hours
        model.estimated_cost_usd = job.estimated_cost_usd
        model.error_message = job.error_message
        model.failure_reason = job.failure_reason
        model.updated_at = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def soft_delete(self, job_id: int) -> bool:
        """Soft delete a training job."""
        result = await self._session.execute(
            select(TrainingJobModel).where(TrainingJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        # Mark as deleted by setting status to FAILED with a deletion message
        model.status = JobStatus.FAILED
        model.error_message = "Job deleted by user"
        model.failure_reason = "USER_DELETED"
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        return True

    async def exists_by_name(self, job_name: str) -> bool:
        """Check if a job with the given name exists."""
        result = await self._session.execute(
            select(func.count(TrainingJobModel.id)).where(
                TrainingJobModel.job_name == job_name
            )
        )
        count = result.scalar() or 0
        return count > 0


async def get_training_job_repository(session: AsyncSession) -> TrainingJobRepository:
    """Factory function for dependency injection."""
    return TrainingJobRepository(session)
