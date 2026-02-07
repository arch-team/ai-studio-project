"""成本分摊服务.

负责将成本按照不同维度（用户、项目、时间）进行分摊。
"""

from dataclasses import dataclass
from typing import Any, Literal

from src.modules.billing.application.services.cost_models import CostBreakdown, TotalCost


@dataclass
class CostAllocationKey:
    """成本分摊维度键."""

    dimension: Literal["user", "project", "time_range"]
    value: str | int  # user_id, project_id, or "YYYY-MM-DD"


@dataclass
class AllocatedCost:
    """分摊后的成本."""

    allocation_key: CostAllocationKey
    total_cost: TotalCost
    jobs: list[int]  # job_ids

    def to_dict(self) -> dict:
        """转换为字典格式."""
        return {
            "allocation": {
                "dimension": self.allocation_key.dimension,
                "value": self.allocation_key.value,
            },
            "cost": self.total_cost.to_dict(),
            "job_ids": self.jobs,
        }


class CostAllocationService:
    """成本分摊服务."""

    def aggregate_costs(self, breakdowns: list[CostBreakdown]) -> TotalCost:
        """聚合多个任务的成本.

        Args:
            breakdowns: 任务成本明细列表

        Returns:
            聚合后的总成本统计
        """
        from decimal import Decimal

        total_compute = sum((b.compute_cost.total_cost for b in breakdowns), start=Decimal("0"))
        total_storage = sum((b.storage_cost.total_cost for b in breakdowns), start=Decimal("0"))
        total_network = sum((b.network_cost.total_cost for b in breakdowns), start=Decimal("0"))
        grand_total = total_compute + total_storage + total_network

        return TotalCost(
            total_compute=total_compute,
            total_storage=total_storage,
            total_network=total_network,
            grand_total=grand_total,
            job_count=len(breakdowns),
        )

    def _allocate_costs(
        self,
        costs: dict[Any, list[tuple[int, CostBreakdown]]],
        dimension: Literal["user", "project", "time_range"],
    ) -> list[AllocatedCost]:
        """通用成本分摊方法.

        Args:
            costs: 维度值到 (job_id, 成本明细) 列表的映射
            dimension: 分摊维度

        Returns:
            按指定维度分摊的成本列表
        """
        return [
            AllocatedCost(
                allocation_key=CostAllocationKey(dimension=dimension, value=key),
                total_cost=self.aggregate_costs([breakdown for _, breakdown in job_costs]),
                jobs=[job_id for job_id, _ in job_costs],
            )
            for key, job_costs in costs.items()
        ]

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
        return self._allocate_costs(costs, "user")

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
        return self._allocate_costs(costs, "project")

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
        return self._allocate_costs(costs, "time_range")