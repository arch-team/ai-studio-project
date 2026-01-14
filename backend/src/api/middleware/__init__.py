"""API Middleware - Request/response processing.

Middleware components:
- Authentication: JWT token validation
- SSO: AWS IAM Identity Center integration
- Logging: Request/response logging
- Error handling: Exception to HTTP response mapping
- CORS: Cross-origin resource sharing
- Rate limiting: Request throttling
"""

from src.api.middleware.auth import AuthenticationMiddleware, CurrentUser
from src.api.middleware.sso import (
    SSOHealthTracker,
    SSOService,
    SSOUserInfo,
    configure_sso_service,
    get_sso_service,
    map_groups_to_role,
)

__all__ = [
    # Authentication
    "AuthenticationMiddleware",
    "CurrentUser",
    # SSO
    "SSOService",
    "SSOHealthTracker",
    "SSOUserInfo",
    "get_sso_service",
    "configure_sso_service",
    "map_groups_to_role",
]
