"""成本计算数据模型.

定义计算、存储、网络三个维度的成本模型。
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


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