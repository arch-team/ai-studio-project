"""审计日志中间件 - API 请求追踪."""

import asyncio
import json
import re
from collections.abc import Callable
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.modules.audit.domain.entities import AuditLog
from src.modules.audit.domain.value_objects import (
    AuditStatus,
    OperationType,
    ResourceType,
)
from src.modules.audit.infrastructure.repositories import AuditLogRepositoryImpl
from src.shared.infrastructure.security.paths import (
    AUDIT_EXEMPT_PATHS,
    AUDIT_EXEMPT_PREFIXES,
)

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """API 操作自动审计日志中间件."""

    # HTTP 方法 → 操作类型映射
    METHOD_OPERATION_MAP: dict[str, OperationType | None] = {
        "POST": OperationType.CREATE,
        "PUT": OperationType.UPDATE,
        "PATCH": OperationType.UPDATE,
        "DELETE": OperationType.DELETE,
        "GET": None,  # 只读操作不记录审计
        "HEAD": None,
        "OPTIONS": None,
    }

    # 状态转换操作的路径后缀映射
    STATE_OPERATION_MAP: dict[str, OperationType] = {
        "/pause": OperationType.PAUSE,
        "/resume": OperationType.RESUME,
        "/cancel": OperationType.CANCEL,
    }

    # 路径关键字 → 资源类型映射
    PATH_RESOURCE_MAP: dict[str, ResourceType] = {
        "training-jobs": ResourceType.TRAINING_JOB,
        "datasets": ResourceType.DATASET,
        "models": ResourceType.MODEL,
        "users": ResourceType.USER,
        "resource-quotas": ResourceType.QUOTA,
        "quotas": ResourceType.QUOTA,
        "ide": ResourceType.SPACE,
        "spaces": ResourceType.SPACE,
        "auth": ResourceType.USER,
    }

    # 需脱敏的敏感字段
    SENSITIVE_FIELDS: set[str] = {
        "password",
        "token",
        "secret",
        "api_key",
        "access_token",
        "refresh_token",
        "authorization",
        "credential",
        "private_key",
    }

    # 最大请求体存储大小 (64KB)
    MAX_BODY_SIZE: int = 65536

    async def _safe_call_next(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """调用下一个中间件并安全处理异常。

        将未捕获的异常转换为 500 响应，避免中间件链中断。
        """
        try:
            response: Response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(
                "unhandled_exception",
                method=request.method,
                path=request.url.path,
                error=str(e),
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """处理请求并创建审计日志."""
        # 跳过免审计路径
        if self._should_skip(request):
            return await self._safe_call_next(request, call_next)

        # 获取操作类型（优先检查状态转换路径）
        operation_type = self._get_operation_type(request)
        if operation_type is None:
            return await self._safe_call_next(request, call_next)

        # 捕获请求数据
        request_data = await self._capture_request_data(request)

        # 执行实际请求
        response = await self._safe_call_next(request, call_next)

        # 异步写入审计日志（不阻塞主流程）
        asyncio.create_task(
            self._write_audit_log(
                request=request,
                response=response,
                operation_type=operation_type,
                request_data=request_data,
            )
        )

        return response

    def _should_skip(self, request: Request) -> bool:
        """检查请求是否应跳过审计."""
        path = request.url.path
        return path in AUDIT_EXEMPT_PATHS or path.startswith(AUDIT_EXEMPT_PREFIXES)

    def _get_operation_type(self, request: Request) -> OperationType | None:
        """根据请求方法和路径确定操作类型.

        状态转换操作 (pause/resume/cancel) 通过路径后缀识别，
        即使 HTTP 方法是 POST。
        """
        path = request.url.path

        # 优先检查状态转换操作（POST 到特定路径后缀）
        if request.method == "POST":
            for suffix, op_type in self.STATE_OPERATION_MAP.items():
                if path.endswith(suffix):
                    return op_type

        # 回退到 HTTP 方法映射
        return self.METHOD_OPERATION_MAP.get(request.method)

    async def _capture_request_data(self, request: Request) -> dict[str, Any] | None:
        """捕获并脱敏请求体."""
        _TRUNCATED = {"_truncated": True, "_message": "Request body too large"}

        try:
            # 通过 Content-Length 头预检大小
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_BODY_SIZE:
                return _TRUNCATED

            body = await request.body()
            if not body or len(body) > self.MAX_BODY_SIZE:
                return _TRUNCATED if body else None

            # 仅解析 JSON 请求体
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                data = json.loads(body.decode("utf-8"))
                return self._sanitize_data(data)

            return None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        except Exception as e:
            logger.warning("capture_request_data_failed", path=request.url.path, error=str(e))
            return None

    def _sanitize_data(self, data: Any) -> Any:
        """递归脱敏数据中的敏感字段."""
        if isinstance(data, dict):
            return {
                key: ("***" if key.lower() in self.SENSITIVE_FIELDS else self._sanitize_data(value))
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        return data

    def _get_resource_type(self, path: str) -> ResourceType | None:
        """从请求路径中提取资源类型."""
        path_lower = path.lower()
        for keyword, resource_type in self.PATH_RESOURCE_MAP.items():
            if keyword in path_lower:
                return resource_type
        return None

    def _get_resource_id(self, path: str) -> str | None:
        """从请求路径中提取资源 ID."""
        # 匹配 /api/v1/training-jobs/{id} 模式
        pattern = r"/api/v\d+/[\w-]+/([^/]+)(?:/.*)?$"
        match = re.search(pattern, path)
        if match:
            return match.group(1)
        return None

    def _get_client_ip(self, request: Request) -> str | None:
        """提取客户端 IP 地址."""
        # 优先从反向代理头获取
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # 直连客户端
        if request.client:
            return request.client.host
        return None

    def _get_user_id(self, request: Request) -> int | None:
        """从请求状态中提取用户 ID（由认证中间件设置）."""
        if hasattr(request.state, "user_id"):
            user_id: int | None = request.state.user_id
            return user_id
        return None

    async def _write_audit_log(
        self,
        request: Request,
        response: Response,
        operation_type: OperationType,
        request_data: dict[str, Any] | None,
    ) -> None:
        """异步写入审计日志到数据库."""
        try:
            status = AuditStatus.SUCCESS if response.status_code < 400 else AuditStatus.FAILED
            response_data = {"status_code": response.status_code}
            audit_log = AuditLog(
                id=0,  # Will be assigned by database
                operation_type=operation_type,
                resource_type=self._get_resource_type(request.url.path) or ResourceType.USER,
                status=status,
                user_id=self._get_user_id(request),
                resource_id=self._get_resource_id(request.url.path),
                request_data=request_data,
                response_data=response_data,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )

            # 持久化审计日志
            # 优先使用注入的 repository（测试用），否则使用 session factory（生产用）
            if hasattr(request.app.state, "audit_repository"):
                await request.app.state.audit_repository.create(audit_log)
            elif hasattr(request.app.state, "audit_session_factory"):
                async with request.app.state.audit_session_factory() as session:
                    repo = AuditLogRepositoryImpl(session)
                    await repo.create(audit_log)
                    await session.commit()
            else:
                logger.debug("audit_repository_not_configured")

        except Exception as e:
            # 记录错误但不阻塞主流程（审计不应影响业务请求）
            logger.exception(
                "audit_log_write_failed",
                operation_type=operation_type.value if operation_type else None,
                path=request.url.path,
                error=str(e),
            )
