"""Tracing Middleware - Request tracing with trace_id for error correlation."""

import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for adding trace_id to requests for error correlation.

    trace_id 来源优先级:
    1. 请求头 X-Request-ID (由上游服务或负载均衡器设置)
    2. 自动生成 8 字符短 UUID

    trace_id 将被添加到:
    - request.state.trace_id (供异常处理器使用)
    - 响应头 X-Request-ID (供前端日志关联)
    - structlog contextvars (供所有日志自动携带)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request and add trace_id."""
        # 从请求头获取或生成 trace_id
        trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]

        # 添加到请求状态供异常处理器使用
        request.state.trace_id = trace_id

        # 绑定到 structlog contextvars，后续所有日志自动携带
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            request_id=trace_id,
        )

        # 执行请求
        response = await call_next(request)

        # 添加到响应头
        response.headers["X-Request-ID"] = trace_id

        return response
