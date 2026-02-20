"""训练成本定价模型服务 - 维护 AWS HyperPod 实例/存储/网络传输成本数据。"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.shared.utils import utc_now


@dataclass(frozen=True)
class InstancePricing:
    """实例定价数据."""

    instance_type: str
    hourly_rate: Decimal
    gpu_count: int
    gpu_type: str
    cpu_cores: int
    memory_gb: int
    region: str


@dataclass(frozen=True)
class StoragePricing:
    """存储定价数据."""

    storage_type: str
    storage_rate_per_gb_month: Decimal
    throughput_rate_per_mb_s: Decimal = Decimal("0.0")
    region: str = "us-east-1"


@dataclass(frozen=True)
class NetworkPricing:
    """网络传输定价数据."""

    transfer_type: str
    rate_per_gb: Decimal
    region: str


class PricingModelService:
    """定价模型服务 - 维护 AWS 资源定价数据，支持按区域查询."""

    PRICING_VERSION = "2026-01-27"

    def __init__(self, default_region: str = "us-east-1"):
        self.default_region = default_region
        self.last_updated = utc_now()
        self._instance_pricing_data = self._initialize_instance_pricing()
        self._storage_pricing_data = self._initialize_storage_pricing()
        self._network_pricing_data = self._initialize_network_pricing()

    @property
    def pricing_version(self) -> str:
        return self.PRICING_VERSION

    def get_instance_rate(self, instance_type: str, region: str | None = None) -> InstancePricing | None:
        """获取实例定价."""
        return self._instance_pricing_data.get((instance_type, region or self.default_region))

    def get_storage_rate(self, storage_type: str, region: str | None = None) -> StoragePricing | None:
        """获取存储定价."""
        return self._storage_pricing_data.get((storage_type, region or self.default_region))

    def get_network_rate(self, transfer_type: str, region: str | None = None) -> NetworkPricing | None:
        """获取网络传输定价."""
        return self._network_pricing_data.get((transfer_type, region or self.default_region))

    def _initialize_instance_pricing(self) -> dict[tuple[str, str], InstancePricing]:
        """初始化实例定价数据 (us-east-1, 2026-01-27 更新)."""
        # (instance_type, hourly_rate, gpu_count, gpu_type, cpu_cores, memory_gb)
        specs = [
            ("p4d.24xlarge", "32.77", 8, "A100 40GB", 96, 1152),
            ("p5.48xlarge", "98.32", 8, "H100 80GB", 192, 2048),
            ("trn1.32xlarge", "21.50", 16, "Trainium", 128, 512),
            ("ml.g5.xlarge", "1.006", 1, "A10G", 4, 16),
            ("ml.g5.2xlarge", "1.212", 1, "A10G", 8, 32),
        ]
        pricing_data = [
            InstancePricing(
                instance_type=itype,
                hourly_rate=Decimal(rate),
                gpu_count=gpus,
                gpu_type=gtype,
                cpu_cores=cpus,
                memory_gb=mem,
                region="us-east-1",
            )
            for itype, rate, gpus, gtype, cpus, mem in specs
        ]
        return {(p.instance_type, p.region): p for p in pricing_data}

    def _initialize_storage_pricing(self) -> dict[tuple[str, str], StoragePricing]:
        """初始化存储定价数据 (us-east-1, 2026-01-27 更新)."""
        pricing_data = [
            # FSx for Lustre (SSD, Persistent_2, 500 MB/s/TiB 吞吐量)
            StoragePricing(
                storage_type="fsx_lustre",
                storage_rate_per_gb_month=Decimal("0.145"),
                throughput_rate_per_mb_s=Decimal("0.0"),  # 包含在存储定价中
                region="us-east-1",
            ),
            # S3 Standard
            StoragePricing(
                storage_type="s3_standard",
                storage_rate_per_gb_month=Decimal("0.023"),
                throughput_rate_per_mb_s=Decimal("0.0"),  # S3 无吞吐量定价
                region="us-east-1",
            ),
        ]

        return {(p.storage_type, p.region): p for p in pricing_data}

    def _initialize_network_pricing(self) -> dict[tuple[str, str], NetworkPricing]:
        """初始化网络传输定价数据 (us-east-1, 2026-01-27 更新)."""
        pricing_data = [
            # 跨 AZ 传输
            NetworkPricing(
                transfer_type="cross_az",
                rate_per_gb=Decimal("0.01"),
                region="us-east-1",
            ),
            # 同 VPC 传输 (免费)
            NetworkPricing(
                transfer_type="same_vpc",
                rate_per_gb=Decimal("0.0"),
                region="us-east-1",
            ),
            # S3 数据传输出站
            NetworkPricing(
                transfer_type="s3_egress",
                rate_per_gb=Decimal("0.09"),
                region="us-east-1",
            ),
        ]

        return {(p.transfer_type, p.region): p for p in pricing_data}
