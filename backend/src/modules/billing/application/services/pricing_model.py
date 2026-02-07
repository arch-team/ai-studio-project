"""
训练成本定价模型服务

维护 AWS HyperPod 实例定价、存储定价、网络传输成本数据
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class InstancePricing:
    """
    实例定价数据

    Attributes:
        instance_type: 实例类型 (e.g., p4d.24xlarge, p5.48xlarge)
        hourly_rate: 每小时价格 (USD)
        gpu_count: GPU 数量
        gpu_type: GPU 类型 (e.g., A100 40GB, H100 80GB, Trainium)
        cpu_cores: CPU 核心数
        memory_gb: 内存大小 (GB)
        region: AWS 区域
    """

    instance_type: str
    hourly_rate: Decimal
    gpu_count: int
    gpu_type: str
    cpu_cores: int
    memory_gb: int
    region: str


@dataclass(frozen=True)
class StoragePricing:
    """
    存储定价数据

    Attributes:
        storage_type: 存储类型 (e.g., fsx_lustre, s3_standard)
        storage_rate_per_gb_month: 每 GB 每月价格 (USD)
        throughput_rate_per_mb_s: 吞吐量每 MB/s 价格 (USD/月, FSx 特有)
        region: AWS 区域
    """

    storage_type: str
    storage_rate_per_gb_month: Decimal
    throughput_rate_per_mb_s: Decimal = Decimal("0.0")
    region: str = "us-east-1"


@dataclass(frozen=True)
class NetworkPricing:
    """
    网络传输定价数据

    Attributes:
        transfer_type: 传输类型 (e.g., cross_az, same_vpc, s3_egress)
        rate_per_gb: 每 GB 价格 (USD)
        region: AWS 区域
    """

    transfer_type: str
    rate_per_gb: Decimal
    region: str


class PricingModelService:
    """
    定价模型服务

    维护 AWS 资源定价数据,支持按区域查询定价
    """

    # 定价数据版本 (格式: YYYY-MM-DD)
    PRICING_VERSION = "2026-01-27"

    def __init__(self, default_region: str = "us-east-1"):
        """
        初始化定价模型服务

        Args:
            default_region: 默认 AWS 区域
        """
        self.default_region = default_region
        self.last_updated = datetime.now()

        # 初始化定价数据
        self._instance_pricing_data = self._initialize_instance_pricing()
        self._storage_pricing_data = self._initialize_storage_pricing()
        self._network_pricing_data = self._initialize_network_pricing()

    @property
    def pricing_version(self) -> str:
        """获取定价数据版本"""
        return self.PRICING_VERSION

    def get_instance_rate(self, instance_type: str, region: str | None = None) -> InstancePricing | None:
        """
        获取实例定价

        Args:
            instance_type: 实例类型 (e.g., p4d.24xlarge, p5.48xlarge)
            region: AWS 区域 (默认 us-east-1)

        Returns:
            实例定价数据,如果不存在则返回 None
        """
        region = region or self.default_region

        # 构造查询键
        key = (instance_type, region)

        return self._instance_pricing_data.get(key)

    def get_storage_rate(self, storage_type: str, region: str | None = None) -> StoragePricing | None:
        """
        获取存储定价

        Args:
            storage_type: 存储类型 (e.g., fsx_lustre, s3_standard)
            region: AWS 区域 (默认 us-east-1)

        Returns:
            存储定价数据,如果不存在则返回 None
        """
        region = region or self.default_region

        # 构造查询键
        key = (storage_type, region)

        return self._storage_pricing_data.get(key)

    def get_network_rate(self, transfer_type: str, region: str | None = None) -> NetworkPricing | None:
        """
        获取网络传输定价

        Args:
            transfer_type: 传输类型 (e.g., cross_az, same_vpc, s3_egress)
            region: AWS 区域 (默认 us-east-1)

        Returns:
            网络传输定价数据,如果不存在则返回 None
        """
        region = region or self.default_region

        # 构造查询键
        key = (transfer_type, region)

        return self._network_pricing_data.get(key)

    def _initialize_instance_pricing(self) -> dict[tuple[str, str], InstancePricing]:
        """初始化实例定价数据."""
        pricing_data = [
            self._create_p4d_pricing(),
            self._create_p5_pricing(),
            self._create_trainium_pricing(),
            self._create_g5_xlarge_pricing(),
            self._create_g5_2xlarge_pricing(),
        ]
        return {(p.instance_type, p.region): p for p in pricing_data}

    def _create_p4d_pricing(self) -> InstancePricing:
        """创建 p4d.24xlarge 定价."""
        return InstancePricing(
            instance_type="p4d.24xlarge",
            hourly_rate=Decimal("32.77"),
            gpu_count=8,
            gpu_type="A100 40GB",
            cpu_cores=96,
            memory_gb=1152,
            region="us-east-1",
        )

    def _create_p5_pricing(self) -> InstancePricing:
        """创建 p5.48xlarge 定价."""
        return InstancePricing(
            instance_type="p5.48xlarge",
            hourly_rate=Decimal("98.32"),
            gpu_count=8,
            gpu_type="H100 80GB",
            cpu_cores=192,
            memory_gb=2048,
            region="us-east-1",
        )

    def _create_trainium_pricing(self) -> InstancePricing:
        """创建 trn1.32xlarge 定价."""
        return InstancePricing(
            instance_type="trn1.32xlarge",
            hourly_rate=Decimal("21.50"),
            gpu_count=16,
            gpu_type="Trainium",
            cpu_cores=128,
            memory_gb=512,
            region="us-east-1",
        )

    def _create_g5_xlarge_pricing(self) -> InstancePricing:
        """创建 ml.g5.xlarge 定价."""
        return InstancePricing(
            instance_type="ml.g5.xlarge",
            hourly_rate=Decimal("1.006"),
            gpu_count=1,
            gpu_type="A10G",
            cpu_cores=4,
            memory_gb=16,
            region="us-east-1",
        )

    def _create_g5_2xlarge_pricing(self) -> InstancePricing:
        """创建 ml.g5.2xlarge 定价."""
        return InstancePricing(
            instance_type="ml.g5.2xlarge",
            hourly_rate=Decimal("1.212"),
            gpu_count=1,
            gpu_type="A10G",
            cpu_cores=8,
            memory_gb=32,
            region="us-east-1",
        )

    def _initialize_storage_pricing(
        self,
    ) -> dict[tuple[str, str], StoragePricing]:
        """
        初始化存储定价数据

        Returns:
            存储定价数据字典 {(storage_type, region): StoragePricing}
        """
        # AWS us-east-1 区域定价 (2026-01-27 更新)
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

        # 转换为字典格式
        return {(p.storage_type, p.region): p for p in pricing_data}

    def _initialize_network_pricing(
        self,
    ) -> dict[tuple[str, str], NetworkPricing]:
        """
        初始化网络传输定价数据

        Returns:
            网络传输定价数据字典 {(transfer_type, region): NetworkPricing}
        """
        # AWS us-east-1 区域定价 (2026-01-27 更新)
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

        # 转换为字典格式
        return {(p.transfer_type, p.region): p for p in pricing_data}
