"""成本准确率验证测试 - 对比计算成本 vs Cost Explorer 实际账单 (T069c).

验证内容:
1. 对比平台计算成本 vs AWS Cost Explorer 实际账单
2. 误差率计算 (目标 <2%)
3. 回归测试 (使用历史训练任务数据模式)
4. 准确率监控告警 (误差 >2% 触发)
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.billing.application.interfaces import ICostExplorerClient, IResourceUsageQuery
from src.modules.billing.application.interfaces.resource_usage_query import TrainingJobStats
from src.modules.billing.application.services import (
    CostAccuracyReport,
    CostAccuracyValidator,
    CostComparisonItem,
)

# === Fixtures ===


def _make_cost_explorer_response(
    compute: str = "1000.00",
    storage: str = "200.00",
    network: str = "50.00",
) -> dict:
    """构建 Cost Explorer API 模拟响应."""
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-01-01", "End": "2026-02-01"},
                "Groups": [
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                        "Metrics": {"UnblendedCost": {"Amount": compute, "Unit": "USD"}},
                    },
                    {
                        "Keys": ["Amazon Simple Storage Service"],
                        "Metrics": {"UnblendedCost": {"Amount": storage, "Unit": "USD"}},
                    },
                    {
                        "Keys": ["AWS Data Transfer"],
                        "Metrics": {"UnblendedCost": {"Amount": network, "Unit": "USD"}},
                    },
                ],
            }
        ]
    }


def _make_training_stats(total_cost: Decimal) -> list[TrainingJobStats]:
    """构建平台训练任务统计模拟数据."""
    return [
        TrainingJobStats(
            period="2026-01",
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 1, 31),
            cpu_hours=Decimal("500"),
            gpu_hours=Decimal("200"),
            estimated_cost_usd=total_cost,
            job_count=15,
        ),
    ]


class TestCostAccuracyValidatorErrorRate:
    """误差率计算测试."""

    def test_zero_error_rate_when_costs_match(self):
        """计算成本与实际成本完全一致时误差率为 0."""
        error_rate = CostAccuracyValidator.calculate_error_rate(Decimal("1000.00"), Decimal("1000.00"))
        assert error_rate == Decimal("0")

    def test_error_rate_within_threshold(self):
        """误差率在 2% 以内."""
        # 计算 1010, 实际 1000 → 误差 1%
        error_rate = CostAccuracyValidator.calculate_error_rate(Decimal("1010.00"), Decimal("1000.00"))
        assert error_rate == Decimal("0.010000")
        assert error_rate < Decimal("0.02")

    def test_error_rate_exceeds_threshold(self):
        """误差率超过 2% 阈值."""
        # 计算 1050, 实际 1000 → 误差 5%
        error_rate = CostAccuracyValidator.calculate_error_rate(Decimal("1050.00"), Decimal("1000.00"))
        assert error_rate == Decimal("0.050000")
        assert error_rate > Decimal("0.02")

    def test_error_rate_underestimate(self):
        """平台低估成本时误差率为正值."""
        # 计算 950, 实际 1000 → 误差 5%
        error_rate = CostAccuracyValidator.calculate_error_rate(Decimal("950.00"), Decimal("1000.00"))
        assert error_rate == Decimal("0.050000")

    def test_zero_actual_cost_zero_calculated(self):
        """实际和计算成本均为 0 时误差率为 0."""
        error_rate = CostAccuracyValidator.calculate_error_rate(Decimal("0"), Decimal("0"))
        assert error_rate == Decimal("0")

    def test_zero_actual_cost_nonzero_calculated(self):
        """实际成本为 0 但计算成本不为 0 时误差率为 100%."""
        error_rate = CostAccuracyValidator.calculate_error_rate(Decimal("100.00"), Decimal("0"))
        assert error_rate == Decimal("1")

    @pytest.mark.parametrize(
        "calculated,actual,expected_rate",
        [
            (Decimal("1000.00"), Decimal("1000.00"), Decimal("0")),
            (Decimal("1005.00"), Decimal("1000.00"), Decimal("0.005000")),
            (Decimal("1010.00"), Decimal("1000.00"), Decimal("0.010000")),
            (Decimal("1020.00"), Decimal("1000.00"), Decimal("0.020000")),
            (Decimal("1050.00"), Decimal("1000.00"), Decimal("0.050000")),
            (Decimal("980.00"), Decimal("1000.00"), Decimal("0.020000")),
            (Decimal("500.00"), Decimal("1000.00"), Decimal("0.500000")),
        ],
    )
    def test_error_rate_parametrized(self, calculated, actual, expected_rate):
        """参数化误差率计算测试."""
        error_rate = CostAccuracyValidator.calculate_error_rate(calculated, actual)
        assert error_rate == expected_rate


class TestCostComparisonItem:
    """成本对比项测试."""

    def test_within_threshold(self):
        """误差率在阈值内."""
        item = CostComparisonItem(
            category="total",
            calculated_cost=Decimal("1010.00"),
            actual_cost=Decimal("1000.00"),
            difference=Decimal("10.00"),
            error_rate=Decimal("0.01"),
        )
        assert item.is_within_threshold is True

    def test_exceeds_threshold(self):
        """误差率超过阈值."""
        item = CostComparisonItem(
            category="total",
            calculated_cost=Decimal("1050.00"),
            actual_cost=Decimal("1000.00"),
            difference=Decimal("50.00"),
            error_rate=Decimal("0.05"),
        )
        assert item.is_within_threshold is False

    def test_exactly_at_threshold(self):
        """误差率恰好等于阈值 (2%) 视为合格."""
        item = CostComparisonItem(
            category="total",
            calculated_cost=Decimal("1020.00"),
            actual_cost=Decimal("1000.00"),
            difference=Decimal("20.00"),
            error_rate=Decimal("0.02"),
        )
        assert item.is_within_threshold is True


class TestCostAccuracyValidatorValidation:
    """成本准确率验证集成逻辑测试."""

    @pytest.fixture
    def mock_cost_explorer(self) -> AsyncMock:
        """Mock Cost Explorer 客户端."""
        return AsyncMock(spec=ICostExplorerClient)

    @pytest.fixture
    def mock_usage_query(self) -> AsyncMock:
        """Mock 资源使用查询."""
        mock = AsyncMock(spec=IResourceUsageQuery)
        mock.build_training_conditions.return_value = []
        return mock

    @pytest.fixture
    def validator(self, mock_cost_explorer, mock_usage_query) -> CostAccuracyValidator:
        """成本准确率验证器."""
        return CostAccuracyValidator(
            cost_explorer=mock_cost_explorer,
            usage_query=mock_usage_query,
        )

    @pytest.mark.asyncio
    async def test_accurate_costs_no_alert(self, validator, mock_cost_explorer, mock_usage_query):
        """成本匹配时不触发告警."""
        # Cost Explorer 返回: compute=700, storage=200, network=100 → total=1000
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        # 平台计算总成本 1000 → 拆分: compute=700, storage=200, network=100
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1000.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert isinstance(report, CostAccuracyReport)
        assert report.is_accurate is True
        assert report.alert_triggered is False
        assert report.overall_error_rate == Decimal("0")
        assert len(report.items) == 4  # compute, storage, network, total

    @pytest.mark.asyncio
    async def test_small_deviation_within_threshold(self, validator, mock_cost_explorer, mock_usage_query):
        """小偏差 (<2%) 在阈值内，不触发告警."""
        # 实际 total=1000, 计算 total=1015 → 误差 1.5%
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1015.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.is_accurate is True
        assert report.alert_triggered is False
        assert report.overall_error_rate < Decimal("0.02")

    @pytest.mark.asyncio
    async def test_large_deviation_triggers_alert(self, validator, mock_cost_explorer, mock_usage_query):
        """大偏差 (>2%) 触发告警."""
        # 实际 total=1000, 计算 total=1100 → 误差 10%
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1100.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.is_accurate is False
        assert report.alert_triggered is True
        assert report.overall_error_rate > Decimal("0.02")
        assert "成本准确率告警" in report.alert_message
        assert "误差率" in report.alert_message

    @pytest.mark.asyncio
    async def test_underestimate_triggers_alert(self, validator, mock_cost_explorer, mock_usage_query):
        """低估成本 (>2%) 也触发告警."""
        # 实际 total=1000, 计算 total=900 → 误差 10%
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("900.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.is_accurate is False
        assert report.alert_triggered is True

    @pytest.mark.asyncio
    async def test_report_contains_all_categories(self, validator, mock_cost_explorer, mock_usage_query):
        """报告包含 compute/storage/network/total 四个对比项."""
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response()
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1250.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        categories = [item.category for item in report.items]
        assert categories == ["compute", "storage", "network", "total"]

    @pytest.mark.asyncio
    async def test_report_total_properties(self, validator, mock_cost_explorer, mock_usage_query):
        """报告的总成本属性正确."""
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1000.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.total_calculated == Decimal("1000.00")
        assert report.total_actual == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_empty_cost_explorer_response(self, validator, mock_cost_explorer, mock_usage_query):
        """Cost Explorer 返回空数据时的处理."""
        mock_cost_explorer.get_cost_and_usage.return_value = {"ResultsByTime": []}
        mock_usage_query.get_training_job_stats_by_period.return_value = []

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        # 双方均为 0，误差率为 0
        assert report.overall_error_rate == Decimal("0")
        assert report.is_accurate is True

    @pytest.mark.asyncio
    async def test_custom_error_threshold(self, mock_cost_explorer, mock_usage_query):
        """自定义误差率阈值."""
        validator = CostAccuracyValidator(
            cost_explorer=mock_cost_explorer,
            usage_query=mock_usage_query,
            error_threshold=Decimal("0.05"),  # 5% 阈值
        )

        # 误差 3%: 在默认 2% 阈值外，但在自定义 5% 阈值内
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1030.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.is_accurate is True
        assert report.alert_triggered is False


class TestCostAccuracyRegressionScenarios:
    """回归测试 - 使用典型训练任务数据模式验证准确率."""

    @pytest.fixture
    def mock_cost_explorer(self) -> AsyncMock:
        return AsyncMock(spec=ICostExplorerClient)

    @pytest.fixture
    def mock_usage_query(self) -> AsyncMock:
        mock = AsyncMock(spec=IResourceUsageQuery)
        mock.build_training_conditions.return_value = []
        return mock

    @pytest.fixture
    def validator(self, mock_cost_explorer, mock_usage_query) -> CostAccuracyValidator:
        return CostAccuracyValidator(
            cost_explorer=mock_cost_explorer,
            usage_query=mock_usage_query,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario,actual_compute,actual_storage,actual_network,calculated_total,should_pass",
        [
            # 场景 1: 小规模训练 - 准确匹配
            ("small_training_exact", "350.00", "100.00", "50.00", Decimal("500.00"), True),
            # 场景 2: 中规模训练 - 1% 偏差
            ("medium_training_1pct", "3500.00", "1000.00", "500.00", Decimal("5050.00"), True),
            # 场景 3: 大规模训练 - 1.5% 偏差
            ("large_training_1.5pct", "35000.00", "10000.00", "5000.00", Decimal("50750.00"), True),
            # 场景 4: GPU 密集训练 - 精确匹配
            ("gpu_intensive_exact", "7000.00", "500.00", "200.00", Decimal("7700.00"), True),
            # 场景 5: 存储密集场景 - 1.8% 偏差
            ("storage_heavy_1.8pct", "500.00", "4000.00", "300.00", Decimal("4886.40"), True),
            # 场景 6: 偏差 3% - 触发告警
            ("over_threshold_3pct", "700.00", "200.00", "100.00", Decimal("1030.00"), False),
            # 场景 7: 偏差 5% - 明确超限
            ("over_threshold_5pct", "7000.00", "2000.00", "1000.00", Decimal("10500.00"), False),
            # 场景 8: 低估 4% - 也触发告警
            ("underestimate_4pct", "700.00", "200.00", "100.00", Decimal("960.00"), False),
        ],
    )
    async def test_regression_scenario(
        self,
        validator,
        mock_cost_explorer,
        mock_usage_query,
        scenario,
        actual_compute,
        actual_storage,
        actual_network,
        calculated_total,
        should_pass,
    ):
        """回归测试场景: {scenario}."""
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute=actual_compute,
            storage=actual_storage,
            network=actual_network,
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(calculated_total)

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.is_accurate is should_pass, (
            f"场景 '{scenario}': 误差率 {report.overall_error_rate:.4%}, " f"期望 {'通过' if should_pass else '告警'}"
        )
        assert report.alert_triggered is (not should_pass)


class TestCostAccuracyAlertBehavior:
    """准确率监控告警行为测试."""

    @pytest.fixture
    def mock_cost_explorer(self) -> AsyncMock:
        return AsyncMock(spec=ICostExplorerClient)

    @pytest.fixture
    def mock_usage_query(self) -> AsyncMock:
        mock = AsyncMock(spec=IResourceUsageQuery)
        mock.build_training_conditions.return_value = []
        return mock

    @pytest.fixture
    def validator(self, mock_cost_explorer, mock_usage_query) -> CostAccuracyValidator:
        return CostAccuracyValidator(
            cost_explorer=mock_cost_explorer,
            usage_query=mock_usage_query,
        )

    @pytest.mark.asyncio
    async def test_alert_message_contains_details(self, validator, mock_cost_explorer, mock_usage_query):
        """告警消息包含关键数据."""
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1100.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.alert_triggered is True
        # 告警消息包含: 误差率、计算成本、实际成本、差异
        assert "误差率" in report.alert_message
        assert "计算成本" in report.alert_message
        assert "实际成本" in report.alert_message
        assert "差异" in report.alert_message

    @pytest.mark.asyncio
    async def test_no_alert_at_exact_threshold(self, validator, mock_cost_explorer, mock_usage_query):
        """误差率恰好等于 2% 时不触发告警 (边界条件)."""
        # 实际 total=1000, 计算 total=1020 → 误差率 = 2%
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1020.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.overall_error_rate == Decimal("0.020000")
        assert report.is_accurate is True
        assert report.alert_triggered is False

    @pytest.mark.asyncio
    async def test_alert_just_over_threshold(self, validator, mock_cost_explorer, mock_usage_query):
        """误差率略超 2% 时触发告警."""
        # 实际 total=1000, 计算 total=1021 → 误差率 = 2.1%
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response(
            compute="700.00", storage="200.00", network="100.00"
        )
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1021.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        assert report.overall_error_rate > Decimal("0.02")
        assert report.is_accurate is False
        assert report.alert_triggered is True

    @pytest.mark.asyncio
    async def test_date_range_passed_to_report(self, validator, mock_cost_explorer, mock_usage_query):
        """验证日期范围正确传递到报告."""
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response()
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1250.00"))

        start = datetime(2026, 1, 1)
        end = datetime(2026, 2, 1)

        report = await validator.validate(start_date=start, end_date=end)

        assert report.start_date == start
        assert report.end_date == end

    @pytest.mark.asyncio
    async def test_cost_explorer_called_with_correct_params(self, validator, mock_cost_explorer, mock_usage_query):
        """验证 Cost Explorer 接收正确的查询参数."""
        mock_cost_explorer.get_cost_and_usage.return_value = _make_cost_explorer_response()
        mock_usage_query.get_training_job_stats_by_period.return_value = []

        start = datetime(2026, 1, 1)
        end = datetime(2026, 2, 1)

        await validator.validate(start_date=start, end_date=end)

        mock_cost_explorer.get_cost_and_usage.assert_called_once_with(
            start_date=start,
            end_date=end,
            granularity="MONTHLY",
            metrics=["UnblendedCost"],
            group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )


class TestCostExplorerResponseParsing:
    """Cost Explorer 响应解析测试."""

    @pytest.fixture
    def mock_cost_explorer(self) -> AsyncMock:
        return AsyncMock(spec=ICostExplorerClient)

    @pytest.fixture
    def mock_usage_query(self) -> AsyncMock:
        mock = AsyncMock(spec=IResourceUsageQuery)
        mock.build_training_conditions.return_value = []
        return mock

    @pytest.fixture
    def validator(self, mock_cost_explorer, mock_usage_query) -> CostAccuracyValidator:
        return CostAccuracyValidator(
            cost_explorer=mock_cost_explorer,
            usage_query=mock_usage_query,
        )

    @pytest.mark.asyncio
    async def test_multiple_compute_services_aggregated(self, validator, mock_cost_explorer, mock_usage_query):
        """多个计算服务 (EC2 + SageMaker) 正确聚合."""
        mock_cost_explorer.get_cost_and_usage.return_value = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2026-01-01", "End": "2026-02-01"},
                    "Groups": [
                        {
                            "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                            "Metrics": {"UnblendedCost": {"Amount": "500.00", "Unit": "USD"}},
                        },
                        {
                            "Keys": ["Amazon SageMaker"],
                            "Metrics": {"UnblendedCost": {"Amount": "300.00", "Unit": "USD"}},
                        },
                    ],
                }
            ]
        }
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("800.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        # 实际总成本 = 500 + 300 = 800
        assert report.total_actual == Decimal("800.00")

    @pytest.mark.asyncio
    async def test_fsx_classified_as_storage(self, validator, mock_cost_explorer, mock_usage_query):
        """FSx 服务正确归类为存储成本."""
        mock_cost_explorer.get_cost_and_usage.return_value = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2026-01-01", "End": "2026-02-01"},
                    "Groups": [
                        {
                            "Keys": ["Amazon FSx"],
                            "Metrics": {"UnblendedCost": {"Amount": "150.00", "Unit": "USD"}},
                        },
                        {
                            "Keys": ["Amazon Elastic Block Store"],
                            "Metrics": {"UnblendedCost": {"Amount": "50.00", "Unit": "USD"}},
                        },
                    ],
                }
            ]
        }
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("200.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 2, 1),
        )

        # 存储类别实际成本 = FSx(150) + EBS(50) = 200
        storage_item = next(item for item in report.items if item.category == "storage")
        assert storage_item.actual_cost == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_multiple_time_periods_aggregated(self, validator, mock_cost_explorer, mock_usage_query):
        """多个时间段的成本正确聚合."""
        mock_cost_explorer.get_cost_and_usage.return_value = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2026-01-01", "End": "2026-02-01"},
                    "Groups": [
                        {
                            "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                            "Metrics": {"UnblendedCost": {"Amount": "400.00", "Unit": "USD"}},
                        },
                    ],
                },
                {
                    "TimePeriod": {"Start": "2026-02-01", "End": "2026-03-01"},
                    "Groups": [
                        {
                            "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                            "Metrics": {"UnblendedCost": {"Amount": "600.00", "Unit": "USD"}},
                        },
                    ],
                },
            ]
        }
        mock_usage_query.get_training_job_stats_by_period.return_value = _make_training_stats(Decimal("1000.00"))

        report = await validator.validate(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 3, 1),
        )

        # 实际总成本 = 400 + 600 = 1000
        assert report.total_actual == Decimal("1000.00")
