"""Prometheus HTTP API 客户端封装 (T062)."""

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any

import boto3
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from src.shared.domain.problem import Problem, problem
from src.shared.infrastructure import get_settings

from ...application.interfaces.prometheus_client import IPrometheusClient


@problem(503, "PROMETHEUS_QUERY_ERROR", "Prometheus 查询失败: {message}")
@dataclass
class PrometheusQueryError(Problem):
    """Prometheus 查询错误."""

    message: str


class PrometheusClient(IPrometheusClient):
    """Prometheus HTTP API 客户端实现."""

    def __init__(
        self,
        endpoint: str | None = None,
        timeout: float = 30.0,
        use_sigv4: bool | None = None,
    ):
        """初始化 Prometheus 客户端.

        Args:
            endpoint: Prometheus 端点 URL。回退链: amp_query_endpoint → prometheus_endpoint → 本地默认
            timeout: 请求超时时间（秒）
            use_sigv4: 是否对请求做 AWS SigV4 签名（查询 Amazon Managed Prometheus 必须）。
                显式传入优先；否则按端点是否含 "aps-workspaces" 自动判定。
        """
        settings = get_settings()
        self._endpoint = (
            endpoint
            or getattr(settings, "amp_query_endpoint", None)
            or getattr(settings, "prometheus_endpoint", None)
            or "http://localhost:9090"
        )
        self._timeout = timeout
        self._region = getattr(settings, "amp_region", "us-east-1")
        self._use_sigv4 = use_sigv4 if use_sigv4 is not None else ("aps-workspaces" in self._endpoint)

    def _sign_headers(self, method: str, url: str) -> dict[str, str]:
        """对发往 AMP 的请求做 SigV4 签名，返回需附加到 HTTP 请求的签名头.

        Args:
            method: HTTP 方法
            url: 含 query string 的完整请求 URL（签名必须作用于最终 URL）
        """
        credentials = boto3.Session().get_credentials()
        aws_request = AWSRequest(method=method, url=url)
        SigV4Auth(credentials, "aps", self._region).add_auth(aws_request)
        return dict(aws_request.headers)

    async def query_instant(self, query: str) -> list[dict[str, Any]]:
        """执行即时查询."""
        url = f"{self._endpoint}/api/v1/query"
        params = {"query": query}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            headers: dict[str, str] = {}
            if self._use_sigv4:
                signed_req = client.build_request("GET", url, params=params)
                headers = self._sign_headers("GET", str(signed_req.url))
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                error_msg = data.get("error", "Unknown error")
                raise PrometheusQueryError(message=f"Prometheus query failed: {error_msg}")

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
        params: dict[str, str | float] = {
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            headers: dict[str, str] = {}
            if self._use_sigv4:
                signed_req = client.build_request("GET", url, params=params)
                headers = self._sign_headers("GET", str(signed_req.url))
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                error_msg = data.get("error", "Unknown error")
                raise PrometheusQueryError(message=f"Prometheus query failed: {error_msg}")

            return data.get("data", {}).get("result", [])


@lru_cache(maxsize=1)
def get_prometheus_client() -> PrometheusClient:
    """获取 Prometheus 客户端单例."""
    return PrometheusClient()
