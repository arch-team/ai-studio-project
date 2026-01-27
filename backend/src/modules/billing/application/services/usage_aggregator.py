"""资源使用聚合查询服务 - 聚合训练任务和存储资源使用情况。

此服务负责:
1. 按用户聚合资源使用 (训练 GPU 时、存储空间等)
2. 按时间维度分组聚合 (day/week/month)
3. 提供多维度的资源使用统计数据

技术实现:
- 使用 SQLAlchemy 2.0 异步查询
- 使用聚合函数 (SUM, COUNT, AVG)
- 使用 MySQL DATE_FORMAT 进行时间分组
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.datasets.infrastructure.models.dataset_model import DatasetModel
from src.modules.training.infrastructure.models.training_job_model import TrainingJobModel

# 时间维度类型
TimePeriod = Literal["day", "week", "month"]


@dataclass
class UserResourceUsage:
    """用户资源使用摘要。"""

    user_id: int
    total_gpu_hours: Decimal
    total_cost_usd: Decimal
    total_storage_bytes: int
    total_training_jobs: int


@dataclass
class TimeSeriesUsage:
    """时间序列资源使用数据。"""

    period_start: datetime
    period_end: datetime | None
    total_gpu_hours: Decimal
    total_cost_usd: Decimal
    job_count: int


@dataclass
class ResourceUsageSummary:
    """资源使用汇总 (用于多用户场景)。"""

    user_id: int
    total_gpu_hours: Decimal
    total_cost_usd: Decimal
    total_storage_bytes: int
    total_training_jobs: int


class UsageAggregatorService:
    """资源使用聚合服务 - 提供多维度资源使用统计。"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def aggregate_by_user(self, user_id: int) -> UserResourceUsage:
        """按用户聚合资源使用。

        聚合内容:
        - 训练任务的总 GPU 时数
        - 训练任务的总成本
        - 数据集的总存储空间
        - 训练任务总数

        Args:
            user_id: 用户 ID

        Returns:
            UserResourceUsage: 用户资源使用摘要
        """
        # 聚合训练任务数据
        training_stmt = (
            select(
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), Decimal("0")).label("total_gpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd), Decimal("0")).label("total_cost_usd"),
                func.count(TrainingJobModel.id).label("job_count"),
            )
            .where(TrainingJobModel.owner_id == user_id)
            .where(TrainingJobModel.status == "completed")
        )

        training_result = await self._session.execute(training_stmt)
        training_row = training_result.one()

        # 聚合存储数据
        storage_stmt = (
            select(func.coalesce(func.sum(DatasetModel.total_size_bytes), 0).label("total_storage_bytes"))
            .where(DatasetModel.owner_id == user_id)
            .where(DatasetModel.status == "available")
        )

        storage_result = await self._session.execute(storage_stmt)
        storage_row = storage_result.one()

        return UserResourceUsage(
            user_id=user_id,
            total_gpu_hours=training_row.total_gpu_hours,
            total_cost_usd=training_row.total_cost_usd,
            total_storage_bytes=storage_row.total_storage_bytes,
            total_training_jobs=training_row.job_count,
        )

    async def aggregate_by_time_period(
        self, user_id: int, start_date: datetime, end_date: datetime, period: TimePeriod
    ) -> list[TimeSeriesUsage]:
        """按时间维度分组聚合资源使用。

        Args:
            user_id: 用户 ID
            start_date: 起始日期
            end_date: 结束日期
            period: 时间维度 (day/week/month)

        Returns:
            list[TimeSeriesUsage]: 时间序列使用数据列表

        Raises:
            ValueError: 如果 period 参数无效
        """
        # 根据时间维度选择 MySQL DATE_FORMAT 格式
        date_format_map = {
            "day": "%Y-%m-%d",
            "week": "%Y-%u",  # ISO week number
            "month": "%Y-%m",
        }

        if period not in date_format_map:
            raise ValueError(f"Invalid period: {period}. Must be one of: day, week, month")

        date_format = date_format_map[period]

        # 使用 MySQL DATE_FORMAT 进行时间分组
        period_column = func.date_format(TrainingJobModel.completed_at, date_format).label("period")

        stmt = (
            select(
                period_column,
                func.min(TrainingJobModel.completed_at).label("period_start"),
                func.max(TrainingJobModel.completed_at).label("period_end"),
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), Decimal("0")).label("total_gpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd), Decimal("0")).label("total_cost_usd"),
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
            .group_by(period_column)
            .order_by(period_column)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            TimeSeriesUsage(
                period_start=row.period_start,
                period_end=row.period_end,
                total_gpu_hours=row.total_gpu_hours,
                total_cost_usd=row.total_cost_usd,
                job_count=row.job_count,
            )
            for row in rows
        ]

    async def aggregate_storage_by_user(self, user_id: int) -> UserResourceUsage:
        """按用户聚合存储使用 (仅存储部分)。

        Args:
            user_id: 用户 ID

        Returns:
            UserResourceUsage: 用户存储使用摘要（其他字段为零）
        """
        stmt = (
            select(
                func.coalesce(func.sum(DatasetModel.total_size_bytes), 0).label("total_storage_bytes"),
                func.count(DatasetModel.id).label("dataset_count"),
            )
            .where(DatasetModel.owner_id == user_id)
            .where(DatasetModel.status == "available")
        )

        result = await self._session.execute(stmt)
        row = result.one()

        return UserResourceUsage(
            user_id=user_id,
            total_gpu_hours=Decimal("0"),
            total_cost_usd=Decimal("0"),
            total_storage_bytes=row.total_storage_bytes,
            total_training_jobs=0,  # 用 dataset_count 替代
        )

    async def aggregate_all_users(self) -> list[ResourceUsageSummary]:
        """聚合所有用户的资源使用。

        Returns:
            list[ResourceUsageSummary]: 所有用户的资源使用摘要列表
        """
        # 聚合训练任务数据（按用户分组）
        training_stmt = (
            select(
                TrainingJobModel.owner_id,
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), Decimal("0")).label("total_gpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd), Decimal("0")).label("total_cost_usd"),
                func.count(TrainingJobModel.id).label("job_count"),
            )
            .where(TrainingJobModel.status == "completed")
            .group_by(TrainingJobModel.owner_id)
        )

        training_result = await self._session.execute(training_stmt)
        training_rows = training_result.all()

        # 聚合存储数据（按用户分组）
        storage_stmt = (
            select(
                DatasetModel.owner_id,
                func.coalesce(func.sum(DatasetModel.total_size_bytes), 0).label("total_storage_bytes"),
            )
            .where(DatasetModel.status == "available")
            .group_by(DatasetModel.owner_id)
        )

        storage_result = await self._session.execute(storage_stmt)
        storage_rows = storage_result.all()

        # 创建存储数据字典便于查找
        storage_map = {row.owner_id: row.total_storage_bytes for row in storage_rows}

        # 合并训练和存储数据
        summaries = []
        for row in training_rows:
            summaries.append(
                ResourceUsageSummary(
                    user_id=row.owner_id,
                    total_gpu_hours=row.total_gpu_hours,
                    total_cost_usd=row.total_cost_usd,
                    total_storage_bytes=storage_map.get(row.owner_id, 0),
                    total_training_jobs=row.job_count,
                )
            )

        # 添加只有存储数据没有训练任务的用户
        training_user_ids = {row.owner_id for row in training_rows}
        for owner_id, total_storage in storage_map.items():
            if owner_id not in training_user_ids:
                summaries.append(
                    ResourceUsageSummary(
                        user_id=owner_id,
                        total_gpu_hours=Decimal("0"),
                        total_cost_usd=Decimal("0"),
                        total_storage_bytes=total_storage,
                        total_training_jobs=0,
                    )
                )

        return summaries
