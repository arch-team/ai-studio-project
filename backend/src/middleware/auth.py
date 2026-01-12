"""Authentication middleware for FastAPI.

Task: T013 - 实现基础认证中间件
验证 IAM Identity Center token,提取用户信息,支持本地开发模式
"""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.core.config import get_settings
from src.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """JWT Token payload schema."""

    sub: str  # Subject (user ID or IAM identity ID)
    email: Optional[str] = None
    username: Optional[str] = None
    groups: Optional[list[str]] = None
    role: Optional[str] = None
    exp: Optional[int] = None  # Expiration time


class CurrentUser(BaseModel):
    """Current authenticated user information."""

    id: Optional[int] = None  # Database user ID (if exists)
    iam_identity_id: str  # IAM Identity Center user ID
    username: str
    email: Optional[str] = None
    role: str = "engineer"  # Default role
    groups: list[str] = []
    is_authenticated: bool = True


def decode_token(token: str) -> TokenPayload:
    """Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload with decoded claims

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    settings = get_settings()

    try:
        # In production, use IAM Identity Center's public keys for verification
        # For development, we use a simple secret key
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return TokenPayload(**payload)
    except JWTError as e:
        logger.warning("jwt_decode_error", error=str(e))
        raise AuthenticationError(
            message=f"Invalid token: {e}",
            code="INVALID_TOKEN",
            details={"reason": str(e)},
        ) from e


async def get_current_user_optional(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[CurrentUser]:
    """Get current user from token (optional - returns None if no token).

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials

    Returns:
        CurrentUser if authenticated, None otherwise
    """
    settings = get_settings()

    # Development mode bypass (only when debug is enabled)
    if settings.debug and not credentials:
        # Check for X-Dev-User header for local development
        dev_user = request.headers.get("X-Dev-User")
        if dev_user:
            logger.debug(f"Development mode: using dev user {dev_user}")
            return CurrentUser(
                iam_identity_id=f"dev-{dev_user}",
                username=dev_user,
                email=f"{dev_user}@dev.local",
                role="admin",  # Dev users get admin for testing
                groups=["dev"],
                is_authenticated=True,
            )
        return None

    if not credentials:
        return None

    try:
        token_data = decode_token(credentials.credentials)
        return CurrentUser(
            iam_identity_id=token_data.sub,
            username=token_data.username or token_data.sub,
            email=token_data.email,
            role=token_data.role or "engineer",
            groups=token_data.groups or [],
            is_authenticated=True,
        )
    except AuthenticationError:
        return None


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> CurrentUser:
    """Get current user from token (required - raises exception if not authenticated).

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials

    Returns:
        CurrentUser

    Raises:
        HTTPException: If not authenticated
    """
    user = await get_current_user_optional(request, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Get current active user (verified as active in database).

    Args:
        current_user: Current authenticated user

    Returns:
        CurrentUser if active

    Raises:
        HTTPException: If user is not active
    """
    # TODO: Add database lookup to verify user status
    # For now, all authenticated users are considered active
    return current_user


def require_role(allowed_roles: list[str]):
    """Dependency factory for role-based access control.

    Args:
        allowed_roles: List of allowed role names

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin")
        async def admin_endpoint(
            user: Annotated[CurrentUser, Depends(require_role(["admin"]))]
        ):
            return {"message": "Admin access granted"}
    """

    async def role_checker(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {allowed_roles}",
            )
        return current_user

    return role_checker


# Pre-defined role dependencies for common use cases
RequireAdmin = Depends(require_role(["admin"]))
RequireProjectManager = Depends(require_role(["admin", "project_manager"]))
RequireEngineer = Depends(require_role(["admin", "project_manager", "engineer"]))
RequireViewer = Depends(require_role(["admin", "project_manager", "engineer", "viewer"]))


def create_access_token(
    subject: str,
    username: str,
    email: Optional[str] = None,
    role: str = "engineer",
    groups: Optional[list[str]] = None,
    expires_delta_minutes: Optional[int] = None,
) -> str:
    """Create JWT access token.

    Args:
        subject: Token subject (user ID or IAM identity ID)
        username: Username
        email: User email
        role: User role
        groups: User groups
        expires_delta_minutes: Token expiration time in minutes

    Returns:
        Encoded JWT token string
    """
    import time

    settings = get_settings()

    expire = int(time.time()) + (
        (expires_delta_minutes or settings.access_token_expire_minutes) * 60
    )

    payload = {
        "sub": subject,
        "username": username,
        "email": email,
        "role": role,
        "groups": groups or [],
        "exp": expire,
    }

    return jwt.encode(payload, settings.secret_key, algorithm="HS256")
