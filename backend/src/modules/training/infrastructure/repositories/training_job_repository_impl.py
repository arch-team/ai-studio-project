"""TrainingJob Repository Implementation - SQLAlchemy data access."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository
from src.shared.utils import calculate_offset

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
        # 构建查询
        query = select(TrainingJobModel)
        count_query = select(func.count(TrainingJobModel.id))

        # 应用过滤条件
        query, count_query = self._apply_job_filters(
            query, count_query, owner_id, status, priority, submitted_after, submitted_before
        )

        # 获取总数
        total = await self._get_job_count(count_query)

        # 应用排序和分页
        query = self._apply_job_sorting(query, sort_by, sort_order)
        query = self._apply_job_pagination(query, page, page_size)

        # 执行查询
        jobs = await self._execute_job_query(query)
        return [self._to_entity(j) for j in jobs], total

    def _apply_job_filters(
        self,
        query: Select[Any],
        count_query: Select[Any],
        owner_id: int | None,
        status: JobStatus | None,
        priority: JobPriority | None,
        submitted_after: datetime | None,
        submitted_before: datetime | None,
    ) -> tuple[Select[Any], Select[Any]]:
        """应用任务过滤条件."""
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

        return query, count_query

    async def _get_job_count(self, count_query: Select[Any]) -> int:
        """获取任务总数."""
        result = await self._session.execute(count_query)
        return result.scalar() or 0

    def _apply_job_sorting(self, query: Select[Any], sort_by: str, sort_order: str) -> Select[Any]:
        """应用排序."""
        sort_column = getattr(TrainingJobModel, sort_by, TrainingJobModel.created_at)
        return query.order_by(sort_column.desc() if sort_order.lower() == "desc" else sort_column.asc())

    def _apply_job_pagination(self, query: Select[Any], page: int, page_size: int) -> Select[Any]:
        """应用分页."""
        offset = calculate_offset(page, page_size)
        return query.offset(offset).limit(page_size)

    async def _execute_job_query(self, query: Select[Any]) -> Sequence[Any]:
        """执行查询."""
        result = await self._session.execute(query)
        return result.scalars().all()

    async def list_by_statuses(self, statuses: list[JobStatus], page_size: int = 1000) -> list[TrainingJob]:
        """通过多个状态批量查询，等效于 WHERE status IN (...)."""
        status_values = [s.value for s in statuses]
        stmt = select(TrainingJobModel).where(TrainingJobModel.status.in_(status_values)).limit(page_size)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def exists_by_name(self, job_name: str) -> bool:
        """Check if a job with the given name exists."""
        result = await self._session.execute(
            select(func.count(TrainingJobModel.id)).where(TrainingJobModel.job_name == job_name)
        )
        count = result.scalar() or 0
        return count > 0
