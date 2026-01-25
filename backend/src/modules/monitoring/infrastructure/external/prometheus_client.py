"""Prometheus HTTP API 客户端封装 (T062)."""

from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache
from typing import Any

import httpx

from src.shared.infrastructure import get_settings


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


class PrometheusClient(IPrometheusClient):
    """Prometheus HTTP API 客户端实现."""

    def __init__(self, endpoint: str | None = None, timeout: float = 30.0):
        """初始化 Prometheus 客户端.

        Args:
            endpoint: Prometheus 端点 URL
            timeout: 请求超时时间（秒）
        """
        settings = get_settings()
        self._endpoint = endpoint or getattr(settings, "prometheus_endpoint", "http://localhost:9090")
        self._timeout = timeout

    async def query_instant(self, query: str) -> list[dict[str, Any]]:
        """执行即时查询."""
        url = f"{self._endpoint}/api/v1/query"
        params = {"query": query}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                error_msg = data.get("error", "Unknown error")
                raise PrometheusQueryError(f"Prometheus query failed: {error_msg}")

            return data.get("data", {}).get("result", [])

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "1m",
    ) -> list[dict[str, Any]]:
        """执行范围查询."""
        url = f"{self._endpoint}/api/v1/query_range"
        params = {
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                error_msg = data.get("error", "Unknown error")
                raise PrometheusQueryError(f"Prometheus query failed: {error_msg}")

            return data.get("data", {}).get("result", [])


class PrometheusQueryError(Exception):
    """Prometheus 查询错误."""

    pass


@lru_cache(maxsize=1)
def get_prometheus_client() -> PrometheusClient:
    """获取 Prometheus 客户端单例."""
    return PrometheusClient()
