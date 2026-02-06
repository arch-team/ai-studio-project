"""成本计算准确率验证测试 (T069c).

验证成本计算逻辑的数学正确性、边界条件和精度处理。
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from src.modules.billing.application.services import (
    ComputeCost,
    CostBreakdown,
    CostCalculator,
    NetworkCost,
    PricingModelService,
    StorageCost,
)


class TestComputeCostAccuracy:
    """计算成本准确性测试."""

    @pytest.fixture
    def pricing_service(self) -> PricingModelService:
        """定价模型服务 fixture."""
        return PricingModelService()

    @pytest.mark.parametrize(
        "instance_type,node_count,hours,expected_cost",
        [
            # p4d.24xlarge: $32.77/hr
            ("p4d.24xlarge", 1, Decimal("1.0"), Decimal("32.77")),
            ("p4d.24xlarge", 4, Decimal("2.5"), Decimal("327.70")),  # 32.77 * 4 * 2.5
            ("p4d.24xlarge", 8, Decimal("10.0"), Decimal("2621.60")),  # 32.77 * 8 * 10
            # p5.48xlarge: $98.32/hr
            ("p5.48xlarge", 1, Decimal("1.0"), Decimal("98.32")),
            ("p5.48xlarge", 2, Decimal("1.0"), Decimal("196.64")),  # 98.32 * 2 * 1.0
            ("p5.48xlarge", 4, Decimal("5.0"), Decimal("1966.40")),  # 98.32 * 4 * 5.0
            # trn1.32xlarge: $21.50/hr
            ("trn1.32xlarge", 1, Decimal("1.0"), Decimal("21.50")),
            ("trn1.32xlarge", 8, Decimal("0.5"), Decimal("86.00")),  # 21.50 * 8 * 0.5
            ("trn1.32xlarge", 16, Decimal("24.0"), Decimal("8256.00")),  # 21.50 * 16 * 24
            # ml.g5.xlarge: $1.006/hr
            ("ml.g5.xlarge", 1, Decimal("1.0"), Decimal("1.006")),
            ("ml.g5.xlarge", 2, Decimal("10.0"), Decimal("20.12")),  # 1.006 * 2 * 10
            # ml.g5.2xlarge: $1.212/hr
            ("ml.g5.2xlarge", 1, Decimal("1.0"), Decimal("1.212")),
            ("ml.g5.2xlarge", 4, Decimal("8.0"), Decimal("38.784")),  # 1.212 * 4 * 8
        ],
    )
    def test_compute_cost_accuracy(
        self,
        pricing_service: PricingModelService,
        instance_type: str,
        node_count: int,
        hours: Decimal,
        expected_cost: Decimal,
    ):
        """测试计算成本公式: 单价 * 节点数 * 小时数."""
        pricing = pricing_service.get_instance_rate(instance_type)
        assert pricing is not None, f"未找到实例类型 {instance_type} 的定价"

        cost = ComputeCost.calculate(
            instance_type=instance_type,
            instance_hourly_rate=pricing.hourly_rate,
            node_count=node_count,
            duration_hours=hours,
        )

        assert cost.total_cost == expected_cost, (
            f"计算成本不正确: "
            f"{pricing.hourly_rate} * {node_count} * {hours} = {cost.total_cost}, "
            f"期望值: {expected_cost}"
        )

    def test_compute_cost_formula_validation(self, pricing_service: PricingModelService):
        """验证计算成本公式: total = hourly_rate * node_count * duration_hours."""
        # 获取 p4d.24xlarge 定价
        pricing = pricing_service.get_instance_rate("p4d.24xlarge")
        assert pricing is not None

        hourly_rate = pricing.hourly_rate
        node_count = 4
        duration_hours = Decimal("2.5")

        cost = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=hourly_rate,
            node_count=node_count,
            duration_hours=duration_hours,
        )

        # 手动计算期望值
        expected = hourly_rate * node_count * duration_hours

        assert cost.total_cost == expected
        assert cost.instance_hourly_rate == hourly_rate
        assert cost.node_count == node_count
        assert cost.duration_hours == duration_hours


class TestStorageCostAccuracy:
    """存储成本准确性测试."""

    @pytest.fixture
    def pricing_service(self) -> PricingModelService:
        """定价模型服务 fixture."""
        return PricingModelService()

    def _monthly_to_hourly_rate(self, monthly_rate: Decimal) -> Decimal:
        """将月费率转换为小时费率 (每月 730 小时)."""
        return monthly_rate / Decimal("730")

    @pytest.mark.parametrize(
        "storage_type,size_gb,hours,expected_cost_formula",
        [
            # FSx Lustre: $0.145/GB/month → $0.0001986/GB/hour
            # 100 GB * 24 小时
            ("fsx_lustre", Decimal("100"), Decimal("24"), lambda rate: Decimal("100") * rate * Decimal("24")),
            # 1000 GB (1TB) * 720 小时 (30天)
            ("fsx_lustre", Decimal("1000"), Decimal("720"), lambda rate: Decimal("1000") * rate * Decimal("720")),
            # S3 Standard: $0.023/GB/month → $0.0000315/GB/hour
            # 500 GB * 168 小时 (7天)
            ("s3_standard", Decimal("500"), Decimal("168"), lambda rate: Decimal("500") * rate * Decimal("168")),
            # 5000 GB (5TB) * 720 小时 (30天)
            ("s3_standard", Decimal("5000"), Decimal("720"), lambda rate: Decimal("5000") * rate * Decimal("720")),
        ],
    )
    def test_storage_cost_accuracy(
        self,
        pricing_service: PricingModelService,
        storage_type: str,
        size_gb: Decimal,
        hours: Decimal,
        expected_cost_formula,
    ):
        """测试存储成本公式: 存储大小 * 每 GB 小时价格 * 小时数."""
        pricing = pricing_service.get_storage_rate(storage_type)
        assert pricing is not None, f"未找到存储类型 {storage_type} 的定价"

        # 将月费率转换为小时费率
        hourly_rate = self._monthly_to_hourly_rate(pricing.storage_rate_per_gb_month)

        cost = StorageCost.calculate(
            storage_type=storage_type,
            storage_size_gb=size_gb,
            storage_rate_per_gb_hour=hourly_rate,
            duration_hours=hours,
        )

        expected_cost = expected_cost_formula(hourly_rate)

        # 使用精度容差比较 (0.000001 USD)
        tolerance = Decimal("0.000001")
        assert abs(cost.total_cost - expected_cost) < tolerance, (
            f"存储成本计算不正确: "
            f"{size_gb} GB * {hourly_rate}/GB/hour * {hours} hours = {cost.total_cost}, "
            f"期望值: {expected_cost}"
        )

    def test_fsx_lustre_monthly_cost(self, pricing_service: PricingModelService):
        """测试 FSx Lustre 月度成本计算."""
        pricing = pricing_service.get_storage_rate("fsx_lustre")
        assert pricing is not None

        # 1 TB 存储一个月的成本
        monthly_rate = pricing.storage_rate_per_gb_month
        storage_gb = Decimal("1000")  # 1 TB
        hours = Decimal("730")  # 一个月

        hourly_rate = monthly_rate / Decimal("730")

        cost = StorageCost.calculate(
            storage_type="fsx_lustre",
            storage_size_gb=storage_gb,
            storage_rate_per_gb_hour=hourly_rate,
            duration_hours=hours,
        )

        # 期望值: $0.145/GB/month * 1000 GB = $145/month
        expected_monthly_cost = monthly_rate * storage_gb

        # 允许舍入误差
        tolerance = Decimal("0.01")
        assert abs(cost.total_cost - expected_monthly_cost) < tolerance

    def test_s3_standard_monthly_cost(self, pricing_service: PricingModelService):
        """测试 S3 Standard 月度成本计算."""
        pricing = pricing_service.get_storage_rate("s3_standard")
        assert pricing is not None

        # 5 TB 存储一个月的成本
        monthly_rate = pricing.storage_rate_per_gb_month
        storage_gb = Decimal("5000")  # 5 TB
        hours = Decimal("730")  # 一个月

        hourly_rate = monthly_rate / Decimal("730")

        cost = StorageCost.calculate(
            storage_type="s3_standard",
            storage_size_gb=storage_gb,
            storage_rate_per_gb_hour=hourly_rate,
            duration_hours=hours,
        )

        # 期望值: $0.023/GB/month * 5000 GB = $115/month
        expected_monthly_cost = monthly_rate * storage_gb

        tolerance = Decimal("0.01")
        assert abs(cost.total_cost - expected_monthly_cost) < tolerance


class TestNetworkCostAccuracy:
    """网络成本准确性测试."""

    @pytest.fixture
    def pricing_service(self) -> PricingModelService:
        """定价模型服务 fixture."""
        return PricingModelService()

    @pytest.mark.parametrize(
        "transfer_type,transfer_gb,expected_rate,expected_cost",
        [
            # 跨 AZ 传输: $0.01/GB
            ("cross_az", Decimal("100"), Decimal("0.01"), Decimal("1.00")),
            ("cross_az", Decimal("500"), Decimal("0.01"), Decimal("5.00")),
            ("cross_az", Decimal("1000"), Decimal("0.01"), Decimal("10.00")),
            # 同 VPC 传输: 免费
            ("same_vpc", Decimal("100"), Decimal("0.0"), Decimal("0.00")),
            ("same_vpc", Decimal("1000"), Decimal("0.0"), Decimal("0.00")),
            ("same_vpc", Decimal("10000"), Decimal("0.0"), Decimal("0.00")),
            # S3 出站传输: $0.09/GB
            ("s3_egress", Decimal("100"), Decimal("0.09"), Decimal("9.00")),
            ("s3_egress", Decimal("500"), Decimal("0.09"), Decimal("45.00")),
            ("s3_egress", Decimal("1000"), Decimal("0.09"), Decimal("90.00")),
        ],
    )
    def test_network_cost_accuracy(
        self,
        pricing_service: PricingModelService,
        transfer_type: str,
        transfer_gb: Decimal,
        expected_rate: Decimal,
        expected_cost: Decimal,
    ):
        """测试网络传输成本公式: 传输量 * 每 GB 价格."""
        pricing = pricing_service.get_network_rate(transfer_type)
        assert pricing is not None, f"未找到传输类型 {transfer_type} 的定价"

        # 验证定价数据正确性
        assert (
            pricing.rate_per_gb == expected_rate
        ), f"定价数据不正确: {transfer_type} 期望费率 {expected_rate}, 实际 {pricing.rate_per_gb}"

        cost = NetworkCost.calculate(
            data_transfer_gb=transfer_gb,
            transfer_rate_per_gb=pricing.rate_per_gb,
            transfer_direction=transfer_type,
        )

        assert cost.total_cost == expected_cost, (
            f"网络成本计算不正确: "
            f"{transfer_gb} GB * {pricing.rate_per_gb}/GB = {cost.total_cost}, "
            f"期望值: {expected_cost}"
        )

    def test_inbound_transfer_free(self, pricing_service: PricingModelService):
        """测试入站传输免费 (same_vpc)."""
        pricing = pricing_service.get_network_rate("same_vpc")
        assert pricing is not None

        # 任意大小的入站传输都应该免费
        for transfer_gb in [100, 1000, 10000]:
            cost = NetworkCost.calculate(
                data_transfer_gb=Decimal(str(transfer_gb)),
                transfer_rate_per_gb=pricing.rate_per_gb,
                transfer_direction="in",
            )
            assert cost.total_cost == Decimal("0.00"), f"入站 {transfer_gb} GB 应该免费"


class TestTotalCostCalculation:
    """总成本汇总测试."""

    @pytest.fixture
    def calculator(self) -> CostCalculator:
        """成本计算器 fixture."""
        return CostCalculator()

    @pytest.fixture
    def pricing_service(self) -> PricingModelService:
        """定价模型服务 fixture."""
        return PricingModelService()

    def test_total_equals_sum_of_components(self, calculator: CostCalculator):
        """验证 total = compute + storage + network."""
        breakdown = calculator.calculate_job_cost(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=4,
            training_duration_hours=Decimal("8.0"),
            storage_size_gb=Decimal("1000"),
            storage_rate_per_gb_hour=Decimal("0.0001986"),  # FSx 小时费率
            data_transfer_gb=Decimal("100"),
            transfer_rate_per_gb=Decimal("0.09"),
            storage_type="FSx",
            transfer_direction="out",
        )

        computed_total = (
            breakdown.compute_cost.total_cost + breakdown.storage_cost.total_cost + breakdown.network_cost.total_cost
        )

        assert breakdown.total_cost == computed_total, (
            f"总成本不等于组件之和: "
            f"compute({breakdown.compute_cost.total_cost}) + "
            f"storage({breakdown.storage_cost.total_cost}) + "
            f"network({breakdown.network_cost.total_cost}) = {computed_total}, "
            f"但 total = {breakdown.total_cost}"
        )

    def test_cost_breakdown_percentages_sum_to_100(self, calculator: CostCalculator):
        """验证成本百分比总和为 100%."""
        breakdown = calculator.calculate_job_cost(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=4,
            training_duration_hours=Decimal("8.0"),
            storage_size_gb=Decimal("1000"),
            storage_rate_per_gb_hour=Decimal("0.0001986"),
            data_transfer_gb=Decimal("100"),
            transfer_rate_per_gb=Decimal("0.09"),
        )

        total = breakdown.total_cost

        # 避免除以零
        if total > 0:
            compute_pct = (breakdown.compute_cost.total_cost / total) * 100
            storage_pct = (breakdown.storage_cost.total_cost / total) * 100
            network_pct = (breakdown.network_cost.total_cost / total) * 100

            total_pct = compute_pct + storage_pct + network_pct

            # 允许浮点误差
            tolerance = Decimal("0.01")
            assert abs(total_pct - Decimal("100")) < tolerance, f"百分比总和应为 100%, 实际: {total_pct}"

    def test_aggregated_costs_match_individual_sums(self, calculator: CostCalculator):
        """验证聚合成本与单独求和结果一致."""
        breakdown1 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p4d.24xlarge", Decimal("32.77"), 2, Decimal("5.0")),
            storage_cost=StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.0001986"), Decimal("5.0")),
            network_cost=NetworkCost.calculate(Decimal("50"), Decimal("0.09"), "out"),
        )
        breakdown2 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p5.48xlarge", Decimal("98.32"), 4, Decimal("3.0")),
            storage_cost=StorageCost.calculate("S3", Decimal("2000"), Decimal("0.0000315"), Decimal("3.0")),
            network_cost=NetworkCost.calculate(Decimal("100"), Decimal("0.09"), "out"),
        )

        aggregated = calculator.aggregate_costs([breakdown1, breakdown2])

        # 手动求和
        manual_compute = breakdown1.compute_cost.total_cost + breakdown2.compute_cost.total_cost
        manual_storage = breakdown1.storage_cost.total_cost + breakdown2.storage_cost.total_cost
        manual_network = breakdown1.network_cost.total_cost + breakdown2.network_cost.total_cost

        assert aggregated.total_compute == manual_compute
        assert aggregated.total_storage == manual_storage
        assert aggregated.total_network == manual_network
        assert aggregated.grand_total == manual_compute + manual_storage + manual_network


class TestBoundaryConditions:
    """边界条件测试."""

    @pytest.fixture
    def calculator(self) -> CostCalculator:
        """成本计算器 fixture."""
        return CostCalculator()

    def test_zero_duration_cost(self, calculator: CostCalculator):
        """测试 0 小时返回 0 成本."""
        breakdown = calculator.calculate_job_cost(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=4,
            training_duration_hours=Decimal("0"),
            storage_size_gb=Decimal("1000"),
            storage_rate_per_gb_hour=Decimal("0.0001986"),
            data_transfer_gb=Decimal("0"),
            transfer_rate_per_gb=Decimal("0.09"),
        )

        # 0 时长应该导致 0 计算成本和 0 存储成本
        assert breakdown.compute_cost.total_cost == Decimal("0")
        assert breakdown.storage_cost.total_cost == Decimal("0")
        # 网络传输量为 0，所以也应该为 0
        assert breakdown.network_cost.total_cost == Decimal("0")
        assert breakdown.total_cost == Decimal("0")

    def test_zero_node_count_cost(self):
        """测试 0 节点返回 0 成本."""
        cost = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=0,
            duration_hours=Decimal("10.0"),
        )

        assert cost.total_cost == Decimal("0")

    def test_zero_storage_size_cost(self):
        """测试 0 存储返回 0 成本."""
        cost = StorageCost.calculate(
            storage_type="FSx",
            storage_size_gb=Decimal("0"),
            storage_rate_per_gb_hour=Decimal("0.0001986"),
            duration_hours=Decimal("24.0"),
        )

        assert cost.total_cost == Decimal("0")

    def test_zero_transfer_cost(self):
        """测试 0 传输量返回 0 成本."""
        cost = NetworkCost.calculate(
            data_transfer_gb=Decimal("0"),
            transfer_rate_per_gb=Decimal("0.09"),
            transfer_direction="out",
        )

        assert cost.total_cost == Decimal("0")

    def test_very_small_duration_precision(self):
        """测试非常小的时长精度 (0.001 小时 = 3.6 秒)."""
        cost = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=1,
            duration_hours=Decimal("0.001"),
        )

        expected = Decimal("32.77") * 1 * Decimal("0.001")  # 0.03277
        assert cost.total_cost == expected

    def test_very_large_scale_cost(self, calculator: CostCalculator):
        """测试大规模计算 (100 节点 * 720 小时)."""
        # 大规模 GPU 集群训练场景
        breakdown = calculator.calculate_job_cost(
            instance_type="p5.48xlarge",
            instance_hourly_rate=Decimal("98.32"),
            node_count=100,
            training_duration_hours=Decimal("720"),  # 30 天
            storage_size_gb=Decimal("100000"),  # 100 TB
            storage_rate_per_gb_hour=Decimal("0.0001986"),  # FSx
            data_transfer_gb=Decimal("10000"),  # 10 TB 传输
            transfer_rate_per_gb=Decimal("0.09"),
        )

        # 验证计算成本: 98.32 * 100 * 720 = 7,079,040
        expected_compute = Decimal("98.32") * 100 * Decimal("720")
        assert breakdown.compute_cost.total_cost == expected_compute

        # 验证存储成本: 100000 * 0.0001986 * 720 = 14,299.2
        expected_storage = Decimal("100000") * Decimal("0.0001986") * Decimal("720")
        assert breakdown.storage_cost.total_cost == expected_storage

        # 验证网络成本: 10000 * 0.09 = 900
        expected_network = Decimal("10000") * Decimal("0.09")
        assert breakdown.network_cost.total_cost == expected_network

        # 验证总成本正确相加
        assert breakdown.total_cost == expected_compute + expected_storage + expected_network

    def test_fractional_hour_precision(self):
        """测试分数小时精度."""
        # 1 小时 15 分钟 = 1.25 小时
        cost1 = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=1,
            duration_hours=Decimal("1.25"),
        )
        assert cost1.total_cost == Decimal("32.77") * Decimal("1.25")

        # 45 分钟 = 0.75 小时
        cost2 = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=1,
            duration_hours=Decimal("0.75"),
        )
        assert cost2.total_cost == Decimal("32.77") * Decimal("0.75")

    def test_single_second_duration(self):
        """测试单秒时长 (1/3600 小时)."""
        one_second_hours = Decimal("1") / Decimal("3600")

        cost = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=1,
            duration_hours=one_second_hours,
        )

        expected = Decimal("32.77") * one_second_hours
        assert cost.total_cost == expected


class TestDecimalPrecision:
    """精度测试 - 确保使用 Decimal 而非 float."""

    def test_uses_decimal_not_float(self):
        """确保成本值使用 Decimal 类型."""
        cost = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=4,
            duration_hours=Decimal("2.5"),
        )

        assert isinstance(cost.total_cost, Decimal)
        assert isinstance(cost.instance_hourly_rate, Decimal)
        assert isinstance(cost.duration_hours, Decimal)

    def test_no_floating_point_errors(self):
        """测试无浮点精度问题."""
        # 经典浮点精度问题: 0.1 + 0.2 != 0.3 in float
        # Decimal 应该精确处理

        # 使用会导致浮点误差的值
        cost = ComputeCost.calculate(
            instance_type="test",
            instance_hourly_rate=Decimal("0.1"),
            node_count=1,
            duration_hours=Decimal("0.3"),
        )

        # Decimal 精确计算
        expected = Decimal("0.1") * Decimal("0.3")  # 0.03 exactly
        assert cost.total_cost == expected

        # 验证不会出现浮点误差 (如 0.030000000000000002)
        assert str(cost.total_cost) == "0.03"

    def test_decimal_multiplication_precision(self):
        """测试 Decimal 乘法精度."""
        rate = Decimal("32.7712345")
        nodes = 8
        hours = Decimal("10.123456")

        cost = ComputeCost.calculate(
            instance_type="test",
            instance_hourly_rate=rate,
            node_count=nodes,
            duration_hours=hours,
        )

        # 精确计算
        expected = rate * nodes * hours
        assert cost.total_cost == expected


class TestCurrencyRounding:
    """货币四舍五入规则测试."""

    def test_rounding_to_cents(self):
        """测试四舍五入到分 (2 位小数)."""
        # 原始成本可能有很多小数位
        cost = ComputeCost.calculate(
            instance_type="test",
            instance_hourly_rate=Decimal("32.77"),
            node_count=3,
            duration_hours=Decimal("1.333"),
        )

        # 原始值: 32.77 * 3 * 1.333 = 131.049
        raw_cost = cost.total_cost

        # 四舍五入到 2 位小数
        rounded_cost = raw_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 验证四舍五入正确
        assert rounded_cost == Decimal("131.05")

    def test_rounding_half_up(self):
        """测试半入法 (0.5 向上舍入)."""
        # 构造一个结果恰好是 X.XX5 的情况
        cost = ComputeCost.calculate(
            instance_type="test",
            instance_hourly_rate=Decimal("10.00"),
            node_count=1,
            duration_hours=Decimal("0.0025"),  # 结果: 0.025
        )

        rounded = cost.total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert rounded == Decimal("0.03")  # 0.025 向上舍入为 0.03

    def test_display_format_consistency(self):
        """测试显示格式一致性."""
        breakdown = CostBreakdown(
            compute_cost=ComputeCost.calculate("test", Decimal("32.77"), 4, Decimal("2.5")),
            storage_cost=StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.0001986"), Decimal("2.5")),
            network_cost=NetworkCost.calculate(Decimal("50"), Decimal("0.09"), "out"),
        )

        result = breakdown.to_dict()

        # 验证转换为 float 后可以正常显示
        assert isinstance(result["total"], float)
        assert isinstance(result["compute"]["total"], float)
        assert isinstance(result["storage"]["total"], float)
        assert isinstance(result["network"]["total"], float)


class TestPricingModelIntegration:
    """定价模型集成测试."""

    @pytest.fixture
    def pricing_service(self) -> PricingModelService:
        """定价模型服务 fixture."""
        return PricingModelService()

    @pytest.fixture
    def calculator(self) -> CostCalculator:
        """成本计算器 fixture."""
        return CostCalculator()

    def test_end_to_end_cost_calculation(self, pricing_service: PricingModelService, calculator: CostCalculator):
        """端到端成本计算测试 - 使用真实定价数据."""
        # 获取定价数据
        instance_pricing = pricing_service.get_instance_rate("p4d.24xlarge")
        storage_pricing = pricing_service.get_storage_rate("fsx_lustre")
        network_pricing = pricing_service.get_network_rate("s3_egress")

        assert instance_pricing is not None
        assert storage_pricing is not None
        assert network_pricing is not None

        # 计算存储小时费率
        storage_hourly_rate = storage_pricing.storage_rate_per_gb_month / Decimal("730")

        # 计算任务成本
        breakdown = calculator.calculate_job_cost(
            instance_type=instance_pricing.instance_type,
            instance_hourly_rate=instance_pricing.hourly_rate,
            node_count=4,
            training_duration_hours=Decimal("8.0"),
            storage_size_gb=Decimal("1000"),
            storage_rate_per_gb_hour=storage_hourly_rate,
            data_transfer_gb=Decimal("100"),
            transfer_rate_per_gb=network_pricing.rate_per_gb,
            storage_type="fsx_lustre",
            transfer_direction="out",
        )

        # 验证各组件成本
        expected_compute = instance_pricing.hourly_rate * 4 * Decimal("8.0")
        expected_storage = Decimal("1000") * storage_hourly_rate * Decimal("8.0")
        expected_network = Decimal("100") * network_pricing.rate_per_gb

        assert breakdown.compute_cost.total_cost == expected_compute
        # 存储成本允许小误差
        tolerance = Decimal("0.0001")
        assert abs(breakdown.storage_cost.total_cost - expected_storage) < tolerance
        assert breakdown.network_cost.total_cost == expected_network

    def test_pricing_version_consistency(self, pricing_service: PricingModelService):
        """测试定价版本一致性."""
        # 确保定价数据有版本标识
        assert pricing_service.pricing_version is not None
        assert len(pricing_service.pricing_version) == 10  # YYYY-MM-DD 格式

    def test_all_instance_types_have_pricing(self, pricing_service: PricingModelService):
        """测试所有支持的实例类型都有定价."""
        expected_types = ["p4d.24xlarge", "p5.48xlarge", "trn1.32xlarge", "ml.g5.xlarge", "ml.g5.2xlarge"]

        for instance_type in expected_types:
            pricing = pricing_service.get_instance_rate(instance_type)
            assert pricing is not None, f"缺少实例类型 {instance_type} 的定价数据"
            assert pricing.hourly_rate > 0, f"实例类型 {instance_type} 的定价应大于 0"

    def test_unknown_instance_type_returns_none(self, pricing_service: PricingModelService):
        """测试未知实例类型返回 None."""
        pricing = pricing_service.get_instance_rate("unknown.type")
        assert pricing is None


class TestCostConsistency:
    """成本一致性测试."""

    @pytest.fixture
    def calculator(self) -> CostCalculator:
        """成本计算器 fixture."""
        return CostCalculator()

    def test_same_input_same_output(self, calculator: CostCalculator):
        """测试相同输入产生相同输出."""
        params = {
            "instance_type": "p4d.24xlarge",
            "instance_hourly_rate": Decimal("32.77"),
            "node_count": 4,
            "training_duration_hours": Decimal("8.0"),
            "storage_size_gb": Decimal("1000"),
            "storage_rate_per_gb_hour": Decimal("0.0001986"),
            "data_transfer_gb": Decimal("100"),
            "transfer_rate_per_gb": Decimal("0.09"),
        }

        result1 = calculator.calculate_job_cost(**params)
        result2 = calculator.calculate_job_cost(**params)

        assert result1.total_cost == result2.total_cost
        assert result1.compute_cost.total_cost == result2.compute_cost.total_cost
        assert result1.storage_cost.total_cost == result2.storage_cost.total_cost
        assert result1.network_cost.total_cost == result2.network_cost.total_cost

    def test_commutative_aggregation(self, calculator: CostCalculator):
        """测试聚合的交换律 - 顺序不影响结果."""
        breakdown1 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p4d.24xlarge", Decimal("32.77"), 2, Decimal("5.0")),
            storage_cost=StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.0001986"), Decimal("5.0")),
            network_cost=NetworkCost.calculate(Decimal("50"), Decimal("0.09"), "out"),
        )
        breakdown2 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p5.48xlarge", Decimal("98.32"), 4, Decimal("3.0")),
            storage_cost=StorageCost.calculate("S3", Decimal("2000"), Decimal("0.0000315"), Decimal("3.0")),
            network_cost=NetworkCost.calculate(Decimal("100"), Decimal("0.09"), "out"),
        )

        # 不同顺序聚合
        result1 = calculator.aggregate_costs([breakdown1, breakdown2])
        result2 = calculator.aggregate_costs([breakdown2, breakdown1])

        assert result1.grand_total == result2.grand_total
        assert result1.total_compute == result2.total_compute
        assert result1.total_storage == result2.total_storage
        assert result1.total_network == result2.total_network
