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


@pytest.fixture
def captured_signed_url(monkeypatch):
    """捕获传入 _sign_headers 的 URL（即 SigV4 签名实际作用的 URL）。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    captured: dict = {}
    original = PrometheusClient._sign_headers

    def spy_sign_headers(self, method, url):
        captured["signed_url"] = url
        return original(self, method, url)

    monkeypatch.setattr(PrometheusClient, "_sign_headers", spy_sign_headers)
    return captured


# 含空格、括号、引号、花括号——即时查询表达式的典型特殊字符
SPECIAL_INSTANT_QUERY = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'


@pytest.mark.asyncio
async def test_instant_query_signed_url_matches_sent_url(captured_request, captured_signed_url, fake_credentials):
    """含特殊字符的即时查询：SigV4 签名作用的 URL 必须与 httpx 实际发送的 URL 完全一致。

    这是 403 根因的回归保护：httpx 默认把空格 form-encode 为 `+`，而 AWS SigV4
    canonical 要求 `%20`。若签名 URL 与发送 URL 编码不一致（如签名用 `%20`、发送用 `+`，
    或反之），AMP 服务端重建的 canonical 与签名 canonical 不匹配 → 403 Forbidden。
    """
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    client = PrometheusClient(
        endpoint="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-x",
        use_sigv4=True,
    )
    await client.query_instant(SPECIAL_INSTANT_QUERY)

    signed_url = captured_signed_url["signed_url"]
    sent_url = captured_request["url"]

    # 1) 签名 URL 与发送 URL 字节级一致（核心断言）
    assert signed_url == sent_url, (
        f"签名 URL 与发送 URL 不一致，将导致 SigV4 签名 mismatch:\n" f"  signed={signed_url}\n  sent  ={sent_url}"
    )
    # 2) 空格编码为 %20（AWS 兼容），且未出现 httpx 风格的 `+` 编码
    assert "%20" in sent_url
    assert "+" not in sent_url.split("?", 1)[1], "query string 不应出现 httpx form-encode 的 `+`（空格）"
    # 3) 发送 URL 不再附带额外 params（已全部编码进 URL，避免 httpx 二次编码）
    assert captured_request["params"] == {}


@pytest.mark.asyncio
async def test_range_query_signed_url_matches_sent_url(captured_request, captured_signed_url, fake_credentials):
    """范围查询（多参数）：签名 URL 同样必须与发送 URL 完全一致。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    client = PrometheusClient(
        endpoint="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-x",
        use_sigv4=True,
    )
    await client.query_range(
        "DCGM_FI_DEV_GPU_UTIL",
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert captured_signed_url["signed_url"] == captured_request["url"]
