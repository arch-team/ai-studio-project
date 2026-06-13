"""PrometheusClient AMP SigV4 签名支持单元测试 (Task 2B.2)."""

from datetime import UTC, datetime

import pytest


class FakeResponse:
    """模拟 httpx 响应，返回成功的空结果。"""

    def raise_for_status(self): ...

    def json(self):
        return {"status": "success", "data": {"result": []}}


@pytest.fixture
def captured_request(monkeypatch):
    """patch httpx.AsyncClient.get，捕获请求的 headers 与 url。"""
    captured: dict = {}

    async def fake_get(self, url, params=None, headers=None):
        captured["headers"] = headers or {}
        captured["url"] = str(url)
        captured["params"] = params or {}
        return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    return captured


@pytest.fixture
def fake_credentials(monkeypatch):
    """注入假 AWS 凭证。CI/本地无凭证时 get_credentials() 返回 None → SigV4Auth 抛错，故须 mock。"""
    from botocore.credentials import Credentials

    monkeypatch.setattr("boto3.Session.get_credentials", lambda self: Credentials("AKIATEST", "secret"))


@pytest.mark.asyncio
async def test_query_instant_signs_request_with_sigv4(captured_request, fake_credentials):
    """启用 AMP（aps-workspaces 端点）时，即时查询应携带 SigV4 Authorization 头。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    client = PrometheusClient(
        endpoint="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-x",
        use_sigv4=True,
    )
    await client.query_instant("up")

    assert "Authorization" in captured_request["headers"]
    assert "AWS4-HMAC-SHA256" in captured_request["headers"]["Authorization"]


@pytest.mark.asyncio
async def test_query_range_signs_request_with_sigv4(captured_request, fake_credentials):
    """启用 AMP（aps-workspaces 端点）时，范围查询同样应携带 SigV4 Authorization 头。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    client = PrometheusClient(
        endpoint="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-x",
        use_sigv4=True,
    )
    await client.query_range(
        "up",
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert "Authorization" in captured_request["headers"]
    assert "AWS4-HMAC-SHA256" in captured_request["headers"]["Authorization"]


@pytest.mark.asyncio
async def test_use_sigv4_auto_detected_for_amp_endpoint(captured_request, fake_credentials):
    """不显式传 use_sigv4 时，含 aps-workspaces 的端点应自动启用签名。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    client = PrometheusClient(
        endpoint="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-x",
    )
    await client.query_instant("up")

    assert "Authorization" in captured_request["headers"]
    assert "AWS4-HMAC-SHA256" in captured_request["headers"]["Authorization"]


@pytest.mark.asyncio
async def test_local_endpoint_not_signed(captured_request):
    """本地端点（非 AMP）不签名，保持现有行为。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    client = PrometheusClient(endpoint="http://localhost:9090")  # 非 AMP
    await client.query_instant("up")

    assert "Authorization" not in (captured_request["headers"] or {})
