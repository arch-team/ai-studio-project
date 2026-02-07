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
        if group_by not in _DATE_FORMAT_MAP:
            raise ValueError(f"Invalid group_by: {group_by}")

        date_format = _DATE_FORMAT_MAP[group_by]

        # 构建查询条件并获取时间序列数据
        conditions = await self._query.build_training_conditions(start_date, end_date, user_id)
        stats_list = await self._query.get_training_job_stats_by_period(date_format, conditions)

        paginated_stats, total_records = _paginate(stats_list, page, page_size)

        # 计算存储 GB 小时数（简化计算，实际需要按时间积分）
        storage_gb_hours = _ZERO
        if user_id:
            storage = await self._query.get_storage_stats_by_user(user_id)
            # 简化计算: 存储大小 x 时间范围小时数
            duration_hours = (end_date - start_date).total_seconds() / 3600
            storage_gb_hours = storage.total_gb * Decimal(str(duration_hours))

        # 构建数据点列表
        data_points = [
            {
                "period_start": s.period_start,
                "period_end": s.period_end,
                "cpu_hours": s.cpu_hours,
                "gpu_hours": s.gpu_hours,
                "storage_gb_hours": storage_gb_hours / len(stats_list) if stats_list else _ZERO,
                "job_count": s.job_count,
            }
            for s in paginated_stats
        ]

        # 统计汇总
        total_cpu_hours = sum((dp["cpu_hours"] for dp in data_points), start=_ZERO)
        total_gpu_hours = sum((dp["gpu_hours"] for dp in data_points), start=_ZERO)
        total_jobs = sum(dp["job_count"] for dp in data_points)

        return {
            "user_id": user_id,
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by,
            "data_points": data_points,
            "total_cpu_hours": total_cpu_hours,
            "total_gpu_hours": total_gpu_hours,
            "total_storage_gb_hours": storage_gb_hours,
            "total_jobs": total_jobs,
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
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
        # 构建查询条件
        conditions = await self._query.build_training_conditions(start_date, end_date, user_id)

        # 按天分组查询成本数据
        rows = await self._query.get_training_cost_by_period(
            date_format="%Y-%m-%d",
            conditions=conditions,
            compute_ratio=CostProportions.COMPUTE_RATIO,
            storage_ratio=CostProportions.STORAGE_RATIO,
            network_ratio=CostProportions.NETWORK_RATIO,
        )

        paginated_rows, total_records = _paginate(rows, page, page_size)

        # 构建数据点列表（按 cost_type 过滤非目标成本类型）
        data_points = [
            {
                "period_start": row["period_start"],
                "period_end": row["period_end"],
                "compute_cost": row["compute_cost"] if not cost_type or cost_type == "compute" else _ZERO,
                "storage_cost": row["storage_cost"] if not cost_type or cost_type == "storage" else _ZERO,
                "network_cost": row["network_cost"] if not cost_type or cost_type == "network" else _ZERO,
                "total_cost": (
                    row["total_cost"]
                    if not cost_type
                    else row["compute_cost"] + row["storage_cost"] + row["network_cost"]
                ),
            }
            for row in paginated_rows
        ]

        # 统计汇总
        total_compute_cost = sum((dp["compute_cost"] for dp in data_points), start=_ZERO)
        total_storage_cost = sum((dp["storage_cost"] for dp in data_points), start=_ZERO)
        total_network_cost = sum((dp["network_cost"] for dp in data_points), start=_ZERO)
        grand_total_cost = total_compute_cost + total_storage_cost + total_network_cost

        # 计算成本趋势
        trend = self._calculate_cost_trend(data_points)

        # 计算成本预测
        forecast = None
        if include_forecast and len(data_points) >= 7:
            forecast = self._calculate_cost_forecast(data_points)

        return {
            "user_id": user_id,
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date,
            "cost_type": cost_type,
            "data_points": data_points,
            "total_compute_cost": total_compute_cost,
            "total_storage_cost": total_storage_cost,
            "total_network_cost": total_network_cost,
            "grand_total_cost": grand_total_cost,
            "trend": trend,
            "forecast": forecast,
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
        }

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
