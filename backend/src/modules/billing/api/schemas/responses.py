"""报表 API 响应 Schema (T071, T072)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ResourceUsageDataPoint(BaseModel):
    """资源使用数据点."""

    period_start: datetime = Field(..., description="时间段开始")
    period_end: datetime | None = Field(None, description="时间段结束")
    cpu_hours: Decimal = Field(..., description="CPU 小时数")
    gpu_hours: Decimal = Field(..., description="GPU 小时数")
    storage_gb_hours: Decimal = Field(..., description="存储 GB 小时数")
    job_count: int = Field(..., description="训练任务数")


class ResourceUsageReportResponse(BaseModel):
    """资源使用报表响应 (T071)."""

    user_id: int | None = Field(None, description="用户 ID")
    project_id: str | None = Field(None, description="项目 ID")
    start_date: datetime = Field(..., description="查询开始日期")
    end_date: datetime = Field(..., description="查询结束日期")
    group_by: str = Field(..., description="分组维度")
    data_points: list[ResourceUsageDataPoint] = Field(..., description="资源使用时间序列数据")
    total_cpu_hours: Decimal = Field(..., description="总 CPU 小时数")
    total_gpu_hours: Decimal = Field(..., description="总 GPU 小时数")
    total_storage_gb_hours: Decimal = Field(..., description="总存储 GB 小时数")
    total_jobs: int = Field(..., description="总任务数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_records: int = Field(..., description="总记录数")


class CostDataPoint(BaseModel):
    """成本数据点."""

    period_start: datetime = Field(..., description="时间段开始")
    period_end: datetime | None = Field(None, description="时间段结束")
    compute_cost: Decimal = Field(..., description="计算成本 (USD)")
    storage_cost: Decimal = Field(..., description="存储成本 (USD)")
    network_cost: Decimal = Field(..., description="网络成本 (USD)")
    total_cost: Decimal = Field(..., description="总成本 (USD)")


class CostForecast(BaseModel):
    """成本预测."""

    forecast_date: datetime = Field(..., description="预测日期")
    estimated_cost: Decimal = Field(..., description="预估成本 (USD)")
    confidence_level: float = Field(..., ge=0, le=1, description="置信度 (0-1)")


class CostTrend(BaseModel):
    """成本趋势分析."""

    trend_direction: str = Field(..., description="趋势方向 (increasing/decreasing/stable)")
    change_percent: Decimal = Field(..., description="变化百分比")
    previous_period_cost: Decimal = Field(..., description="上一周期成本 (USD)")
    current_period_cost: Decimal = Field(..., description="当前周期成本 (USD)")


class CostAnalysisReportResponse(BaseModel):
    """成本分析报表响应 (T072)."""

    user_id: int | None = Field(None, description="用户 ID")
    project_id: str | None = Field(None, description="项目 ID")
    start_date: datetime = Field(..., description="查询开始日期")
    end_date: datetime = Field(..., description="查询结束日期")
    cost_type: str | None = Field(None, description="成本类型过滤")
    data_points: list[CostDataPoint] = Field(..., description="成本时间序列数据")
    total_compute_cost: Decimal = Field(..., description="总计算成本 (USD)")
    total_storage_cost: Decimal = Field(..., description="总存储成本 (USD)")
    total_network_cost: Decimal = Field(..., description="总网络成本 (USD)")
    grand_total_cost: Decimal = Field(..., description="总成本 (USD)")
    trend: CostTrend | None = Field(None, description="成本趋势分析")
    forecast: list[CostForecast] | None = Field(None, description="成本预测数据")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_records: int = Field(..., description="总记录数")
