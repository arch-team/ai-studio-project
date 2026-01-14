"""Service dependencies for FastAPI endpoints."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.auth_service import AuthService
from src.core.database import get_db


async def get_auth_service(
    session: AsyncSession = Depends(get_db),
) -> AuthService:
    """Get AuthService instance."""
    return AuthService(session)
