"""TrainingJob Repository Implementation - SQLAlchemy data access."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import TrainingJob
from ...domain.repositories import ITrainingJobRepository
from ...domain.value_objects import JobPriority, JobStatus
from ..models import TrainingJobModel


class TrainingJobRepository(PydanticRepository[TrainingJob, TrainingJobModel, int], ITrainingJobRepository):
    """SQLAlchemy implementation of TrainingJob repository.

    使用 PydanticRepository 自动处理 Entity ↔ Model 转换。
    """

    _entity_class = TrainingJob
    _updatable_fields = [
        # Status fields
        "status",
        "hyperpod_status",
        "kueue_status",
        # Pod statistics
        "running_pods",
        "failed_pods",
        "preemption_count",
        # Training metrics
        "current_epoch",
        "current_step",
        "latest_loss",
        "latest_accuracy",
        # Time statistics
        "started_at",
        "completed_at",
        "duration_seconds",
        # Error information
        "error_message",
        "failure_reason",
        # HyperPod ARN (set after job submission)
        "hyperpod_job_arn",
        "kueue_workload_name",
        # Cost statistics
        "total_gpu_hours",
        "estimated_cost_usd",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, TrainingJobModel)

    # ========== Domain-specific queries ==========

    async def get_by_name(self, job_name: str) -> TrainingJob | None:
        """Get training job by unique name."""
        result = await self._session.execute(select(TrainingJobModel).where(TrainingJobModel.job_name == job_name))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

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
        query = select(TrainingJobModel)
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
            count_query = count_query.where(TrainingJobModel.submitted_at >= submitted_after)

        if submitted_before is not None:
            query = query.where(TrainingJobModel.submitted_at <= submitted_before)
            count_query = count_query.where(TrainingJobModel.submitted_at <= submitted_before)

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

        return [self._to_entity(m) for m in models], total

    async def exists_by_name(self, job_name: str) -> bool:
        """Check if a job with the given name exists."""
        result = await self._session.execute(
            select(func.count(TrainingJobModel.id)).where(TrainingJobModel.job_name == job_name)
        )
        count = result.scalar() or 0
        return count > 0
