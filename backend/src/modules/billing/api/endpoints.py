"""Billing 报表 API 端点 (T071, T072).

提供资源使用报表和成本分析报表查询接口。
"""

import structlog
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.modules.auth.api.dependencies import get_current_active_user

from ..application.services import CostAccuracyValidator, ReportService
from .dependencies import get_cost_accuracy_validator, get_report_service
from .schemas import CostAccuracyInfo, CostAnalysisReportResponse, ResourceUsageReportResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/reports/resource-usage", response_model=ResourceUsageReportResponse)
async def get_resource_usage_report(
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    user_id: int | None = Query(None, description="用户 ID 过滤"),
    project_id: str | None = Query(None, description="项目 ID 过滤"),
    group_by: str = Query(default="day", description="时间维度分组 (day/week/month)"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    _: None = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service),
) -> ResourceUsageReportResponse:
    """查询资源使用报表 (T071).

    支持功能:
    - 时间范围过滤 (start_date, end_date)
    - 用户/项目过滤 (user_id, project_id)
    - 按时间维度分组 (day, week, month)
    - 返回 CPU/GPU/Storage 使用统计
    - 支持分页

    Returns:
        ResourceUsageReportResponse: 包含资源使用时间序列数据和统计汇总
    """
    result = await report_service.get_resource_usage_report(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        project_id=project_id,
        group_by=group_by,
        page=page,
        page_size=page_size,
    )

    return ResourceUsageReportResponse(**result)


@router.get("/reports/cost-analysis", response_model=CostAnalysisReportResponse)
async def get_cost_analysis_report(
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    cost_type: str | None = Query(None, description="成本类型过滤 (compute/storage/network)"),
    user_id: int | None = Query(None, description="用户 ID 过滤"),
    project_id: str | None = Query(None, description="项目 ID 过滤"),
    include_forecast: bool = Query(default=False, description="是否包含成本预测"),
    validate: bool = Query(default=False, description="是否执行成本准确率验证 (对比 Cost Explorer)"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    _: None = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service),
    accuracy_validator: CostAccuracyValidator | None = Depends(get_cost_accuracy_validator),
) -> CostAnalysisReportResponse:
    """查询成本分析报表 (T072).

    支持功能:
    - 时间范围过滤
    - 成本类型过滤 (compute, storage, network)
    - 用户/项目级别钻取
    - 成本趋势分析
    - 成本预测 (可选)
    - 成本准确率验证 (可选, validate=True 时对比 Cost Explorer 账单)
    - 支持分页

    Returns:
        CostAnalysisReportResponse: 包含成本时间序列数据、趋势分析和预测
    """
    result = await report_service.get_cost_analysis_report(
        start_date=start_date,
        end_date=end_date,
        cost_type=cost_type,
        user_id=user_id,
        project_id=project_id,
        include_forecast=include_forecast,
        page=page,
        page_size=page_size,
    )

    # 成本准确率验证 (可选)
    accuracy_info = None
    if validate and accuracy_validator is not None:
        try:
            accuracy_report = await accuracy_validator.validate(
                start_date=start_date,
                end_date=end_date,
            )
            accuracy_info = CostAccuracyInfo(
                overall_error_rate=accuracy_report.overall_error_rate,
                is_accurate=accuracy_report.is_accurate,
                alert_triggered=accuracy_report.alert_triggered,
                alert_message=accuracy_report.alert_message,
                total_calculated=accuracy_report.total_calculated,
                total_actual=accuracy_report.total_actual,
            )
        except Exception:
            logger.warning(
                "cost_accuracy_validation_failed",
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                exc_info=True,
            )

    result["accuracy"] = accuracy_info

    return CostAnalysisReportResponse(**result)
