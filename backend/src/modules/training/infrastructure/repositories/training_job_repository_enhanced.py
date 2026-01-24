"""Enhanced TrainingJob Repository using the new base class."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.training.domain.entities import TrainingJob
from src.modules.training.domain.repositories import ITrainingJobRepository
from src.modules.training.domain.value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
)
from src.modules.training.infrastructure.models import TrainingJobModel
from src.shared.infrastructure.repository_base import EnhancedBaseRepository


class TrainingJobRepositoryEnhanced(
    EnhancedBaseRepository[TrainingJob, TrainingJobModel, int], ITrainingJobRepository
):
    """Enhanced SQLAlchemy implementation of TrainingJob repository.

    Demonstrates how to use the new EnhancedBaseRepository to reduce boilerplate.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, TrainingJobModel)

    def _to_entity(self, model: TrainingJobModel) -> TrainingJob:
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
            distribution_strategy=DistributionStrategy(model.distribution_strategy.value),
            mixed_precision=model.mixed_precision,
            use_spot_instances=model.use_spot_instances,
            spot_interruption_behavior=(
                SpotInterruptionBehavior(model.spot_interruption_behavior.value)
                if model.spot_interruption_behavior
                else None
            ),
            priority=JobPriority(model.priority.value),
            status=JobStatus(model.status.value),
            dataset_id=model.dataset_id,
            data_mount_path=model.data_mount_path,
            checkpoint_mount_path=model.checkpoint_mount_path,
            checkpoint_interval=model.checkpoint_interval,
            auto_resume_checkpoint_id=model.auto_resume_checkpoint_id,
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

    def _to_model(self, entity: TrainingJob) -> TrainingJobModel:
        """Convert domain entity to ORM model."""
        return TrainingJobModel(
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
        )

    def _update_model(self, model: TrainingJobModel, entity: TrainingJob) -> None:
        """Update ORM model fields from entity."""
        # Update mutable fields only
        model.status = entity.status
        model.hyperpod_status = entity.hyperpod_status
        model.kueue_status = entity.kueue_status
        model.running_pods = entity.running_pods
        model.failed_pods = entity.failed_pods
        model.preemption_count = entity.preemption_count
        model.current_epoch = entity.current_epoch
        model.current_step = entity.current_step
        model.latest_loss = entity.latest_loss
        model.latest_accuracy = entity.latest_accuracy
        model.started_at = entity.started_at
        model.completed_at = entity.completed_at
        model.duration_seconds = entity.duration_seconds
        model.error_message = entity.error_message
        model.failure_reason = entity.failure_reason

    # ========== Custom Methods Using Base Class ==========

    async def get_by_name(self, job_name: str) -> TrainingJob | None:
        """Get training job by unique name."""
        # Use the base class's query builder
        builder = self._create_query_builder()
        builder = builder.with_filter("job_name", job_name)
        items = await builder.execute(self._session)

        if not items:
            return None
        return self._to_entity(items[0])

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
        """List training jobs with pagination and filters.

        Now using the base class's _list_with_filters method.
        """
        # Build filters dict
        filters = {
            "owner_id": owner_id,
            "status": status,
            "priority": priority,
        }

        # Handle date range filters separately for now
        # (Could extend QueryBuilder to support range filters)
        builder = self._create_query_builder()
        builder = builder.with_soft_delete_filter()

        for column_name, value in filters.items():
            if value is not None:
                builder = builder.with_filter(column_name, value)

        # Add date range filters
        if submitted_after is not None:
            builder._query = builder._query.where(
                TrainingJobModel.submitted_at >= submitted_after
            )
            builder._filters.append(TrainingJobModel.submitted_at >= submitted_after)

        if submitted_before is not None:
            builder._query = builder._query.where(
                TrainingJobModel.submitted_at <= submitted_before
            )
            builder._filters.append(TrainingJobModel.submitted_at <= submitted_before)

        # Apply sorting
        builder = builder.with_order_by(sort_by, sort_order)

        # Get total count
        total = await builder.count(self._session)

        # Apply pagination
        builder = builder.with_pagination(page, page_size)

        # Execute query
        items = await builder.execute(self._session)

        # Convert to entities
        entities = [self._to_entity(item) for item in items]

        return entities, total

    async def exists_by_name(self, job_name: str) -> bool:
        """Check if a job with the given name exists.

        Using the base class's exists_by method.
        """
        return await self.exists_by("job_name", job_name)