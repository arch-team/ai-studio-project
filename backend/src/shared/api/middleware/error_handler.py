"""统一错误处理中间件 - 捕获所有未处理异常，返回 RFC 7807 Problem Details 格式响应。

整合已有的 exception_handlers.py 和 Problem 装饰器，提供全局兜底异常处理。
在中间件层统一记录错误日志（structlog），确保所有异常都有标准化响应。
"""

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from src.shared.domain.exceptions import DomainError
from src.shared.domain.problem import Problem
from src.shared.infrastructure.security.exceptions import SecurityError

logger = structlog.get_logger(__name__)


def _get_trace_id(request: Request) -> str | None:
    """从请求中提取 trace_id。"""
    return getattr(request.state, "trace_id", None)


def _build_error_body(
    code: str,
    message: str,
    details: dict | None = None,
    trace_id: str | None = None,
) -> dict:
    """构建统一的错误响应体。"""
    error: dict = {
        "code": code,
        "message": message,
    }
    if details:
        error["details"] = details
    if trace_id:
        error["trace_id"] = trace_id
    return {"error": error}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件。

    职责:
    - 捕获所有未被 FastAPI exception_handler 处理的异常
    - 对 Problem / DomainError / SecurityError 返回对应 HTTP 状态码
    - 对未知异常返回 500 并隐藏内部错误信息
    - 使用 structlog 记录错误日志（包含 trace_id、请求路径等上下文）
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """处理请求，捕获异常并返回标准化错误响应。"""
        try:
            return await call_next(request)
        except Problem as exc:
            return self._handle_problem(request, exc)
        except DomainError as exc:
            return self._handle_domain_error(request, exc)
        except SecurityError as exc:
            return self._handle_security_error(request, exc)
        except Exception as exc:
            return self._handle_unexpected_error(request, exc)

    def _handle_problem(self, request: Request, exc: Problem) -> JSONResponse:
        """处理 Problem 类异常。"""
        trace_id = _get_trace_id(request)
        logger.warning(
            "problem_exception",
            error_code=exc.error_code,
            http_status=exc.http_status,
            message=exc.message,
            trace_id=trace_id,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=_build_error_body(
                code=exc.error_code,
                message=exc.message,
                details=exc.get_details(),
                trace_id=trace_id,
            ),
        )

    def _handle_domain_error(self, request: Request, exc: DomainError) -> JSONResponse:
        """处理 DomainError 类异常（兼容旧异常体系）。"""
        trace_id = _get_trace_id(request)
        logger.warning(
            "domain_exception",
            error_code=exc.error_code,
            http_status=exc.http_status,
            message=exc.message,
            trace_id=trace_id,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=_build_error_body(
                code=exc.error_code,
                message=exc.message,
                details=exc.get_details(),
                trace_id=trace_id,
            ),
        )

    def _handle_security_error(self, request: Request, exc: SecurityError) -> JSONResponse:
        """处理 SecurityError 类异常。"""
        trace_id = _get_trace_id(request)
        logger.warning(
            "security_exception",
            error_code=exc.error_code,
            http_status=exc.http_status,
            message=exc.message,
            trace_id=trace_id,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=_build_error_body(
                code=exc.error_code,
                message=exc.message,
                details=exc.get_details(),
                trace_id=trace_id,
            ),
        )

    def _handle_unexpected_error(self, request: Request, exc: Exception) -> JSONResponse:
        """处理未预期的异常，返回 500 并记录完整错误日志。"""
        trace_id = _get_trace_id(request)
        logger.error(
            "unhandled_exception",
            exc_info=exc,
            trace_id=trace_id,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content=_build_error_body(
                code="INTERNAL_SERVER_ERROR",
                message="Internal server error",
                trace_id=trace_id,
            ),
        )
