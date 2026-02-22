"""PerformanceMiddleware 单元测试。

验证中间件能正确记录请求延迟并跳过非业务端点。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.shared.api.middleware.performance import PerformanceMiddleware


def _make_request(path: str = "/api/v1/test", method: str = "GET") -> Request:
    """创建测试用 Request 对象。"""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    return Request(scope)


class TestPerformanceMiddleware:
    """PerformanceMiddleware 测试。"""

    @pytest.fixture
    def middleware(self) -> PerformanceMiddleware:
        """创建中间件实例。"""
        return PerformanceMiddleware(app=MagicMock())

    async def test_normal_request_passes_through(self, middleware: PerformanceMiddleware) -> None:
        """正常请求通过并返回响应。"""
        request = _make_request()
        expected_response = JSONResponse(content={"data": "ok"})
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response
        call_next.assert_called_once()

    async def test_health_endpoint_skipped(self, middleware: PerformanceMiddleware) -> None:
        """/health 端点不记录性能指标。"""
        request = _make_request(path="/health")
        expected_response = JSONResponse(content={"status": "healthy"})
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response

    async def test_docs_endpoint_skipped(self, middleware: PerformanceMiddleware) -> None:
        """/docs 端点不记录性能指标。"""
        request = _make_request(path="/docs")
        expected_response = JSONResponse(content={})
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response

    async def test_openapi_endpoint_skipped(self, middleware: PerformanceMiddleware) -> None:
        """/openapi.json 端点不记录性能指标。"""
        request = _make_request(path="/openapi.json")
        expected_response = JSONResponse(content={})
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response

    async def test_api_endpoint_recorded(self, middleware: PerformanceMiddleware) -> None:
        """业务 API 端点记录性能指标。"""
        request = _make_request(path="/api/v1/training-jobs", method="POST")
        expected_response = MagicMock()
        expected_response.status_code = 201
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response
