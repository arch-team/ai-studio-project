"""统一错误处理中间件 - 捕获所有未处理异常，返回 RFC 7807 Problem Details 格式响应。

整合已有的 exception_handlers.py 和 Problem 装饰器，提供全局兜底异常处理。
在中间件层统一记录错误日志（structlog），确保所有异常都有标准化响应。
"""

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from src.shared.domain.problem import Problem

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
    - 对 Problem（含 DomainError / SecurityError 别名）返回对应 HTTP 状态码
    - 对未知异常返回 500 并隐藏内部错误信息
    - 使用 structlog 记录错误日志（包含 trace_id、请求路径等上下文）

    注意: DomainError 和 SecurityError 均为 Problem 的别名，
    无需分别捕获，统一由 except Problem 处理。
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
            return self._handle_known_error(request, exc)
        except Exception as exc:
            return self._handle_unexpected_error(request, exc)

    def _handle_known_error(self, request: Request, exc: Problem) -> JSONResponse:
        """处理 Problem 及其子类异常（含 DomainError / SecurityError）。

        根据 HTTP 状态码区分日志级别: 4xx → info, 5xx → warning。
        通过 type(exc).__name__ 区分日志事件名。
        """
        trace_id = _get_trace_id(request)
        event_name = f"{type(exc).__name__}_exception"
        log_kwargs = {
            "error_code": exc.error_code,
            "http_status": exc.http_status,
            "message": exc.message,
            "trace_id": trace_id,
            "path": request.url.path,
            "method": request.method,
        }

        # 4xx 客户端错误用 info，5xx 服务端错误用 warning
        if exc.http_status >= 500:
            logger.warning(event_name, **log_kwargs)
        else:
            logger.info(event_name, **log_kwargs)

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
