"""成本计算引擎核心逻辑 (T069).

实现多维度成本分析 (compute/storage/network)、成本累加和分摊逻辑。
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal


class CostDimension(str, Enum):
    """成本维度枚举."""

    COMPUTE = "compute"  # 计算成本 (EC2 实例)
    STORAGE = "storage"  # 存储成本 (FSx, S3, EBS)
    NETWORK = "network"  # 网络传输成本


@dataclass
class ComputeCost:
    """计算成本详细信息."""

    instance_type: str
    instance_hourly_rate: Decimal
    node_count: int
    duration_hours: Decimal
    total_cost: Decimal

    @classmethod
    def calculate(
        cls,
        instance_type: str,
        instance_hourly_rate: Decimal,
        node_count: int,
        duration_hours: Decimal,
    ) -> "ComputeCost":
        """计算计算成本.

        公式: total = instance_hourly_rate × node_count × duration_hours
        """
        total_cost = instance_hourly_rate * node_count * duration_hours
        return cls(
            instance_type=instance_type,
            instance_hourly_rate=instance_hourly_rate,
            node_count=node_count,
            duration_hours=duration_hours,
            total_cost=total_cost,
        )


@dataclass
class StorageCost:
    """存储成本详细信息."""

    storage_type: str  # FSx, S3, EBS
    storage_size_gb: Decimal
    storage_rate_per_gb_hour: Decimal
    duration_hours: Decimal
    total_cost: Decimal

    @classmethod
    def calculate(
        cls,
        storage_type: str,
        storage_size_gb: Decimal,
        storage_rate_per_gb_hour: Decimal,
        duration_hours: Decimal,
    ) -> "StorageCost":
        """计算存储成本.

        公式: total = storage_size_gb × storage_rate_per_gb_hour × duration_hours
        """
        total_cost = storage_size_gb * storage_rate_per_gb_hour * duration_hours
        return cls(
            storage_type=storage_type,
            storage_size_gb=storage_size_gb,
            storage_rate_per_gb_hour=storage_rate_per_gb_hour,
            duration_hours=duration_hours,
            total_cost=total_cost,
        )


@dataclass
class NetworkCost:
    """网络传输成本详细信息."""

    data_transfer_gb: Decimal
    transfer_rate_per_gb: Decimal
    transfer_direction: str  # in, out, inter-region
    total_cost: Decimal

    @classmethod
    def calculate(
        cls,
        data_transfer_gb: Decimal,
        transfer_rate_per_gb: Decimal,
        transfer_direction: str = "out",
    ) -> "NetworkCost":
        """计算网络传输成本.

        公式: total = data_transfer_gb × transfer_rate_per_gb
        """
        total_cost = data_transfer_gb * transfer_rate_per_gb
        return cls(
            data_transfer_gb=data_transfer_gb,
            transfer_rate_per_gb=transfer_rate_per_gb,
            transfer_direction=transfer_direction,
            total_cost=total_cost,
        )


@dataclass
class CostBreakdown:
    """成本明细分解."""

    compute_cost: ComputeCost
    storage_cost: StorageCost
    network_cost: NetworkCost

    @property
    def total_cost(self) -> Decimal:
        """总成本 = 计算 + 存储 + 网络."""
        return self.compute_cost.total_cost + self.storage_cost.total_cost + self.network_cost.total_cost

    def to_dict(self) -> dict:
        """转换为字典格式."""
        return {
            "compute": {
                "instance_type": self.compute_cost.instance_type,
                "node_count": self.compute_cost.node_count,
                "duration_hours": float(self.compute_cost.duration_hours),
                "hourly_rate": float(self.compute_cost.instance_hourly_rate),
                "total": float(self.compute_cost.total_cost),
            },
            "storage": {
                "storage_type": self.storage_cost.storage_type,
                "size_gb": float(self.storage_cost.storage_size_gb),
                "rate_per_gb_hour": float(self.storage_cost.storage_rate_per_gb_hour),
                "duration_hours": float(self.storage_cost.duration_hours),
                "total": float(self.storage_cost.total_cost),
            },
            "network": {
                "data_transfer_gb": float(self.network_cost.data_transfer_gb),
                "rate_per_gb": float(self.network_cost.transfer_rate_per_gb),
                "direction": self.network_cost.transfer_direction,
                "total": float(self.network_cost.total_cost),
            },
            "total": float(self.total_cost),
        }


@dataclass
class TotalCost:
    """总成本统计."""

    total_compute: Decimal
    total_storage: Decimal
    total_network: Decimal
    grand_total: Decimal
    job_count: int

    def to_dict(self) -> dict:
        """转换为字典格式."""
        return {
            "compute": float(self.total_compute),
            "storage": float(self.total_storage),
            "network": float(self.total_network),
            "total": float(self.grand_total),
            "job_count": self.job_count,
        }


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


class CostCalculator:
    """成本计算引擎.

    提供单任务成本计算和批量聚合功能，支持多维度成本分析。
    """

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
        """计算单个训练任务的成本明细.

        Args:
            instance_type: 实例类型 (p4d.24xlarge, p5.48xlarge, ...)
            instance_hourly_rate: 实例小时价格
            node_count: 节点数量
            training_duration_hours: 训练时长（小时）
            storage_size_gb: 存储空间大小 (GB)
            storage_rate_per_gb_hour: 存储每 GB 每小时价格
            data_transfer_gb: 数据传输量 (GB)
            transfer_rate_per_gb: 数据传输每 GB 价格
            storage_type: 存储类型 (FSx, S3, EBS)
            transfer_direction: 传输方向 (in, out, inter-region)

        Returns:
            包含计算、存储、网络三维度的成本明细
        """
        compute_cost = ComputeCost.calculate(
            instance_type=instance_type,
            instance_hourly_rate=instance_hourly_rate,
            node_count=node_count,
            duration_hours=training_duration_hours,
        )

        storage_cost = StorageCost.calculate(
            storage_type=storage_type,
            storage_size_gb=storage_size_gb,
            storage_rate_per_gb_hour=storage_rate_per_gb_hour,
            duration_hours=training_duration_hours,
        )

        network_cost = NetworkCost.calculate(
            data_transfer_gb=data_transfer_gb,
            transfer_rate_per_gb=transfer_rate_per_gb,
            transfer_direction=transfer_direction,
        )

        return CostBreakdown(
            compute_cost=compute_cost,
            storage_cost=storage_cost,
            network_cost=network_cost,
        )

    def aggregate_costs(self, breakdowns: list[CostBreakdown]) -> TotalCost:
        """聚合多个任务的成本.

        Args:
            breakdowns: 任务成本明细列表

        Returns:
            聚合后的总成本统计
        """
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
        allocated_costs: list[AllocatedCost] = []

        for user_id, job_costs in costs.items():
            job_ids = [job_id for job_id, _ in job_costs]
            breakdowns = [breakdown for _, breakdown in job_costs]
            total = self.aggregate_costs(breakdowns)

            allocated_costs.append(
                AllocatedCost(
                    allocation_key=CostAllocationKey(dimension="user", value=user_id),
                    total_cost=total,
                    jobs=job_ids,
                )
            )

        return allocated_costs

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
        allocated_costs: list[AllocatedCost] = []

        for project_id, job_costs in costs.items():
            job_ids = [job_id for job_id, _ in job_costs]
            breakdowns = [breakdown for _, breakdown in job_costs]
            total = self.aggregate_costs(breakdowns)

            allocated_costs.append(
                AllocatedCost(
                    allocation_key=CostAllocationKey(dimension="project", value=project_id),
                    total_cost=total,
                    jobs=job_ids,
                )
            )

        return allocated_costs

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
        allocated_costs: list[AllocatedCost] = []

        for date_str, job_costs in costs.items():
            job_ids = [job_id for job_id, _ in job_costs]
            breakdowns = [breakdown for _, breakdown in job_costs]
            total = self.aggregate_costs(breakdowns)

            allocated_costs.append(
                AllocatedCost(
                    allocation_key=CostAllocationKey(dimension="time_range", value=date_str),
                    total_cost=total,
                    jobs=job_ids,
                )
            )

        return allocated_costs
