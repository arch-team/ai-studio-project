"""成本准确率验证服务 (T069c).

对比平台计算成本 vs AWS Cost Explorer 实际账单，计算误差率，
支持准确率监控告警 (误差 >2% 触发)。
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

import structlog

from src.modules.billing.application.interfaces import ICostExplorerClient, IResourceUsageQuery
from src.modules.billing.application.services.cost_calculator import CostCalculator
from src.modules.billing.application.services.pricing_model import PricingModelService

logger = structlog.get_logger(__name__)


# 默认误差率阈值 (2%)
DEFAULT_ERROR_THRESHOLD = Decimal("0.02")


@dataclass
class CostComparisonItem:
    """单项成本对比结果."""

    category: str  # compute / storage / network / total
    calculated_cost: Decimal
    actual_cost: Decimal
    difference: Decimal
    error_rate: Decimal  # 绝对误差率

    @property
    def is_within_threshold(self) -> bool:
        """误差率是否在 2% 阈值以内."""
        return self.error_rate <= DEFAULT_ERROR_THRESHOLD


@dataclass
class CostAccuracyReport:
    """成本准确率验证报告."""

    start_date: datetime
    end_date: datetime
    items: list[CostComparisonItem] = field(default_factory=list)
    overall_error_rate: Decimal = Decimal("0")
    is_accurate: bool = True
    alert_triggered: bool = False
    alert_message: str = ""

    @property
    def total_calculated(self) -> Decimal:
        """平台计算总成本."""
        for item in self.items:
            if item.category == "total":
                return item.calculated_cost
        return Decimal("0")

    @property
    def total_actual(self) -> Decimal:
        """Cost Explorer 实际总成本."""
        for item in self.items:
            if item.category == "total":
                return item.actual_cost
        return Decimal("0")


class CostAccuracyValidator:
    """成本准确率验证器.

    对比平台计算成本 vs AWS Cost Explorer 实际账单数据。
    目标: 误差率 <2%。超过阈值时触发告警。
    """

    def __init__(
        self,
        cost_explorer: ICostExplorerClient,
        usage_query: IResourceUsageQuery,
        pricing_service: PricingModelService | None = None,
        calculator: CostCalculator | None = None,
        error_threshold: Decimal = DEFAULT_ERROR_THRESHOLD,
    ) -> None:
        self._cost_explorer = cost_explorer
        self._usage_query = usage_query
        self._pricing_service = pricing_service or PricingModelService()
        self._calculator = calculator or CostCalculator()
        self._error_threshold = error_threshold

    @staticmethod
    def calculate_error_rate(calculated: Decimal, actual: Decimal) -> Decimal:
        """计算误差率 (绝对值).

        公式: |calculated - actual| / actual
        当实际成本为 0 时: 如果计算成本也为 0 则误差率为 0，否则为 100%。
        """
        if actual == Decimal("0"):
            return Decimal("0") if calculated == Decimal("0") else Decimal("1")

        error = abs(calculated - actual) / actual
        return error.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _build_comparison_item(
        self,
        category: str,
        calculated: Decimal,
        actual: Decimal,
    ) -> CostComparisonItem:
        """构建单项成本对比结果."""
        difference = calculated - actual
        error_rate = self.calculate_error_rate(calculated, actual)

        return CostComparisonItem(
            category=category,
            calculated_cost=calculated,
            actual_cost=actual,
            difference=difference,
            error_rate=error_rate,
        )

    async def _get_actual_costs(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Decimal]:
        """从 Cost Explorer 获取实际成本数据.

        Returns:
            按类别分类的实际成本: {compute, storage, network, total}
        """
        # 按服务分组查询成本
        result = await self._cost_explorer.get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            granularity="MONTHLY",
            metrics=["UnblendedCost"],
            group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        compute_cost = Decimal("0")
        storage_cost = Decimal("0")
        network_cost = Decimal("0")

        # 解析 Cost Explorer 响应
        for time_period in result.get("ResultsByTime", []):
            for group in time_period.get("Groups", []):
                service_name = group.get("Keys", [""])[0]
                amount_str = group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0")
                amount = Decimal(amount_str)

                # 按 AWS 服务名称归类到成本维度
                if service_name in (
                    "Amazon Elastic Compute Cloud - Compute",
                    "Amazon SageMaker",
                ):
                    compute_cost += amount
                elif service_name in (
                    "Amazon Simple Storage Service",
                    "Amazon FSx",
                    "Amazon Elastic Block Store",
                ):
                    storage_cost += amount
                elif service_name in (
                    "AWS Data Transfer",
                    "Amazon EC2 - Data Transfer",
                ):
                    network_cost += amount

        total_cost = compute_cost + storage_cost + network_cost

        return {
            "compute": compute_cost,
            "storage": storage_cost,
            "network": network_cost,
            "total": total_cost,
        }

    async def _get_calculated_costs(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Decimal]:
        """从平台使用数据计算预期成本.

        Returns:
            按类别分类的计算成本: {compute, storage, network, total}
        """
        # 构建时间范围查询条件
        conditions = await self._usage_query.build_training_conditions(
            start_date=start_date,
            end_date=end_date,
        )

        # 按月聚合训练任务统计
        stats = await self._usage_query.get_training_job_stats_by_period(
            date_format="%Y-%m",
            conditions=conditions,
        )

        # 汇总平台计算的成本
        total_computed_cost = Decimal("0")
        for stat in stats:
            total_computed_cost += Decimal(str(stat.estimated_cost_usd))

        # 使用固定比例拆分 (与 report_service 一致: 计算 70%, 存储 20%, 网络 10%)
        compute_ratio = Decimal("0.70")
        storage_ratio = Decimal("0.20")
        network_ratio = Decimal("0.10")

        return {
            "compute": (total_computed_cost * compute_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "storage": (total_computed_cost * storage_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "network": (total_computed_cost * network_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "total": total_computed_cost,
        }

    async def validate(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> CostAccuracyReport:
        """执行成本准确率验证.

        对比平台计算成本 vs AWS Cost Explorer 实际账单。

        Args:
            start_date: 验证起始日期
            end_date: 验证结束日期

        Returns:
            成本准确率验证报告
        """
        report = CostAccuracyReport(
            start_date=start_date,
            end_date=end_date,
        )

        # 获取实际成本和计算成本
        actual_costs = await self._get_actual_costs(start_date, end_date)
        calculated_costs = await self._get_calculated_costs(start_date, end_date)

        # 构建对比项
        for category in ("compute", "storage", "network", "total"):
            item = self._build_comparison_item(
                category=category,
                calculated=calculated_costs[category],
                actual=actual_costs[category],
            )
            report.items.append(item)

        # 以 total 类别的误差率作为整体误差率
        total_item = report.items[-1]
        report.overall_error_rate = total_item.error_rate
        report.is_accurate = total_item.error_rate <= self._error_threshold

        # 告警判定
        if not report.is_accurate:
            report.alert_triggered = True
            report.alert_message = (
                f"成本准确率告警: 误差率 {total_item.error_rate:.4%} "
                f"超过阈值 {self._error_threshold:.0%}。"
                f"计算成本: ${total_item.calculated_cost:.2f}, "
                f"实际成本: ${total_item.actual_cost:.2f}, "
                f"差异: ${total_item.difference:.2f}"
            )
            logger.warning(
                "cost_accuracy_alert",
                error_rate=float(total_item.error_rate),
                calculated=float(total_item.calculated_cost),
                actual=float(total_item.actual_cost),
                threshold=float(self._error_threshold),
            )

        return report
