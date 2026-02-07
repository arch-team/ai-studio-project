"""资源使用查询实现 - 跨模块 ORM 查询。"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.billing.application.interfaces.resource_usage_query import (
    IResourceUsageQuery,
    StorageStats,
    TrainingJobStats,
    UserTrainingStats,
)
from src.modules.datasets.infrastructure.models.dataset_model import DatasetModel
from src.modules.training.infrastructure.models.training_job_model import TrainingJobModel

_ZERO = Decimal("0")
_GB_DIVISOR = 1024 * 1024 * 1024


def _period_column(date_format: str):
    """构建按时间周期分组的列表达式。"""
    return func.date_format(TrainingJobModel.completed_at, date_format).label("period")


def _period_range_columns():
    """构建周期起止时间的列表达式。"""
    return (
        func.min(TrainingJobModel.completed_at).label("period_start"),
        func.max(TrainingJobModel.completed_at).label("period_end"),
    )


class ResourceUsageQueryImpl(IResourceUsageQuery):
    """资源使用查询实现。"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def build_training_conditions(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: int | None = None,
    ) -> list[Any]:
        """构建训练任务查询条件。"""
        conditions: list[Any] = [
            TrainingJobModel.status == "completed",
            TrainingJobModel.completed_at >= start_date,
            TrainingJobModel.completed_at <= end_date,
        ]
        if user_id:
            conditions.append(TrainingJobModel.owner_id == user_id)
        return conditions

    async def get_training_job_stats_by_period(
        self,
        date_format: str,
        conditions: list[Any],
    ) -> list[TrainingJobStats]:
        """按时间维度聚合训练任务统计。"""
        period_col = _period_column(date_format)
        stmt = (
            select(
                period_col,
                *_period_range_columns(),
                func.coalesce(
                    func.sum(TrainingJobModel.duration_seconds / Decimal("3600") * TrainingJobModel.node_count),
                    _ZERO,
                ).label("cpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), _ZERO).label("gpu_hours"),
                func.count(TrainingJobModel.id).label("job_count"),
            )
            .where(and_(*conditions))
            .group_by(period_col)
            .order_by(period_col)
        )
        result = await self._session.execute(stmt)
        return [
            TrainingJobStats(
                period=row.period,
                period_start=row.period_start,
                period_end=row.period_end,
                cpu_hours=row.cpu_hours,
                gpu_hours=row.gpu_hours,
                job_count=row.job_count,
            )
            for row in result.all()
        ]

    async def get_storage_stats_by_user(self, user_id: int) -> StorageStats:
        """获取用户存储统计。"""
        stmt = (
            select(
                func.coalesce(func.sum(DatasetModel.total_size_bytes / _GB_DIVISOR), _ZERO).label("total_gb"),
                func.coalesce(func.sum(DatasetModel.total_size_bytes), 0).label("total_bytes"),
            )
            .where(DatasetModel.owner_id == user_id)
            .where(DatasetModel.status == "available")
        )
        row = (await self._session.execute(stmt)).one()
        return StorageStats(total_size_bytes=row.total_bytes, total_gb=row.total_gb or _ZERO)

    async def get_training_cost_by_period(
        self,
        date_format: str,
        conditions: list[Any],
        compute_ratio: Decimal,
        storage_ratio: Decimal,
        network_ratio: Decimal,
    ) -> list[dict]:
        """按时间维度聚合训练成本。"""
        period_col = _period_column(date_format)
        cost_col = TrainingJobModel.estimated_cost_usd
        stmt = (
            select(
                period_col,
                *_period_range_columns(),
                func.coalesce(func.sum(cost_col * compute_ratio), _ZERO).label("compute_cost"),
                func.coalesce(func.sum(cost_col * storage_ratio), _ZERO).label("storage_cost"),
                func.coalesce(func.sum(cost_col * network_ratio), _ZERO).label("network_cost"),
                func.coalesce(func.sum(cost_col), _ZERO).label("total_cost"),
            )
            .where(and_(*conditions))
            .group_by(period_col)
            .order_by(period_col)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "period_start": row.period_start,
                "period_end": row.period_end,
                "compute_cost": row.compute_cost,
                "storage_cost": row.storage_cost,
                "network_cost": row.network_cost,
                "total_cost": row.total_cost,
            }
            for row in result.all()
        ]

    async def get_user_training_aggregate(self, user_id: int) -> UserTrainingStats:
        """获取用户训练任务聚合。"""
        stmt = (
            select(
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), _ZERO).label("total_gpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd), _ZERO).label("total_cost_usd"),
                func.count(TrainingJobModel.id).label("job_count"),
            )
            .where(TrainingJobModel.owner_id == user_id)
            .where(TrainingJobModel.status == "completed")
        )
        row = (await self._session.execute(stmt)).one()
        return UserTrainingStats(
            user_id=user_id,
            total_gpu_hours=row.total_gpu_hours,
            total_cost_usd=row.total_cost_usd,
            job_count=row.job_count,
        )

    async def get_user_training_by_period(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        date_format: str,
    ) -> list[TrainingJobStats]:
        """按用户和时间维度聚合训练统计。"""
        period_col = _period_column(date_format)
        stmt = (
            select(
                period_col,
                *_period_range_columns(),
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), _ZERO).label("gpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd), _ZERO).label("total_cost_usd"),
                func.count(TrainingJobModel.id).label("job_count"),
            )
            .where(
                and_(
                    TrainingJobModel.owner_id == user_id,
                    TrainingJobModel.status == "completed",
                    TrainingJobModel.completed_at >= start_date,
                    TrainingJobModel.completed_at <= end_date,
                )
            )
            .group_by(period_col)
            .order_by(period_col)
        )
        result = await self._session.execute(stmt)
        return [
            TrainingJobStats(
                period=row.period,
                period_start=row.period_start,
                period_end=row.period_end,
                gpu_hours=row.gpu_hours,
                estimated_cost_usd=row.total_cost_usd,
                job_count=row.job_count,
            )
            for row in result.all()
        ]

    async def get_all_users_training_aggregate(self) -> list[UserTrainingStats]:
        """聚合所有用户的训练数据。"""
        stmt = (
            select(
                TrainingJobModel.owner_id,
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), _ZERO).label("total_gpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd), _ZERO).label("total_cost_usd"),
                func.count(TrainingJobModel.id).label("job_count"),
            )
            .where(TrainingJobModel.status == "completed")
            .group_by(TrainingJobModel.owner_id)
        )
        return [
            UserTrainingStats(
                user_id=row.owner_id,
                total_gpu_hours=row.total_gpu_hours,
                total_cost_usd=row.total_cost_usd,
                job_count=row.job_count,
            )
            for row in (await self._session.execute(stmt)).all()
        ]

    async def get_all_users_storage_aggregate(self) -> dict[int, int]:
        """聚合所有用户的存储数据，返回 {user_id: total_storage_bytes}。"""
        stmt = (
            select(
                DatasetModel.owner_id,
                func.coalesce(func.sum(DatasetModel.total_size_bytes), 0).label("total_storage_bytes"),
            )
            .where(DatasetModel.status == "available")
            .group_by(DatasetModel.owner_id)
        )
        return {row.owner_id: row.total_storage_bytes for row in (await self._session.execute(stmt)).all()}
