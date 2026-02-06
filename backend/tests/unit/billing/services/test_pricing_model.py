"""
PricingModelService 单元测试

测试覆盖:
1. 实例定价查询
2. FSx 存储定价查询
3. S3 存储定价查询
4. 网络传输成本计算
5. 区域特定定价
6. 定价数据版本管理
"""

from datetime import datetime
from decimal import Decimal

import pytest

from src.modules.billing.application.services.pricing_model import (
    InstancePricing,
    PricingModelService,
    StoragePricing,
    NetworkPricing,
)


class TestPricingDataClasses:
    """测试定价数据类"""

    def test_instance_pricing_creation(self):
        """测试实例定价数据创建"""
        pricing = InstancePricing(
            instance_type="p4d.24xlarge",
            hourly_rate=Decimal("32.77"),
            gpu_count=8,
            gpu_type="A100 40GB",
            cpu_cores=96,
            memory_gb=1152,
            region="us-east-1",
        )

        assert pricing.instance_type == "p4d.24xlarge"
        assert pricing.hourly_rate == Decimal("32.77")
        assert pricing.gpu_count == 8
        assert pricing.gpu_type == "A100 40GB"
        assert pricing.cpu_cores == 96
        assert pricing.memory_gb == 1152
        assert pricing.region == "us-east-1"

    def test_storage_pricing_creation(self):
        """测试存储定价数据创建"""
        pricing = StoragePricing(
            storage_type="fsx_lustre",
            storage_rate_per_gb_month=Decimal("0.145"),
            throughput_rate_per_mb_s=Decimal("0.0"),  # 包含在存储定价中
            region="us-east-1",
        )

        assert pricing.storage_type == "fsx_lustre"
        assert pricing.storage_rate_per_gb_month == Decimal("0.145")
        assert pricing.throughput_rate_per_mb_s == Decimal("0.0")
        assert pricing.region == "us-east-1"

    def test_network_pricing_creation(self):
        """测试网络定价数据创建"""
        pricing = NetworkPricing(
            transfer_type="cross_az",
            rate_per_gb=Decimal("0.01"),
            region="us-east-1",
        )

        assert pricing.transfer_type == "cross_az"
        assert pricing.rate_per_gb == Decimal("0.01")
        assert pricing.region == "us-east-1"


class TestPricingModelService:
    """测试定价模型服务"""

    @pytest.fixture
    def pricing_service(self):
        """创建定价模型服务实例"""
        return PricingModelService(default_region="us-east-1")

    def test_service_initialization(self, pricing_service: PricingModelService):
        """测试服务初始化"""
        assert pricing_service.default_region == "us-east-1"
        assert pricing_service.pricing_version is not None
        assert isinstance(pricing_service.last_updated, datetime)

    def test_get_instance_rate_p4d(self, pricing_service: PricingModelService):
        """测试获取 p4d.24xlarge 定价"""
        pricing = pricing_service.get_instance_rate("p4d.24xlarge")

        assert pricing is not None
        assert pricing.instance_type == "p4d.24xlarge"
        assert pricing.hourly_rate == Decimal("32.77")
        assert pricing.gpu_count == 8
        assert pricing.gpu_type == "A100 40GB"
        assert pricing.region == "us-east-1"

    def test_get_instance_rate_p5(self, pricing_service: PricingModelService):
        """测试获取 p5.48xlarge 定价"""
        pricing = pricing_service.get_instance_rate("p5.48xlarge")

        assert pricing is not None
        assert pricing.instance_type == "p5.48xlarge"
        assert pricing.hourly_rate == Decimal("98.32")
        assert pricing.gpu_count == 8
        assert pricing.gpu_type == "H100 80GB"

    def test_get_instance_rate_trn1(self, pricing_service: PricingModelService):
        """测试获取 trn1.32xlarge 定价"""
        pricing = pricing_service.get_instance_rate("trn1.32xlarge")

        assert pricing is not None
        assert pricing.instance_type == "trn1.32xlarge"
        assert pricing.hourly_rate == Decimal("21.50")
        assert pricing.gpu_count == 16
        assert pricing.gpu_type == "Trainium"

    def test_get_instance_rate_ml_g5_xlarge(self, pricing_service: PricingModelService):
        """测试获取 ml.g5.xlarge 定价"""
        pricing = pricing_service.get_instance_rate("ml.g5.xlarge")

        assert pricing is not None
        assert pricing.instance_type == "ml.g5.xlarge"
        assert pricing.hourly_rate == Decimal("1.006")
        assert pricing.gpu_count == 1
        assert pricing.gpu_type == "A10G"

    def test_get_instance_rate_ml_g5_2xlarge(self, pricing_service: PricingModelService):
        """测试获取 ml.g5.2xlarge 定价"""
        pricing = pricing_service.get_instance_rate("ml.g5.2xlarge")

        assert pricing is not None
        assert pricing.instance_type == "ml.g5.2xlarge"
        assert pricing.hourly_rate == Decimal("1.212")
        assert pricing.gpu_count == 1
        assert pricing.gpu_type == "A10G"

    def test_get_instance_rate_not_found(self, pricing_service: PricingModelService):
        """测试获取不存在的实例类型"""
        pricing = pricing_service.get_instance_rate("invalid.type")

        assert pricing is None

    def test_get_instance_rate_with_region(self, pricing_service: PricingModelService):
        """测试按区域获取实例定价"""
        # 默认区域
        pricing_us_east = pricing_service.get_instance_rate("p4d.24xlarge", region="us-east-1")
        assert pricing_us_east is not None
        assert pricing_us_east.region == "us-east-1"

        # 其他区域 (暂不支持, 返回 None)
        pricing_eu = pricing_service.get_instance_rate("p4d.24xlarge", region="eu-west-1")
        assert pricing_eu is None

    def test_get_storage_rate_fsx_lustre(self, pricing_service: PricingModelService):
        """测试获取 FSx for Lustre 定价"""
        pricing = pricing_service.get_storage_rate("fsx_lustre")

        assert pricing is not None
        assert pricing.storage_type == "fsx_lustre"
        assert pricing.storage_rate_per_gb_month == Decimal("0.145")
        assert pricing.throughput_rate_per_mb_s == Decimal("0.0")  # 包含在存储定价中
        assert pricing.region == "us-east-1"

    def test_get_storage_rate_s3_standard(self, pricing_service: PricingModelService):
        """测试获取 S3 Standard 定价"""
        pricing = pricing_service.get_storage_rate("s3_standard")

        assert pricing is not None
        assert pricing.storage_type == "s3_standard"
        assert pricing.storage_rate_per_gb_month == Decimal("0.023")
        assert pricing.region == "us-east-1"

    def test_get_storage_rate_not_found(self, pricing_service: PricingModelService):
        """测试获取不存在的存储类型"""
        pricing = pricing_service.get_storage_rate("invalid_storage")

        assert pricing is None

    def test_get_network_rate_cross_az(self, pricing_service: PricingModelService):
        """测试获取跨 AZ 网络传输定价"""
        pricing = pricing_service.get_network_rate("cross_az")

        assert pricing is not None
        assert pricing.transfer_type == "cross_az"
        assert pricing.rate_per_gb == Decimal("0.01")
        assert pricing.region == "us-east-1"

    def test_get_network_rate_same_vpc(self, pricing_service: PricingModelService):
        """测试获取同 VPC 网络传输定价"""
        pricing = pricing_service.get_network_rate("same_vpc")

        assert pricing is not None
        assert pricing.transfer_type == "same_vpc"
        assert pricing.rate_per_gb == Decimal("0.0")  # 同 VPC 免费
        assert pricing.region == "us-east-1"

    def test_get_network_rate_s3_egress(self, pricing_service: PricingModelService):
        """测试获取 S3 数据传输出站定价"""
        pricing = pricing_service.get_network_rate("s3_egress")

        assert pricing is not None
        assert pricing.transfer_type == "s3_egress"
        assert pricing.rate_per_gb == Decimal("0.09")
        assert pricing.region == "us-east-1"

    def test_get_network_rate_not_found(self, pricing_service: PricingModelService):
        """测试获取不存在的网络传输类型"""
        pricing = pricing_service.get_network_rate("invalid_transfer")

        assert pricing is None

    def test_pricing_version_management(self, pricing_service: PricingModelService):
        """测试定价数据版本管理"""
        assert pricing_service.pricing_version is not None
        assert len(pricing_service.pricing_version) > 0

        # 版本格式: YYYY-MM-DD
        version_parts = pricing_service.pricing_version.split("-")
        assert len(version_parts) == 3
        assert len(version_parts[0]) == 4  # 年份
        assert len(version_parts[1]) == 2  # 月份
        assert len(version_parts[2]) == 2  # 日期

    def test_last_updated_timestamp(self, pricing_service: PricingModelService):
        """测试最后更新时间戳"""
        assert isinstance(pricing_service.last_updated, datetime)
        assert pricing_service.last_updated <= datetime.now()

    def test_calculate_training_cost(self, pricing_service: PricingModelService):
        """测试计算训练成本 (集成测试)"""
        # 场景: p4d.24xlarge 实例训练 2 小时
        instance_pricing = pricing_service.get_instance_rate("p4d.24xlarge")
        assert instance_pricing is not None

        training_hours = 2
        expected_cost = instance_pricing.hourly_rate * Decimal(training_hours)

        assert expected_cost == Decimal("32.77") * Decimal("2")
        assert expected_cost == Decimal("65.54")

    def test_calculate_storage_cost(self, pricing_service: PricingModelService):
        """测试计算存储成本 (集成测试)"""
        # 场景: 10 TiB FSx for Lustre 存储 1 个月
        fsx_pricing = pricing_service.get_storage_rate("fsx_lustre")
        assert fsx_pricing is not None

        storage_gb = 10 * 1024  # 10 TiB = 10,240 GB
        expected_cost = fsx_pricing.storage_rate_per_gb_month * Decimal(storage_gb)

        assert expected_cost == Decimal("0.145") * Decimal("10240")
        assert expected_cost == Decimal("1484.80")

    def test_calculate_network_cost(self, pricing_service: PricingModelService):
        """测试计算网络传输成本 (集成测试)"""
        # 场景: 跨 AZ 传输 100 GB 数据
        network_pricing = pricing_service.get_network_rate("cross_az")
        assert network_pricing is not None

        transfer_gb = 100
        expected_cost = network_pricing.rate_per_gb * Decimal(transfer_gb)

        assert expected_cost == Decimal("0.01") * Decimal("100")
        assert expected_cost == Decimal("1.00")
