"""Authentication Middleware - JWT token validation for protected routes."""

import re
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from src.core.security.exceptions import InvalidTokenError, TokenExpiredError
from src.core.security.jwt import TokenPayload, TokenType, get_jwt_manager

# Paths that don't require authentication
EXEMPT_PATHS: list[str] = [
    "/health",
    "/healthz",
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/token/refresh",
    "/api/v1/auth/password-reset/request",
    "/api/v1/auth/password-reset/confirm",
]

# Regex patterns for exempt paths
EXEMPT_PATTERNS: list[str] = [
    r"^/api/v1/auth/password-reset/.*$",
]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication on protected routes."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request and validate JWT token."""
        # Skip authentication for exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # Extract token from Authorization header
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "UNAUTHORIZED",
                    "message": "Authorization header required",
                },
            )

        # Validate token
        payload = self._validate_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "INVALID_TOKEN",
                    "message": "Invalid or expired token",
                },
            )

        # Attach user info to request state
        request.state.user_id = int(payload.sub)
        request.state.username = payload.username
        request.state.email = payload.email
        request.state.role = payload.role
        request.state.token_payload = payload

        return await call_next(request)

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from authentication."""
        if path in EXEMPT_PATHS:
            return True

        return any(re.match(pattern, path) for pattern in EXEMPT_PATTERNS)

    def _extract_token(self, request: Request) -> str | None:
        """Extract Bearer token from Authorization header."""
        if not (auth_header := request.headers.get("Authorization")):
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def _validate_token(self, token: str) -> TokenPayload | None:
        """Validate JWT token and return payload."""
        try:
            jwt_manager = get_jwt_manager()
            return jwt_manager.verify_token(token, TokenType.ACCESS)
        except (InvalidTokenError, TokenExpiredError):
            return None


class CurrentUser:
    """Helper class to represent the current authenticated user."""

    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        role: str,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role

    @classmethod
    def from_request(cls, request: Request) -> Optional["CurrentUser"]:
        """Create CurrentUser from request state."""
        if not hasattr(request.state, "user_id"):
            return None

        return cls(
            user_id=request.state.user_id,
            username=request.state.username,
            email=request.state.email,
            role=request.state.role,
        )

    def has_role(self, role: str) -> bool:
        """Check if user has at least the specified role level."""
        from src.application.services.rbac_service import get_rbac_service

        rbac = get_rbac_service()
        return rbac.has_role_level(self.role, role)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        from src.application.services.rbac_service import Permission, get_rbac_service

        rbac = get_rbac_service()
        try:
            perm = Permission(permission)
            return rbac.has_permission(self.role, perm)
        except ValueError:
            return False
