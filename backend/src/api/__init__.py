"""API Routes.

This module provides FastAPI routers for the AI Training Platform API.
"""

from src.api.auth import router as auth_router

__all__ = [
    "auth_router",
]
