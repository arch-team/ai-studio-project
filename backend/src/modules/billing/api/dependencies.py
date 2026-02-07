"""Billing API 依赖注入 (T071, T072)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db

from ..application.interfaces import IResourceUsageQuery
from ..application.services import ReportService, UsageAggregatorService
from ..infrastructure.repositories.resource_usage_query_impl import ResourceUsageQueryImpl


async def get_resource_usage_query(
    session: AsyncSession = Depends(get_db),
) -> IResourceUsageQuery:
    """获取资源使用查询实例."""
    return ResourceUsageQueryImpl(session)


async def get_usage_aggregator_service(
    query: IResourceUsageQuery = Depends(get_resource_usage_query),
) -> UsageAggregatorService:
    """获取资源使用聚合服务实例."""
    return UsageAggregatorService(query)


async def get_report_service(
    query: IResourceUsageQuery = Depends(get_resource_usage_query),
) -> ReportService:
    """获取报表服务实例."""
    return ReportService(query)
