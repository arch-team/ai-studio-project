"""PrometheusClient AMP SigV4 签名支持单元测试 (Task 2B.2)."""

import pytest


@pytest.mark.asyncio
async def test_query_instant_signs_request_with_sigv4(monkeypatch):
    """启用 AMP（aps-workspaces 端点）时，请求应携带 SigV4 Authorization 头。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    captured = {}

    class FakeResponse:
        def raise_for_status(self): ...
        def json(self):
            return {"status": "success", "data": {"result": []}}

    async def fake_get(self, url, params=None, headers=None):
        captured["headers"] = headers or {}
        captured["url"] = str(url)
        return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    # CI/本地无 AWS 凭证时 get_credentials() 返回 None → SigV4Auth 抛错，必须 mock 假凭证
    from botocore.credentials import Credentials

    monkeypatch.setattr("boto3.Session.get_credentials", lambda self: Credentials("AKIATEST", "secret"))

    client = PrometheusClient(
        endpoint="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-x",
        use_sigv4=True,
    )
    await client.query_instant("up")
    assert "Authorization" in captured["headers"]
    assert "AWS4-HMAC-SHA256" in captured["headers"]["Authorization"]


@pytest.mark.asyncio
async def test_local_endpoint_not_signed(monkeypatch):
    """本地端点（非 AMP）不签名，保持现有行为。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    captured = {}

    class FakeResponse:
        def raise_for_status(self): ...
        def json(self):
            return {"status": "success", "data": {"result": []}}

    async def fake_get(self, url, params=None, headers=None):
        captured["headers"] = headers or {}
        return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    client = PrometheusClient(endpoint="http://localhost:9090")  # 非 AMP
    await client.query_instant("up")
    assert "Authorization" not in (captured["headers"] or {})
