"""报表服务 - 资源使用和成本分析报表 (T071, T072)."""

from datetime import datetime, timedelta
from decimal import Decimal

from src.modules.billing.application.interfaces.resource_usage_query import IResourceUsageQuery
from src.modules.billing.application.services.usage_aggregator import _DATE_FORMAT_MAP

_ZERO = Decimal("0")


class CostProportions:
    """成本比例配置。"""

    COMPUTE_RATIO = Decimal("0.7")
    STORAGE_RATIO = Decimal("0.2")
    NETWORK_RATIO = Decimal("0.1")


def _paginate(items: list, page: int, page_size: int) -> tuple[list, int]:
    """对列表做内存分页，返回 (分页结果, 总数)。"""
    total = len(items)
    start = (page - 1) * page_size
    return items[start : start + page_size], total


class ReportService:
    """报表服务 - 提供资源使用和成本分析报表。"""

    def __init__(self, query: IResourceUsageQuery):
        self._query = query

    async def get_resource_usage_report(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: int | None = None,
        project_id: str | None = None,
        group_by: str = "day",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取资源使用报表 (T071)."""
        # 验证分组参数
        self._validate_group_by(group_by)

        # 获取时间序列统计数据
        stats_list = await self._fetch_time_series_stats(start_date, end_date, user_id, group_by)
        paginated_stats, total_records = _paginate(stats_list, page, page_size)

        # 计算存储使用量
        storage_gb_hours = await self._calculate_storage_usage(user_id, start_date, end_date, len(stats_list))

        # 构建数据点
        data_points = self._build_data_points(paginated_stats, storage_gb_hours, len(stats_list))

        # 计算汇总
        summary = self._calculate_summary(data_points, storage_gb_hours)

        return {
            "user_id": user_id,
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by,
            "data_points": data_points,
            **summary,
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
        }

    def _validate_group_by(self, group_by: str) -> None:
        """验证分组参数."""
        if group_by not in _DATE_FORMAT_MAP:
            raise ValueError(f"Invalid group_by: {group_by}")

    async def _fetch_time_series_stats(
        self, start_date: datetime, end_date: datetime, user_id: int | None, group_by: str
    ) -> list:
        """获取时间序列统计数据."""
        date_format = _DATE_FORMAT_MAP[group_by]
        conditions = await self._query.build_training_conditions(start_date, end_date, user_id)
        return await self._query.get_training_job_stats_by_period(date_format, conditions)

    async def _calculate_storage_usage(
        self, user_id: int | None, start_date: datetime, end_date: datetime, periods: int
    ) -> Decimal:
        """计算存储 GB 小时数."""
        if not user_id:
            return _ZERO

        storage = await self._query.get_storage_stats_by_user(user_id)
        duration_hours = (end_date - start_date).total_seconds() / 3600
        return storage.total_gb * Decimal(str(duration_hours))

    def _build_data_points(self, stats: list, storage_gb_hours: Decimal, total_periods: int) -> list[dict]:
        """构建数据点列表."""
        avg_storage = storage_gb_hours / total_periods if total_periods else _ZERO
        return [
            {
                "period_start": s.period_start,
                "period_end": s.period_end,
                "cpu_hours": s.cpu_hours,
                "gpu_hours": s.gpu_hours,
                "storage_gb_hours": avg_storage,
                "job_count": s.job_count,
            }
            for s in stats
        ]

    def _calculate_summary(self, data_points: list[dict], storage_gb_hours: Decimal) -> dict:
        """计算汇总数据."""
        return {
            "total_cpu_hours": sum((dp["cpu_hours"] for dp in data_points), start=_ZERO),
            "total_gpu_hours": sum((dp["gpu_hours"] for dp in data_points), start=_ZERO),
            "total_storage_gb_hours": storage_gb_hours,
            "total_jobs": sum(dp["job_count"] for dp in data_points),
        }

    async def get_cost_analysis_report(
        self,
        start_date: datetime,
        end_date: datetime,
        cost_type: str | None = None,
        user_id: int | None = None,
        project_id: str | None = None,
        include_forecast: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取成本分析报表 (T072)."""
        # 查询成本数据
        raw_data = await self._fetch_cost_data(start_date, end_date, user_id)
        paginated_rows, total_records = _paginate(raw_data, page, page_size)

        # 构建数据点
        data_points = self._build_cost_data_points(paginated_rows, cost_type)

        # 计算汇总统计
        summary = self._calculate_cost_summary(data_points)

        # 计算趋势和预测
        trend = self._calculate_cost_trend(data_points)
        forecast = self._calculate_forecast_if_needed(data_points, include_forecast)

        return {
            "user_id": user_id,
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date,
            "cost_type": cost_type,
            "data_points": data_points,
            **summary,
            "trend": trend,
            "forecast": forecast,
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
        }

    async def _fetch_cost_data(self, start_date: datetime, end_date: datetime, user_id: int | None) -> list:
        """获取成本原始数据。"""
        conditions = await self._query.build_training_conditions(start_date, end_date, user_id)
        return await self._query.get_training_cost_by_period(
            date_format="%Y-%m-%d",
            conditions=conditions,
            compute_ratio=CostProportions.COMPUTE_RATIO,
            storage_ratio=CostProportions.STORAGE_RATIO,
            network_ratio=CostProportions.NETWORK_RATIO,
        )

    def _build_cost_data_points(self, rows: list, cost_type: str | None) -> list[dict]:
        """构建成本数据点。"""
        return [
            {
                "period_start": row["period_start"],
                "period_end": row["period_end"],
                "compute_cost": row["compute_cost"] if not cost_type or cost_type == "compute" else _ZERO,
                "storage_cost": row["storage_cost"] if not cost_type or cost_type == "storage" else _ZERO,
                "network_cost": row["network_cost"] if not cost_type or cost_type == "network" else _ZERO,
                "total_cost": self._calculate_row_total(row, cost_type),
            }
            for row in rows
        ]

    def _calculate_row_total(self, row: dict, cost_type: str | None) -> Decimal:
        """计算单行总成本。"""
        if not cost_type:
            return row["total_cost"]
        return row["compute_cost"] + row["storage_cost"] + row["network_cost"]

    def _calculate_cost_summary(self, data_points: list[dict]) -> dict:
        """计算成本汇总统计。"""
        total_compute = sum((dp["compute_cost"] for dp in data_points), start=_ZERO)
        total_storage = sum((dp["storage_cost"] for dp in data_points), start=_ZERO)
        total_network = sum((dp["network_cost"] for dp in data_points), start=_ZERO)

        return {
            "total_compute_cost": total_compute,
            "total_storage_cost": total_storage,
            "total_network_cost": total_network,
            "grand_total_cost": total_compute + total_storage + total_network,
        }

    def _calculate_forecast_if_needed(self, data_points: list[dict], include_forecast: bool) -> dict | None:
        """根据条件计算成本预测。"""
        if include_forecast and len(data_points) >= 7:
            return self._calculate_cost_forecast(data_points)
        return None

    def _calculate_cost_trend(self, data_points: list[dict]) -> dict | None:
        """计算成本趋势."""
        if len(data_points) < 2:
            return None

        # 简单趋势分析: 比较前后两半时期的平均成本
        mid = len(data_points) // 2
        first_half = data_points[:mid]
        second_half = data_points[mid:]

        first_half_avg = sum((dp["total_cost"] for dp in first_half), start=_ZERO) / len(first_half)
        second_half_avg = sum((dp["total_cost"] for dp in second_half), start=_ZERO) / len(second_half)

        if first_half_avg == 0:
            change_percent = _ZERO
        else:
            change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100

        # 判断趋势方向
        if abs(change_percent) < 5:
            trend_direction = "stable"
        elif change_percent > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"

        return {
            "trend_direction": trend_direction,
            "change_percent": change_percent,
            "previous_period_cost": first_half_avg,
            "current_period_cost": second_half_avg,
        }

    def _calculate_cost_forecast(self, data_points: list[dict]) -> list[dict]:
        """计算成本预测 (简单线性预测)."""
        if len(data_points) < 7:
            return []

        # 简单线性回归预测
        recent_costs = [dp["total_cost"] for dp in data_points[-7:]]
        avg_cost = sum(recent_costs, start=_ZERO) / len(recent_costs)

        # 计算趋势斜率
        x_values = list(range(len(recent_costs)))
        x_mean = sum(x_values) / len(x_values)
        y_mean = avg_cost

        numerator = sum((x - x_mean) * (float(y) - float(y_mean)) for x, y in zip(x_values, recent_costs))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            slope = _ZERO
        else:
            slope = Decimal(str(numerator / denominator))

        # 预测未来 7 天
        forecast = []
        last_date = data_points[-1]["period_start"]

        for i in range(1, 8):
            forecast_date = last_date + timedelta(days=i)
            estimated_cost = avg_cost + slope * i
            estimated_cost = max(estimated_cost, _ZERO)  # 确保非负

            # 置信度随时间递减
            confidence_level = max(0.5, 1.0 - (i * 0.05))

            forecast.append(
                {
                    "forecast_date": forecast_date,
                    "estimated_cost": estimated_cost,
                    "confidence_level": confidence_level,
                }
            )

        return forecast
