"""Authentication Middleware - JWT token validation for protected routes."""

import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from src.shared.infrastructure.security.exceptions import InvalidTokenError, TokenExpiredError
from src.shared.infrastructure.security.jwt import TokenPayload, TokenType, get_jwt_manager
from src.shared.infrastructure.security.paths import AUTH_EXEMPT_PATHS, AUTH_EXEMPT_PATTERNS
from src.shared.infrastructure import get_settings

# Development mock token
DEV_MOCK_TOKEN = "dev-mock-token"


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
                    "code": "UNAUTHORIZED",
                    "message": "Authorization header required",
                },
            )

        # Validate token
        payload = self._validate_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "INVALID_TOKEN",
                    "message": "Invalid or expired token",
                },
            )

        # Attach user info to request state
        request.state.user_id = int(payload.sub)
        request.state.username = payload.username
        request.state.email = payload.email
        request.state.role = payload.role
        request.state.token_payload = payload
        # Also set as a dict for CurrentUser.from_request compatibility
        request.state.user = {
            "user_id": int(payload.sub),
            "username": payload.username,
            "email": payload.email,
            "role": payload.role,
        }

        return await call_next(request)

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from authentication."""
        if path in AUTH_EXEMPT_PATHS:
            return True

        return any(re.match(pattern, path) for pattern in AUTH_EXEMPT_PATTERNS)

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
        # Development mode: accept mock token
        settings = get_settings()
        if settings.environment == "development" and token == DEV_MOCK_TOKEN:
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc)
            return TokenPayload(
                sub="1",
                username="dev_user",
                email="dev@example.com",
                role="admin",
                exp=now + timedelta(hours=24),
                iat=now,
                token_type=TokenType.ACCESS,
                jti="dev-mock-jti",
            )

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
    def from_request(cls, request: Request) -> "CurrentUser | None":
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
        from src.modules.auth.application.services import get_rbac_service

        rbac = get_rbac_service()
        return rbac.has_role_level(self.role, role)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        from src.modules.auth.application.services import Permission, get_rbac_service

        rbac = get_rbac_service()
        try:
            perm = Permission(permission)
            return rbac.has_permission(self.role, perm)
        except ValueError:
            return False
