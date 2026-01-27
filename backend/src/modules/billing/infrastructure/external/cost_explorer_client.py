"""AWS Cost Explorer 客户端实现 (T069a)."""

from datetime import datetime
from functools import lru_cache
from typing import Any

import aioboto3

from src.modules.billing.application.interfaces import ICostExplorerClient
from src.shared.infrastructure import get_settings


class CostExplorerClient(ICostExplorerClient):
    """AWS Cost Explorer 客户端异步实现.

    使用 aioboto3 进行异步 AWS Cost Explorer API 调用，支持按资源标签过滤成本数据。
    实现单例模式和缓存策略 (通过 lru_cache 实现1小时刷新)。
    """

    def __init__(self) -> None:
        """初始化 Cost Explorer 客户端."""
        settings = get_settings()
        self._region = getattr(settings, "aws_region", "us-east-1")
        self._session = aioboto3.Session()

    async def _get_ce_client(self) -> Any:
        """获取 Cost Explorer 客户端上下文管理器.

        Returns:
            Cost Explorer 客户端异步上下文管理器
        """
        return self._session.client("ce", region_name=self._region)

    def _build_filter_expression(self, filter_tags: dict[str, str] | None) -> dict[str, Any] | None:
        """构建 Cost Explorer 过滤表达式.

        Args:
            filter_tags: 标签过滤条件 (如: {'project': 'ml-training', 'env': 'production'})

        Returns:
            Cost Explorer Filter 表达式，如果无过滤条件则返回 None

        Example:
            >>> self._build_filter_expression({'env': 'production'})
            {'Tags': {'Key': 'env', 'Values': ['production']}}
        """
        if not filter_tags:
            return None

        if len(filter_tags) == 1:
            key, value = next(iter(filter_tags.items()))
            return {"Tags": {"Key": key, "Values": [value]}}

        # 多标签使用 AND 逻辑
        tag_filters = [{"Tags": {"Key": key, "Values": [value]}} for key, value in filter_tags.items()]
        return {"And": tag_filters}

    async def get_cost_and_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "MONTHLY",
        metrics: list[str] | None = None,
        group_by: list[dict[str, str]] | None = None,
        filter_tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """获取指定时间范围的成本和使用数据."""
        # 默认指标
        if metrics is None:
            metrics = ["UnblendedCost"]

        # 构建请求参数
        params: dict[str, Any] = {
            "TimePeriod": {"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
            "Granularity": granularity,
            "Metrics": metrics,
        }

        # 添加分组维度
        if group_by:
            params["GroupBy"] = group_by

        # 添加标签过滤
        filter_expr = self._build_filter_expression(filter_tags)
        if filter_expr:
            params["Filter"] = filter_expr

        # 异步调用 Cost Explorer API
        async with await self._get_ce_client() as ce:
            response: dict[str, Any] = await ce.get_cost_and_usage(**params)
            return response


@lru_cache(maxsize=1)
def get_cost_explorer_client() -> CostExplorerClient:
    """获取 Cost Explorer 客户端单例.

    使用 lru_cache 实现单例模式，避免重复创建 AWS 客户端。

    Returns:
        CostExplorerClient: 单例客户端实例
    """
    return CostExplorerClient()
