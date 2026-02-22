"""ErrorHandlerMiddleware 单元测试。

验证中间件能正确捕获各类异常并返回标准化错误响应。
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.shared.api.middleware.error_handler import ErrorHandlerMiddleware
from src.shared.domain.exceptions import DomainError
from src.shared.domain.problem import Problem, problem
from src.shared.infrastructure.security.exceptions import SecurityError


def _make_request(path: str = "/api/v1/test", method: str = "GET", trace_id: str = "test-123") -> Request:
    """创建测试用 Request 对象。"""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    request = Request(scope)
    request.state.trace_id = trace_id
    return request


@problem(404, "TEST_NOT_FOUND", "Test entity '{entity_id}' not found")
@dataclass
class SampleNotFoundError(Problem):
    """测试用 Problem 异常。"""

    entity_id: str


class TestErrorHandlerMiddleware:
    """ErrorHandlerMiddleware 测试。"""

    @pytest.fixture
    def middleware(self) -> ErrorHandlerMiddleware:
        """创建中间件实例。"""
        return ErrorHandlerMiddleware(app=MagicMock())

    async def test_normal_request_passes_through(self, middleware: ErrorHandlerMiddleware) -> None:
        """正常请求直接通过。"""
        request = _make_request()
        expected_response = JSONResponse(content={"data": "ok"})
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response

    async def test_problem_exception_returns_correct_status(self, middleware: ErrorHandlerMiddleware) -> None:
        """Problem 异常返回正确的 HTTP 状态码和错误体。"""
        request = _make_request()
        call_next = AsyncMock(side_effect=SampleNotFoundError(entity_id="123"))

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

    async def test_unexpected_exception_returns_500(self, middleware: ErrorHandlerMiddleware) -> None:
        """未预期异常返回 500 且不暴露内部信息。"""
        request = _make_request()
        call_next = AsyncMock(side_effect=RuntimeError("数据库连接失败"))

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    async def test_domain_error_returns_correct_status(self, middleware: ErrorHandlerMiddleware) -> None:
        """DomainError 返回正确的 HTTP 状态码。"""
        request = _make_request()
        error = DomainError.__new__(DomainError)
        error.message = "Domain error"
        error.http_status = 422
        error.error_code = "VALIDATION_ERROR"
        error.get_details = lambda: None
        call_next = AsyncMock(side_effect=error)

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    async def test_security_error_returns_correct_status(self, middleware: ErrorHandlerMiddleware) -> None:
        """SecurityError 返回正确的 HTTP 状态码。"""
        request = _make_request()
        error = SecurityError.__new__(SecurityError)
        error.message = "Access denied"
        error.http_status = 403
        error.error_code = "FORBIDDEN"
        error.get_details = lambda: None
        call_next = AsyncMock(side_effect=error)

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
