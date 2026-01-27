"""Billing API 依赖注入 (T071, T072)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db

from ..application.services import ReportService, UsageAggregatorService


async def get_usage_aggregator_service(
    session: AsyncSession = Depends(get_db),
) -> UsageAggregatorService:
    """获取资源使用聚合服务实例."""
    return UsageAggregatorService(session)


async def get_report_service(
    session: AsyncSession = Depends(get_db),
) -> ReportService:
    """获取报表服务实例."""
    return ReportService(session)
