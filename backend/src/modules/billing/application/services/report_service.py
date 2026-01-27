"""报表服务 - 资源使用和成本分析报表 (T071, T072)."""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.datasets.infrastructure.models.dataset_model import DatasetModel
from src.modules.training.infrastructure.models.training_job_model import TrainingJobModel


class ReportService:
    """报表服务 - 提供资源使用和成本分析报表."""

    def __init__(self, session: AsyncSession):
        self._session = session

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
        """获取资源使用报表 (T071).

        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户 ID 过滤
            project_id: 项目 ID 过滤
            group_by: 时间维度分组 (day/week/month)
            page: 页码
            page_size: 每页数量

        Returns:
            包含资源使用时间序列数据和统计汇总的字典
        """
        # 根据时间维度选择分组格式
        date_format_map = {
            "day": "%Y-%m-%d",
            "week": "%Y-%u",
            "month": "%Y-%m",
        }

        if group_by not in date_format_map:
            raise ValueError(f"Invalid group_by: {group_by}")

        date_format = date_format_map[group_by]
        period_column = func.date_format(TrainingJobModel.completed_at, date_format).label("period")

        # 构建基础查询条件
        conditions = [
            TrainingJobModel.status == "completed",
            TrainingJobModel.completed_at >= start_date,
            TrainingJobModel.completed_at <= end_date,
        ]

        if user_id:
            conditions.append(TrainingJobModel.owner_id == user_id)

        if project_id:
            conditions.append(TrainingJobModel.project_id == project_id)

        # 时间序列数据查询
        stmt = (
            select(
                period_column,
                func.min(TrainingJobModel.completed_at).label("period_start"),
                func.max(TrainingJobModel.completed_at).label("period_end"),
                # Note: total_cpu_hours 字段暂未实现，使用 duration_seconds 估算
                func.coalesce(
                    func.sum(TrainingJobModel.duration_seconds / Decimal("3600") * TrainingJobModel.node_count),
                    Decimal("0"),
                ).label("cpu_hours"),
                func.coalesce(func.sum(TrainingJobModel.total_gpu_hours), Decimal("0")).label("gpu_hours"),
                func.count(TrainingJobModel.id).label("job_count"),
            )
            .where(and_(*conditions))
            .group_by(period_column)
            .order_by(period_column)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        # 分页
        total_records = len(rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_rows = rows[start_idx:end_idx]

        # 计算存储 GB 小时数 (简化计算，实际需要按时间积分)
        storage_gb_hours = Decimal("0")
        if user_id:
            storage_stmt = (
                select(
                    func.coalesce(func.sum(DatasetModel.total_size_bytes / 1024 / 1024 / 1024), Decimal("0")).label(
                        "total_gb"
                    )
                )
                .where(DatasetModel.owner_id == user_id)
                .where(DatasetModel.status == "available")
            )
            storage_result = await self._session.execute(storage_stmt)
            total_gb = storage_result.scalar_one()
            # 简化计算: 存储大小 × 时间范围小时数
            duration_hours = (end_date - start_date).total_seconds() / 3600
            storage_gb_hours = total_gb * Decimal(str(duration_hours))

        # 构建数据点列表
        data_points = [
            {
                "period_start": row.period_start,
                "period_end": row.period_end,
                "cpu_hours": row.cpu_hours,
                "gpu_hours": row.gpu_hours,
                "storage_gb_hours": storage_gb_hours / len(rows) if rows else Decimal("0"),
                "job_count": row.job_count,
            }
            for row in paginated_rows
        ]

        # 统计汇总
        total_cpu_hours = sum((dp["cpu_hours"] for dp in data_points), start=Decimal("0"))
        total_gpu_hours = sum((dp["gpu_hours"] for dp in data_points), start=Decimal("0"))
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
        """获取成本分析报表 (T072).

        Args:
            start_date: 开始日期
            end_date: 结束日期
            cost_type: 成本类型过滤 (compute/storage/network)
            user_id: 用户 ID 过滤
            project_id: 项目 ID 过滤
            include_forecast: 是否包含成本预测
            page: 页码
            page_size: 每页数量

        Returns:
            包含成本时间序列数据、趋势分析和预测的字典
        """
        # 构建查询条件
        conditions = [
            TrainingJobModel.status == "completed",
            TrainingJobModel.completed_at >= start_date,
            TrainingJobModel.completed_at <= end_date,
        ]

        if user_id:
            conditions.append(TrainingJobModel.owner_id == user_id)

        # Note: project_id 字段暂未在 TrainingJobModel 中实现
        # if project_id:
        #     conditions.append(TrainingJobModel.project_id == project_id)

        # 按天分组查询成本数据
        period_column = func.date_format(TrainingJobModel.completed_at, "%Y-%m-%d").label("period")

        # Note: 当前 TrainingJobModel 只有 estimated_cost_usd 字段
        # compute_cost_usd, storage_cost_usd, network_cost_usd 字段需要后续添加
        # 暂时使用 estimated_cost_usd 作为 total_cost，其他成本字段设为 0
        stmt = (
            select(
                period_column,
                func.min(TrainingJobModel.completed_at).label("period_start"),
                func.max(TrainingJobModel.completed_at).label("period_end"),
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd * Decimal("0.7")), Decimal("0")).label(
                    "compute_cost"
                ),  # 假设计算成本占 70%
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd * Decimal("0.2")), Decimal("0")).label(
                    "storage_cost"
                ),  # 假设存储成本占 20%
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd * Decimal("0.1")), Decimal("0")).label(
                    "network_cost"
                ),  # 假设网络成本占 10%
                func.coalesce(func.sum(TrainingJobModel.estimated_cost_usd), Decimal("0")).label("total_cost"),
            )
            .where(and_(*conditions))
            .group_by(period_column)
            .order_by(period_column)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        # 分页
        total_records = len(rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_rows = rows[start_idx:end_idx]

        # 构建数据点列表
        data_points = [
            {
                "period_start": row.period_start,
                "period_end": row.period_end,
                "compute_cost": row.compute_cost if not cost_type or cost_type == "compute" else Decimal("0"),
                "storage_cost": row.storage_cost if not cost_type or cost_type == "storage" else Decimal("0"),
                "network_cost": row.network_cost if not cost_type or cost_type == "network" else Decimal("0"),
                "total_cost": (
                    row.total_cost if not cost_type else row.compute_cost + row.storage_cost + row.network_cost
                ),
            }
            for row in paginated_rows
        ]

        # 统计汇总
        total_compute_cost = sum((dp["compute_cost"] for dp in data_points), start=Decimal("0"))
        total_storage_cost = sum((dp["storage_cost"] for dp in data_points), start=Decimal("0"))
        total_network_cost = sum((dp["network_cost"] for dp in data_points), start=Decimal("0"))
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
        """计算成本趋势.

        Args:
            data_points: 成本数据点列表

        Returns:
            成本趋势分析结果
        """
        if len(data_points) < 2:
            return None

        # 简单趋势分析: 比较前后两半时期的平均成本
        mid = len(data_points) // 2
        first_half = data_points[:mid]
        second_half = data_points[mid:]

        first_half_avg = sum((dp["total_cost"] for dp in first_half), start=Decimal("0")) / len(first_half)
        second_half_avg = sum((dp["total_cost"] for dp in second_half), start=Decimal("0")) / len(second_half)

        if first_half_avg == 0:
            change_percent = Decimal("0")
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
        """计算成本预测 (简单线性预测).

        Args:
            data_points: 成本数据点列表

        Returns:
            未来 7 天的成本预测列表
        """
        if len(data_points) < 7:
            return []

        # 简单线性回归预测
        recent_costs = [dp["total_cost"] for dp in data_points[-7:]]
        avg_cost = sum(recent_costs, start=Decimal("0")) / len(recent_costs)

        # 计算趋势斜率
        x_values = list(range(len(recent_costs)))
        x_mean = sum(x_values) / len(x_values)
        y_mean = avg_cost

        numerator = sum((x - x_mean) * (float(y) - float(y_mean)) for x, y in zip(x_values, recent_costs))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            slope = Decimal("0")
        else:
            slope = Decimal(str(numerator / denominator))

        # 预测未来 7 天
        forecast = []
        last_date = data_points[-1]["period_start"]

        for i in range(1, 8):
            forecast_date = last_date + timedelta(days=i)
            estimated_cost = avg_cost + slope * i
            estimated_cost = max(estimated_cost, Decimal("0"))  # 确保非负

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
