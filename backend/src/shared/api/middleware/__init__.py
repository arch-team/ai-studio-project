"""Shared API middleware."""

from .auth import AuthenticationMiddleware, CurrentUser
from .error_handler import ErrorHandlerMiddleware
from .performance import PerformanceMiddleware
from .sso import SSOHealthTracker, SSOService, SSOUserInfo, get_sso_health_tracker, get_sso_service, map_groups_to_role
from .tracing import TracingMiddleware

__all__ = [
    "AuthenticationMiddleware",
    "CurrentUser",
    "ErrorHandlerMiddleware",
    "PerformanceMiddleware",
    "SSOHealthTracker",
    "SSOService",
    "SSOUserInfo",
    "TracingMiddleware",
    "get_sso_health_tracker",
    "get_sso_service",
    "map_groups_to_role",
]
