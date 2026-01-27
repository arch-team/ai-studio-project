"""成本计算引擎单元测试 (T069)."""

from decimal import Decimal

import pytest

from src.modules.billing.application.services import (
    AllocatedCost,
    ComputeCost,
    CostAllocationKey,
    CostBreakdown,
    CostCalculator,
    NetworkCost,
    StorageCost,
    TotalCost,
)


class TestComputeCost:
    """计算成本测试."""

    def test_calculate_single_node(self):
        """测试单节点计算成本."""
        cost = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=1,
            duration_hours=Decimal("2.5"),
        )

        assert cost.instance_type == "p4d.24xlarge"
        assert cost.node_count == 1
        assert cost.duration_hours == Decimal("2.5")
        assert cost.total_cost == Decimal("32.77") * 1 * Decimal("2.5")  # 81.925

    def test_calculate_multi_node(self):
        """测试多节点计算成本."""
        cost = ComputeCost.calculate(
            instance_type="p5.48xlarge",
            instance_hourly_rate=Decimal("98.32"),
            node_count=8,
            duration_hours=Decimal("10.0"),
        )

        assert cost.node_count == 8
        assert cost.total_cost == Decimal("98.32") * 8 * Decimal("10.0")  # 7865.6


class TestStorageCost:
    """存储成本测试."""

    def test_calculate_fsx_storage(self):
        """测试 FSx 存储成本."""
        cost = StorageCost.calculate(
            storage_type="FSx",
            storage_size_gb=Decimal("1000"),  # 1TB
            storage_rate_per_gb_hour=Decimal("0.00014"),  # $0.14/GB/month
            duration_hours=Decimal("24"),  # 1 day
        )

        assert cost.storage_type == "FSx"
        assert cost.storage_size_gb == Decimal("1000")
        assert cost.total_cost == Decimal("1000") * Decimal("0.00014") * Decimal("24")  # 3.36

    def test_calculate_s3_storage(self):
        """测试 S3 存储成本."""
        cost = StorageCost.calculate(
            storage_type="S3",
            storage_size_gb=Decimal("5000"),  # 5TB
            storage_rate_per_gb_hour=Decimal("0.000003"),  # $0.023/GB/month
            duration_hours=Decimal("720"),  # 30 days
        )

        assert cost.storage_type == "S3"
        assert cost.total_cost == Decimal("5000") * Decimal("0.000003") * Decimal("720")  # 10.8


class TestNetworkCost:
    """网络传输成本测试."""

    def test_calculate_outbound_transfer(self):
        """测试出站数据传输成本."""
        cost = NetworkCost.calculate(
            data_transfer_gb=Decimal("500"),
            transfer_rate_per_gb=Decimal("0.09"),  # $0.09/GB
            transfer_direction="out",
        )

        assert cost.data_transfer_gb == Decimal("500")
        assert cost.transfer_direction == "out"
        assert cost.total_cost == Decimal("500") * Decimal("0.09")  # 45.0

    def test_calculate_inter_region_transfer(self):
        """测试跨区域数据传输成本."""
        cost = NetworkCost.calculate(
            data_transfer_gb=Decimal("100"),
            transfer_rate_per_gb=Decimal("0.02"),  # $0.02/GB
            transfer_direction="inter-region",
        )

        assert cost.transfer_direction == "inter-region"
        assert cost.total_cost == Decimal("100") * Decimal("0.02")  # 2.0


class TestCostBreakdown:
    """成本明细测试."""

    def test_total_cost_calculation(self):
        """测试总成本计算."""
        compute = ComputeCost.calculate(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=4,
            duration_hours=Decimal("5.0"),
        )
        storage = StorageCost.calculate(
            storage_type="FSx",
            storage_size_gb=Decimal("2000"),
            storage_rate_per_gb_hour=Decimal("0.00014"),
            duration_hours=Decimal("5.0"),
        )
        network = NetworkCost.calculate(
            data_transfer_gb=Decimal("50"),
            transfer_rate_per_gb=Decimal("0.09"),
            transfer_direction="out",
        )

        breakdown = CostBreakdown(compute_cost=compute, storage_cost=storage, network_cost=network)

        expected_total = compute.total_cost + storage.total_cost + network.total_cost
        assert breakdown.total_cost == expected_total

    def test_to_dict(self):
        """测试转换为字典."""
        compute = ComputeCost.calculate("p4d.24xlarge", Decimal("32.77"), 2, Decimal("1.0"))
        storage = StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.00014"), Decimal("1.0"))
        network = NetworkCost.calculate(Decimal("10"), Decimal("0.09"), "out")

        breakdown = CostBreakdown(compute_cost=compute, storage_cost=storage, network_cost=network)
        result = breakdown.to_dict()

        assert "compute" in result
        assert "storage" in result
        assert "network" in result
        assert "total" in result
        assert result["compute"]["instance_type"] == "p4d.24xlarge"
        assert result["storage"]["storage_type"] == "FSx"
        assert result["network"]["direction"] == "out"


class TestCostCalculator:
    """成本计算引擎测试."""

    @pytest.fixture
    def calculator(self):
        """成本计算器 fixture."""
        return CostCalculator()

    def test_calculate_job_cost_basic(self, calculator):
        """测试基本任务成本计算."""
        breakdown = calculator.calculate_job_cost(
            instance_type="p4d.24xlarge",
            instance_hourly_rate=Decimal("32.77"),
            node_count=4,
            training_duration_hours=Decimal("8.0"),
            storage_size_gb=Decimal("1000"),
            storage_rate_per_gb_hour=Decimal("0.00014"),
            data_transfer_gb=Decimal("100"),
            transfer_rate_per_gb=Decimal("0.09"),
            storage_type="FSx",
            transfer_direction="out",
        )

        assert breakdown.compute_cost.total_cost == Decimal("32.77") * 4 * Decimal("8.0")  # 1048.64
        assert breakdown.storage_cost.total_cost == Decimal("1000") * Decimal("0.00014") * Decimal("8.0")  # 1.12
        assert breakdown.network_cost.total_cost == Decimal("100") * Decimal("0.09")  # 9.0
        assert breakdown.total_cost == Decimal("1048.64") + Decimal("1.12") + Decimal("9.0")  # 1058.76

    def test_aggregate_costs_multiple_jobs(self, calculator):
        """测试多任务成本聚合."""
        breakdown1 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p4d.24xlarge", Decimal("32.77"), 2, Decimal("5.0")),
            storage_cost=StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.00014"), Decimal("5.0")),
            network_cost=NetworkCost.calculate(Decimal("50"), Decimal("0.09"), "out"),
        )
        breakdown2 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p5.48xlarge", Decimal("98.32"), 4, Decimal("3.0")),
            storage_cost=StorageCost.calculate("S3", Decimal("2000"), Decimal("0.000003"), Decimal("3.0")),
            network_cost=NetworkCost.calculate(Decimal("30"), Decimal("0.09"), "out"),
        )

        total = calculator.aggregate_costs([breakdown1, breakdown2])

        assert total.job_count == 2
        assert total.total_compute == breakdown1.compute_cost.total_cost + breakdown2.compute_cost.total_cost
        assert total.total_storage == breakdown1.storage_cost.total_cost + breakdown2.storage_cost.total_cost
        assert total.total_network == breakdown1.network_cost.total_cost + breakdown2.network_cost.total_cost
        assert total.grand_total == total.total_compute + total.total_storage + total.total_network

    def test_allocate_by_user(self, calculator):
        """测试按用户分摊成本."""
        breakdown1 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p4d.24xlarge", Decimal("32.77"), 2, Decimal("5.0")),
            storage_cost=StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.00014"), Decimal("5.0")),
            network_cost=NetworkCost.calculate(Decimal("50"), Decimal("0.09"), "out"),
        )
        breakdown2 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p5.48xlarge", Decimal("98.32"), 1, Decimal("2.0")),
            storage_cost=StorageCost.calculate("S3", Decimal("500"), Decimal("0.000003"), Decimal("2.0")),
            network_cost=NetworkCost.calculate(Decimal("20"), Decimal("0.09"), "out"),
        )

        costs = {
            101: [(1, breakdown1)],  # user 101 has job 1
            102: [(2, breakdown2)],  # user 102 has job 2
        }

        allocated = calculator.allocate_by_user(costs)

        assert len(allocated) == 2
        assert allocated[0].allocation_key.dimension == "user"
        assert allocated[0].allocation_key.value in [101, 102]
        assert allocated[0].total_cost.job_count == 1

    def test_allocate_by_project(self, calculator):
        """测试按项目分摊成本."""
        breakdown1 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p4d.24xlarge", Decimal("32.77"), 2, Decimal("5.0")),
            storage_cost=StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.00014"), Decimal("5.0")),
            network_cost=NetworkCost.calculate(Decimal("50"), Decimal("0.09"), "out"),
        )
        breakdown2 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p5.48xlarge", Decimal("98.32"), 1, Decimal("2.0")),
            storage_cost=StorageCost.calculate("S3", Decimal("500"), Decimal("0.000003"), Decimal("2.0")),
            network_cost=NetworkCost.calculate(Decimal("20"), Decimal("0.09"), "out"),
        )

        costs = {
            "project-alpha": [(1, breakdown1), (2, breakdown2)],  # 2 jobs in same project
        }

        allocated = calculator.allocate_by_project(costs)

        assert len(allocated) == 1
        assert allocated[0].allocation_key.dimension == "project"
        assert allocated[0].allocation_key.value == "project-alpha"
        assert allocated[0].total_cost.job_count == 2
        assert len(allocated[0].jobs) == 2

    def test_allocate_by_time_range(self, calculator):
        """测试按时间范围分摊成本."""
        breakdown1 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p4d.24xlarge", Decimal("32.77"), 2, Decimal("5.0")),
            storage_cost=StorageCost.calculate("FSx", Decimal("1000"), Decimal("0.00014"), Decimal("5.0")),
            network_cost=NetworkCost.calculate(Decimal("50"), Decimal("0.09"), "out"),
        )
        breakdown2 = CostBreakdown(
            compute_cost=ComputeCost.calculate("p5.48xlarge", Decimal("98.32"), 1, Decimal("2.0")),
            storage_cost=StorageCost.calculate("S3", Decimal("500"), Decimal("0.000003"), Decimal("2.0")),
            network_cost=NetworkCost.calculate(Decimal("20"), Decimal("0.09"), "out"),
        )

        costs = {
            "2026-01-27": [(1, breakdown1)],
            "2026-01-28": [(2, breakdown2)],
        }

        allocated = calculator.allocate_by_time_range(costs)

        assert len(allocated) == 2
        assert allocated[0].allocation_key.dimension == "time_range"
        assert allocated[0].allocation_key.value in ["2026-01-27", "2026-01-28"]


class TestTotalCost:
    """总成本统计测试."""

    def test_to_dict(self):
        """测试转换为字典."""
        total = TotalCost(
            total_compute=Decimal("1000.50"),
            total_storage=Decimal("50.25"),
            total_network=Decimal("10.75"),
            grand_total=Decimal("1061.50"),
            job_count=5,
        )

        result = total.to_dict()

        assert result["compute"] == 1000.50
        assert result["storage"] == 50.25
        assert result["network"] == 10.75
        assert result["total"] == 1061.50
        assert result["job_count"] == 5


class TestAllocatedCost:
    """分摊成本测试."""

    def test_to_dict(self):
        """测试转换为字典."""
        total = TotalCost(
            total_compute=Decimal("500.0"),
            total_storage=Decimal("25.0"),
            total_network=Decimal("5.0"),
            grand_total=Decimal("530.0"),
            job_count=2,
        )
        allocated = AllocatedCost(
            allocation_key=CostAllocationKey(dimension="user", value=101),
            total_cost=total,
            jobs=[1, 2],
        )

        result = allocated.to_dict()

        assert result["allocation"]["dimension"] == "user"
        assert result["allocation"]["value"] == 101
        assert result["cost"]["total"] == 530.0
        assert result["job_ids"] == [1, 2]
