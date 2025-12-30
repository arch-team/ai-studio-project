"""请求/响应日志中间件

记录所有API请求和响应的详细信息
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件

    记录每个请求的详细信息:
    - 请求ID
    - 请求方法和路径
    - 客户端IP
    - 响应状态码
    - 处理时间
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: 响应对象
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"

        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url.path} "
            f"[request_id={request_id}] [client={client_ip}]"
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            # 记录响应信息
            logger.info(
                f"请求完成: {request.method} {request.url.path} "
                f"[request_id={request_id}] [status={response.status_code}] "
                f"[time={process_time:.3f}s]"
            )

            return response

        except Exception as exc:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录异常
            logger.error(
                f"请求异常: {request.method} {request.url.path} "
                f"[request_id={request_id}] [time={process_time:.3f}s] - {str(exc)}",
                exc_info=True,
            )

            raise


def log_request_body(request: Request) -> None:
    """记录请求体

    Args:
        request: 请求对象
    """
    # 仅在DEBUG级别记录请求体
    if logger.isEnabledFor(logging.DEBUG):
        body = request.body()
        logger.debug(f"请求体: {body}")


__all__ = [
    "RequestLoggingMiddleware",
    "log_request_body",
]
