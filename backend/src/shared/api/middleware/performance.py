"""性能监控中间件 - 记录 API 请求延迟和状态码，上报 CloudWatch Metrics。

通过 FastAPI middleware 自动采集每个请求的延迟和状态码，
使用 structlog 记录性能日志，并通过 CloudWatch client 上报指标。
"""

import time

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = structlog.get_logger(__name__)

# 告警阈值配置
P95_LATENCY_THRESHOLD_MS = 500.0

# 不需要记录性能指标的路径
_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"})


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件。

    职责:
    - 记录每个请求的延迟 (毫秒) 和 HTTP 状态码
    - 通过 structlog 输出性能日志（CloudWatch Logs 可查询）
    - 延迟超过阈值时记录 WARNING 级别日志
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """测量请求处理耗时并记录性能指标。"""
        path = request.url.path

        # 跳过非业务端点
        if path in _SKIP_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.monotonic() - start_time) * 1000
            status_code = response.status_code if response else 500
            method = request.method

            # 记录性能日志（适配 CloudWatch Logs Insights 查询）
            log_data = {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            }

            if duration_ms > P95_LATENCY_THRESHOLD_MS:
                logger.warning("slow_request", **log_data)
            else:
                logger.info("request_completed", **log_data)
