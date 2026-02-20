"""成本计算引擎核心逻辑 (T069).

协调成本计算、分摊和聚合。
"""

from decimal import Decimal

from src.modules.billing.application.services.cost_allocation import (
    AllocatedCost,
    CostAllocationService,
)
from src.modules.billing.application.services.cost_models import (
    ComputeCost,
    CostBreakdown,
    CostDimension,
    NetworkCost,
    StorageCost,
    TotalCost,
)


class CostCalculator:
    """成本计算引擎.

    提供单任务成本计算和批量聚合功能，支持多维度成本分析。
    """

    def __init__(self) -> None:
        self._allocation_service = CostAllocationService()

    def calculate_job_cost(
        self,
        instance_type: str,
        instance_hourly_rate: Decimal,
        node_count: int,
        training_duration_hours: Decimal,
        storage_size_gb: Decimal,
        storage_rate_per_gb_hour: Decimal,
        data_transfer_gb: Decimal,
        transfer_rate_per_gb: Decimal,
        storage_type: str = "FSx",
        transfer_direction: str = "out",
    ) -> CostBreakdown:
        """计算单个训练任务的成本明细."""
        compute_cost = self._calculate_compute_cost(
            instance_type, instance_hourly_rate, node_count, training_duration_hours
        )

        storage_cost = self._calculate_storage_cost(
            storage_type, storage_size_gb, storage_rate_per_gb_hour, training_duration_hours
        )

        network_cost = self._calculate_network_cost(data_transfer_gb, transfer_rate_per_gb, transfer_direction)

        return CostBreakdown(
            compute_cost=compute_cost,
            storage_cost=storage_cost,
            network_cost=network_cost,
        )

    def _calculate_compute_cost(
        self, instance_type: str, instance_hourly_rate: Decimal, node_count: int, duration_hours: Decimal
    ) -> ComputeCost:
        """计算计算成本."""
        return ComputeCost.calculate(
            instance_type=instance_type,
            instance_hourly_rate=instance_hourly_rate,
            node_count=node_count,
            duration_hours=duration_hours,
        )

    def _calculate_storage_cost(
        self, storage_type: str, storage_size_gb: Decimal, storage_rate_per_gb_hour: Decimal, duration_hours: Decimal
    ) -> StorageCost:
        """计算存储成本."""
        return StorageCost.calculate(
            storage_type=storage_type,
            storage_size_gb=storage_size_gb,
            storage_rate_per_gb_hour=storage_rate_per_gb_hour,
            duration_hours=duration_hours,
        )

    def _calculate_network_cost(
        self, data_transfer_gb: Decimal, transfer_rate_per_gb: Decimal, transfer_direction: str
    ) -> NetworkCost:
        """计算网络成本."""
        return NetworkCost.calculate(
            data_transfer_gb=data_transfer_gb,
            transfer_rate_per_gb=transfer_rate_per_gb,
            transfer_direction=transfer_direction,
        )

    def aggregate_costs(self, breakdowns: list[CostBreakdown]) -> TotalCost:
        """聚合多个任务的成本.

        Args:
            breakdowns: 任务成本明细列表

        Returns:
            聚合后的总成本统计
        """
        return self._allocation_service.aggregate_costs(breakdowns)

    def allocate_by_user(
        self,
        costs: dict[int, list[tuple[int, CostBreakdown]]],  # user_id -> [(job_id, breakdown)]
    ) -> list[AllocatedCost]:
        """按用户维度分摊成本.

        Args:
            costs: 用户 ID 到 (job_id, 成本明细) 列表的映射

        Returns:
            按用户分摊的成本列表
        """
        return self._allocation_service.allocate_by_user(costs)

    def allocate_by_project(
        self,
        costs: dict[str, list[tuple[int, CostBreakdown]]],  # project_id -> [(job_id, breakdown)]
    ) -> list[AllocatedCost]:
        """按项目维度分摊成本.

        Args:
            costs: 项目 ID 到 (job_id, 成本明细) 列表的映射

        Returns:
            按项目分摊的成本列表
        """
        return self._allocation_service.allocate_by_project(costs)

    def allocate_by_time_range(
        self,
        costs: dict[str, list[tuple[int, CostBreakdown]]],  # date_str -> [(job_id, breakdown)]
    ) -> list[AllocatedCost]:
        """按时间范围维度分摊成本.

        Args:
            costs: 日期字符串 (YYYY-MM-DD) 到 (job_id, 成本明细) 列表的映射

        Returns:
            按时间范围分摊的成本列表
        """
        return self._allocation_service.allocate_by_time_range(costs)


# 导出常用类型以保持兼容性
__all__ = [
    "CostCalculator",
    "CostBreakdown",
    "CostDimension",
    "ComputeCost",
    "StorageCost",
    "NetworkCost",
    "TotalCost",
    "AllocatedCost",
]
