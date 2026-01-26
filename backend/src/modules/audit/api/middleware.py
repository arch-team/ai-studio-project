"""Audit logging middleware for API request tracking."""

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
from src.shared.infrastructure.security.paths import (
    AUDIT_EXEMPT_PATHS,
    AUDIT_EXEMPT_PREFIXES,
)

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic audit logging of API operations."""

    # HTTP method to operation type mapping
    METHOD_OPERATION_MAP: dict[str, OperationType | None] = {
        "POST": OperationType.CREATE,
        "PUT": OperationType.UPDATE,
        "PATCH": OperationType.UPDATE,
        "DELETE": OperationType.DELETE,
        "GET": None,  # Read-only operations not audited
        "HEAD": None,
        "OPTIONS": None,
    }

    # Special path patterns for state transition operations
    STATE_OPERATION_MAP: dict[str, OperationType] = {
        "/pause": OperationType.PAUSE,
        "/resume": OperationType.RESUME,
        "/cancel": OperationType.CANCEL,
    }

    # Path keywords to resource type mapping
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

    # Sensitive fields to sanitize
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

    # Maximum request body size to store (64KB)
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
        """Process request and create audit log entry."""
        # Skip exempt paths
        if self._should_skip(request):
            return await self._safe_call_next(request, call_next)

        # Get operation type - check for state transitions first
        operation_type = self._get_operation_type(request)
        if operation_type is None:
            return await self._safe_call_next(request, call_next)

        # Capture request data before processing
        request_data = await self._capture_request_data(request)

        # Execute the actual request with error handling
        response = await self._safe_call_next(request, call_next)

        # Create audit log asynchronously (non-blocking)
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
        """Check if request should skip audit logging."""
        path = request.url.path
        return path in AUDIT_EXEMPT_PATHS or path.startswith(AUDIT_EXEMPT_PREFIXES)

    def _get_operation_type(self, request: Request) -> OperationType | None:
        """Get operation type based on request method and path.

        State transition operations (pause/resume/cancel) are identified
        by path suffix even though they use POST method.
        """
        path = request.url.path

        # Check for state transition operations first (POST to specific paths)
        if request.method == "POST":
            for suffix, op_type in self.STATE_OPERATION_MAP.items():
                if path.endswith(suffix):
                    return op_type

        # Fall back to HTTP method mapping
        return self.METHOD_OPERATION_MAP.get(request.method)

    async def _capture_request_data(self, request: Request) -> dict[str, Any] | None:
        """Capture and sanitize request body."""
        try:
            # Check content length
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_BODY_SIZE:
                return {"_truncated": True, "_message": "Request body too large"}

            # Read body
            body = await request.body()
            if not body:
                return None

            # Check actual size
            if len(body) > self.MAX_BODY_SIZE:
                return {"_truncated": True, "_message": "Request body too large"}

            # Try to parse as JSON
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                data = json.loads(body.decode("utf-8"))
                result: dict[str, Any] | None = self._sanitize_data(data)
                return result

            return None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        except Exception as e:
            logger.warning("capture_request_data_failed", path=request.url.path, error=str(e))
            return None

    def _sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize sensitive fields in data."""
        if isinstance(data, dict):
            return {
                key: ("***" if key.lower() in self.SENSITIVE_FIELDS else self._sanitize_data(value))
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        return data

    def _get_resource_type(self, path: str) -> ResourceType | None:
        """Extract resource type from request path."""
        path_lower = path.lower()
        for keyword, resource_type in self.PATH_RESOURCE_MAP.items():
            if keyword in path_lower:
                return resource_type
        return None

    def _get_resource_id(self, path: str) -> str | None:
        """Extract resource ID from request path."""
        # Match patterns like /api/v1/training-jobs/{id}
        pattern = r"/api/v\d+/[\w-]+/([^/]+)(?:/.*)?$"
        match = re.search(pattern, path)
        if match:
            return match.group(1)
        return None

    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP address."""
        # Check X-Forwarded-For header first (for reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client
        if request.client:
            return request.client.host
        return None

    def _get_user_id(self, request: Request) -> int | None:
        """Extract user ID from request state (set by auth middleware)."""
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
        """Write audit log to database asynchronously."""
        try:
            # Determine audit status based on response code
            status = AuditStatus.SUCCESS if response.status_code < 400 else AuditStatus.FAILED

            # Build response data
            response_data = {"status_code": response.status_code}

            # Create audit log entity
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

            # Get repository from app state and persist
            if hasattr(request.app.state, "audit_repository"):
                await request.app.state.audit_repository.create(audit_log)
            else:
                logger.debug("audit_repository_not_configured")

        except Exception as e:
            # Log error but don't fail the request (audit should never block main flow)
            logger.exception(
                "audit_log_write_failed",
                operation_type=operation_type.value if operation_type else None,
                path=request.url.path,
                error=str(e),
            )
