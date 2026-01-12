"""Authentication and SSO Middleware.

This module provides authentication middleware for the AI Training Platform.
"""

from src.middleware.auth import (
    AuthenticationError,
    CurrentUser,
    TokenPayload,
    create_access_token,
    decode_token,
    get_current_active_user,
    get_current_user,
    get_current_user_optional,
    require_role,
    RequireAdmin,
    RequireEngineer,
    RequireProjectManager,
    RequireViewer,
)
from src.middleware.sso import (
    get_sso_client,
    map_sso_user_to_role,
    SSOClient,
    SSOConfig,
    SSOTokenResponse,
    SSOUserInfo,
)

__all__ = [
    # Auth middleware
    "AuthenticationError",
    "CurrentUser",
    "TokenPayload",
    "create_access_token",
    "decode_token",
    "get_current_active_user",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "RequireAdmin",
    "RequireEngineer",
    "RequireProjectManager",
    "RequireViewer",
    # SSO
    "get_sso_client",
    "map_sso_user_to_role",
    "SSOClient",
    "SSOConfig",
    "SSOTokenResponse",
    "SSOUserInfo",
]
