"""AWS Cost Explorer 客户端接口定义 (T069a)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class ICostExplorerClient(ABC):
    """AWS Cost Explorer 客户端接口.

    提供 AWS 账单数据获取能力，支持按时间范围、服务类型、资源标签等维度查询成本数据。
    实现类应使用 aioboto3 进行异步 AWS 调用，并实现缓存策略 (1小时刷新)。
    """

    @abstractmethod
    async def get_cost_and_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "MONTHLY",
        metrics: list[str] | None = None,
        group_by: list[dict[str, str]] | None = None,
        filter_tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """获取指定时间范围的成本和使用数据.

        Args:
            start_date: 查询起始日期
            end_date: 查询结束日期
            granularity: 时间粒度 ('DAILY', 'MONTHLY', 'HOURLY')
            metrics: 指标列表 (默认: ['UnblendedCost'])
            group_by: 分组维度 (如: [{'Type': 'DIMENSION', 'Key': 'SERVICE'}])
            filter_tags: 按标签过滤 (如: {'project': 'ml-training'})

        Returns:
            dict: Cost Explorer API 返回的成本数据结构

        Example:
            >>> client = CostExplorerClient()
            >>> result = await client.get_cost_and_usage(
            ...     start_date=datetime(2025, 1, 1),
            ...     end_date=datetime(2025, 1, 31),
            ...     granularity='MONTHLY',
            ...     group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
            ...     filter_tags={'env': 'production'}
            ... )
            >>> print(result['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
            '1234.56'
        """
