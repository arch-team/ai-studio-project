"""Billing API 依赖注入 (T071, T072)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db

from ..application.interfaces import ICostExplorerClient, IResourceUsageQuery
from ..application.services import CostAccuracyValidator, ReportService, UsageAggregatorService
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


async def get_cost_accuracy_validator(
    query: IResourceUsageQuery = Depends(get_resource_usage_query),
) -> CostAccuracyValidator | None:
    """获取成本准确率验证器实例。

    由于 ICostExplorerClient 需要 AWS 凭证，当不可用时返回 None。
    """
    try:
        from ..infrastructure.external.cost_explorer_client import CostExplorerClient

        cost_explorer: ICostExplorerClient = CostExplorerClient()
        return CostAccuracyValidator(
            cost_explorer=cost_explorer,
            usage_query=query,
        )
    except Exception:
        # Cost Explorer 客户端不可用时 (如本地开发环境) 返回 None
        return None
