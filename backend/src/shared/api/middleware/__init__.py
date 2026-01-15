"""Shared API middleware."""

from .auth import AuthenticationMiddleware, CurrentUser

__all__ = ["AuthenticationMiddleware", "CurrentUser"]
