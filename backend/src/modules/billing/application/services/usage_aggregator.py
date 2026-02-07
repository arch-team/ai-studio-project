"""资源使用聚合查询服务 - 聚合训练任务和存储资源使用情况。"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from src.modules.billing.application.interfaces.resource_usage_query import IResourceUsageQuery

TimePeriod = Literal["day", "week", "month"]

# 时间维度 → MySQL DATE_FORMAT 格式映射
_DATE_FORMAT_MAP: dict[str, str] = {
    "day": "%Y-%m-%d",
    "week": "%Y-%u",
    "month": "%Y-%m",
}


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


class UsageAggregatorService:
    """资源使用聚合服务 - 提供多维度资源使用统计。"""

    def __init__(self, query: IResourceUsageQuery):
        self._query = query

    async def aggregate_by_user(self, user_id: int) -> UserResourceUsage:
        """按用户聚合资源使用。"""
        # 聚合训练任务数据
        training = await self._query.get_user_training_aggregate(user_id)

        # 聚合存储数据
        storage = await self._query.get_storage_stats_by_user(user_id)

        return UserResourceUsage(
            user_id=user_id,
            total_gpu_hours=training.total_gpu_hours,
            total_cost_usd=training.total_cost_usd,
            total_storage_bytes=storage.total_size_bytes,
            total_training_jobs=training.job_count,
        )

    async def aggregate_by_time_period(
        self, user_id: int, start_date: datetime, end_date: datetime, period: TimePeriod
    ) -> list[TimeSeriesUsage]:
        """按时间维度分组聚合资源使用。

        Raises:
            ValueError: 如果 period 参数无效
        """
        if period not in _DATE_FORMAT_MAP:
            raise ValueError(f"Invalid period: {period}. Must be one of: {', '.join(_DATE_FORMAT_MAP)}")

        stats_list = await self._query.get_user_training_by_period(
            user_id, start_date, end_date, _DATE_FORMAT_MAP[period]
        )

        return [
            TimeSeriesUsage(
                period_start=s.period_start,
                period_end=s.period_end,
                total_gpu_hours=s.gpu_hours,
                total_cost_usd=s.estimated_cost_usd,
                job_count=s.job_count,
            )
            for s in stats_list
        ]

    async def aggregate_storage_by_user(self, user_id: int) -> UserResourceUsage:
        """按用户聚合存储使用 (仅存储部分)。"""
        storage = await self._query.get_storage_stats_by_user(user_id)

        return UserResourceUsage(
            user_id=user_id,
            total_gpu_hours=Decimal("0"),
            total_cost_usd=Decimal("0"),
            total_storage_bytes=storage.total_size_bytes,
            total_training_jobs=0,
        )

    async def aggregate_all_users(self) -> list[UserResourceUsage]:
        """聚合所有用户的资源使用。"""
        training_stats = await self._query.get_all_users_training_aggregate()
        storage_map = await self._query.get_all_users_storage_aggregate()

        # 合并训练和存储数据
        training_user_ids = {t.user_id for t in training_stats}
        summaries = [
            UserResourceUsage(
                user_id=t.user_id,
                total_gpu_hours=t.total_gpu_hours,
                total_cost_usd=t.total_cost_usd,
                total_storage_bytes=storage_map.get(t.user_id, 0),
                total_training_jobs=t.job_count,
            )
            for t in training_stats
        ]

        # 添加只有存储数据没有训练任务的用户
        summaries.extend(
            UserResourceUsage(
                user_id=owner_id,
                total_gpu_hours=Decimal("0"),
                total_cost_usd=Decimal("0"),
                total_storage_bytes=total_storage,
                total_training_jobs=0,
            )
            for owner_id, total_storage in storage_map.items()
            if owner_id not in training_user_ids
        )

        return summaries
