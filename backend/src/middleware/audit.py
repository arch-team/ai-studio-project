"""Audit Logging Middleware.

Task: T016b - 审计日志中间件
拦截所有 API 请求,自动记录操作日志 (user_id, operation_type, resource_type, 
request/response data),异步写入数据库,确保审计完整性
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# Resource type mapping based on URL patterns
RESOURCE_PATTERNS = [
    (r"/api/v1/training-jobs/?(\w+)?", "training_job"),
    (r"/api/v1/datasets/?(\w+)?", "dataset"),
    (r"/api/v1/models/?(\w+)?", "model"),
    (r"/api/v1/checkpoints/?(\w+)?", "checkpoint"),
    (r"/api/v1/spaces/?(\w+)?", "space"),
    (r"/api/v1/users/?(\w+)?", "user"),
    (r"/api/v1/quotas/?(\w+)?", "quota"),
    (r"/api/v1/auth/", "user"),  # Auth operations affect users
]

# HTTP method to operation type mapping
METHOD_OPERATION_MAP = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
    "GET": None,  # Don't audit GET requests by default
}

# Paths to exclude from auditing
EXCLUDED_PATHS = [
    "/health",
    "/ready",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/favicon.ico",
]


class AuditLogEntry:
    """Represents a single audit log entry."""

    def __init__(
        self,
        user_id: Optional[int],
        operation_type: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        request_data: Optional[dict] = None,
        response_data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        self.user_id = user_id
        self.operation_type = operation_type
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.request_data = request_data
        self.response_data = response_data
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = status
        self.error_message = error_message
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic audit logging of API operations."""

    def __init__(
        self,
        app: ASGIApp,
        audit_handler: Optional[Callable[[AuditLogEntry], None]] = None,
        exclude_paths: Optional[list[str]] = None,
        max_body_size: int = 10000,  # Max bytes to log from request/response body
    ):
        """Initialize audit middleware.

        Args:
            app: ASGI application
            audit_handler: Async function to handle audit log entries
            exclude_paths: Additional paths to exclude from auditing
            max_body_size: Maximum body size to include in audit logs
        """
        super().__init__(app)
        self.audit_handler = audit_handler or self._default_handler
        self.exclude_paths = set(EXCLUDED_PATHS + (exclude_paths or []))
        self.max_body_size = max_body_size

    def _default_handler(self, entry: AuditLogEntry) -> None:
        """Default audit handler - logs to standard logger."""
        logger.info(
            f"AUDIT: {entry.operation_type} {entry.resource_type} "
            f"by user {entry.user_id} - {entry.status}",
            extra=entry.to_dict(),
        )

    def _should_audit(self, request: Request) -> bool:
        """Determine if request should be audited.

        Args:
            request: FastAPI request object

        Returns:
            True if request should be audited
        """
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return False

        for excluded in self.exclude_paths:
            if request.url.path.startswith(excluded):
                return False

        # Skip GET requests (read operations) by default
        if request.method == "GET":
            return False

        return True

    def _extract_resource_info(self, path: str) -> tuple[str, Optional[str]]:
        """Extract resource type and ID from URL path.

        Args:
            path: URL path

        Returns:
            Tuple of (resource_type, resource_id)
        """
        for pattern, resource_type in RESOURCE_PATTERNS:
            match = re.match(pattern, path)
            if match:
                resource_id = match.group(1) if match.lastindex else None
                return resource_type, resource_id

        return "unknown", None

    def _get_operation_type(self, method: str, path: str) -> str:
        """Determine operation type from HTTP method and path.

        Args:
            method: HTTP method
            path: URL path

        Returns:
            Operation type string
        """
        # Special case for login/logout
        if "/auth/login" in path:
            return "login"
        if "/auth/logout" in path:
            return "logout"

        return METHOD_OPERATION_MAP.get(method, "unknown")

    def _sanitize_body(self, body: bytes, content_type: Optional[str]) -> Optional[dict]:
        """Sanitize and parse request/response body.

        Args:
            body: Raw body bytes
            content_type: Content-Type header value

        Returns:
            Sanitized body dict or None
        """
        if not body or len(body) > self.max_body_size:
            return None

        if not content_type or "application/json" not in content_type:
            return None

        try:
            data = json.loads(body.decode("utf-8"))

            # Remove sensitive fields
            sensitive_fields = [
                "password",
                "current_password",
                "new_password",
                "token",
                "access_token",
                "refresh_token",
                "secret",
                "api_key",
                "authorization",
            ]

            if isinstance(data, dict):
                return {
                    k: "***REDACTED***" if k.lower() in sensitive_fields else v
                    for k, v in data.items()
                }

            return data
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _get_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from request state.

        Args:
            request: FastAPI request object

        Returns:
            User ID or None
        """
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, "user") and request.state.user:
            return getattr(request.state.user, "id", None)

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and create audit log entry.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler

        Returns:
            Response object
        """
        # Check if should audit
        if not self._should_audit(request):
            return await call_next(request)

        # Extract request info before processing
        resource_type, resource_id = self._extract_resource_info(request.url.path)
        operation_type = self._get_operation_type(request.method, request.url.path)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:512]

        # Read request body (only for non-GET requests)
        request_body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                request_body = self._sanitize_body(
                    body_bytes, request.headers.get("content-type")
                )
            except Exception:
                pass

        # Process request
        response = await call_next(request)

        # Get user ID after auth middleware has run
        user_id = self._get_user_id(request)

        # Determine status
        status = "success" if response.status_code < 400 else "failed"
        error_message = None if status == "success" else f"HTTP {response.status_code}"

        # Create audit entry
        entry = AuditLogEntry(
            user_id=user_id,
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            request_data=request_body,
            response_data=None,  # Don't log response body by default
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )

        # Call audit handler (async in background)
        try:
            self.audit_handler(entry)
        except Exception as e:
            logger.error(f"Failed to process audit log: {e}")

        return response


async def create_db_audit_handler():
    """Create audit handler that writes to database.

    Returns:
        Async function that creates AuditLog records
    """
    # This will be implemented when database session is available
    # from sqlalchemy.ext.asyncio import AsyncSession
    # from src.core.database import get_session
    # from src.models.audit_log import AuditLog, AuditOperationType, AuditResourceType, AuditStatus

    async def handler(entry: AuditLogEntry) -> None:
        """Write audit entry to database."""
        # Placeholder - will use actual database in production
        logger.info(
            "audit_log_db",
            user_id=entry.user_id,
            operation=entry.operation_type,
            resource=entry.resource_type,
            resource_id=entry.resource_id,
            status=entry.status,
        )

    return handler
