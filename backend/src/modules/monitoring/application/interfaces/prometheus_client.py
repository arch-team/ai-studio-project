"""Prometheus 客户端接口定义 (Application 层).

将接口放在 Application 层，遵循 Clean Architecture 依赖方向：
Infrastructure 层实现应依赖 Application 层定义的抽象，而非反向。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class IPrometheusClient(ABC):
    """Prometheus 客户端接口."""

    @abstractmethod
    async def query_instant(self, query: str) -> list[dict[str, Any]]:
        """执行即时查询.

        Args:
            query: PromQL 查询语句

        Returns:
            查询结果列表
        """

    @abstractmethod
    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "1m",
    ) -> list[dict[str, Any]]:
        """执行范围查询.

        Args:
            query: PromQL 查询语句
            start: 开始时间
            end: 结束时间
            step: 时间步长

        Returns:
            查询结果列表
        """
