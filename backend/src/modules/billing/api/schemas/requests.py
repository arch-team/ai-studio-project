"""报表 API 请求 Schema (T071, T072)."""

from datetime import datetime

from pydantic import BaseModel, Field


class ResourceUsageReportRequest(BaseModel):
    """资源使用报表查询请求 (T071)."""

    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    user_id: int | None = Field(None, description="用户 ID 过滤")
    project_id: str | None = Field(None, description="项目 ID 过滤")
    group_by: str = Field(default="day", description="时间维度分组 (day/week/month)")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class CostAnalysisReportRequest(BaseModel):
    """成本分析报表查询请求 (T072)."""

    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    cost_type: str | None = Field(None, description="成本类型过滤 (compute/storage/network)")
    user_id: int | None = Field(None, description="用户 ID 过滤")
    project_id: str | None = Field(None, description="项目 ID 过滤")
    include_forecast: bool = Field(default=False, description="是否包含成本预测")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
