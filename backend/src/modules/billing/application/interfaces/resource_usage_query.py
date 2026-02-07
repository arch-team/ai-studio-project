"""资源使用查询接口 - 跨模块数据查询抽象。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class TrainingJobStats:
    """训练任务统计数据。"""

    period: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    cpu_hours: Decimal = Decimal("0")
    gpu_hours: Decimal = Decimal("0")
    estimated_cost_usd: Decimal = Decimal("0")
    job_count: int = 0


@dataclass
class StorageStats:
    """存储统计数据。"""

    total_size_bytes: int = 0
    total_gb: Decimal = Decimal("0")


@dataclass
class UserTrainingStats:
    """用户训练任务聚合数据。"""

    user_id: int
    total_gpu_hours: Decimal = Decimal("0")
    total_cost_usd: Decimal = Decimal("0")
    job_count: int = 0


class IResourceUsageQuery(ABC):
    """资源使用查询接口 - 供 billing 模块使用。

    实现在 billing/infrastructure 层，查询 training 和 datasets 模块的数据。
    """

    @abstractmethod
    async def get_training_job_stats_by_period(
        self,
        date_format: str,
        conditions: list[Any],
    ) -> list[TrainingJobStats]:
        """按时间维度聚合训练任务统计。"""

    @abstractmethod
    async def get_storage_stats_by_user(self, user_id: int) -> StorageStats:
        """获取用户存储统计。"""

    @abstractmethod
    async def get_training_cost_by_period(
        self,
        date_format: str,
        conditions: list[Any],
        compute_ratio: Decimal,
        storage_ratio: Decimal,
        network_ratio: Decimal,
    ) -> list[dict]:
        """按时间维度聚合训练成本。"""

    @abstractmethod
    async def get_user_training_aggregate(self, user_id: int) -> UserTrainingStats:
        """获取用户训练任务聚合。"""

    @abstractmethod
    async def get_user_training_by_period(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        date_format: str,
    ) -> list[TrainingJobStats]:
        """按用户和时间维度聚合训练统计。"""

    @abstractmethod
    async def get_all_users_training_aggregate(self) -> list[UserTrainingStats]:
        """聚合所有用户的训练数据。"""

    @abstractmethod
    async def get_all_users_storage_aggregate(self) -> dict[int, int]:
        """聚合所有用户的存储数据，返回 {user_id: total_storage_bytes}。"""

    @abstractmethod
    async def build_training_conditions(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: int | None = None,
    ) -> list[Any]:
        """构建训练任务查询条件。"""
