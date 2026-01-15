"""Service dependencies for FastAPI endpoints."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.account_service import AccountService
from src.application.services.auth_service import AuthService
from src.application.services.password_service import PasswordService
from src.core.database import get_db


async def get_auth_service(
    session: AsyncSession = Depends(get_db),
) -> AuthService:
    """Get AuthService instance."""
    return AuthService(session)


async def get_password_service(
    session: AsyncSession = Depends(get_db),
) -> PasswordService:
    """Get PasswordService instance."""
    return PasswordService(session)


async def get_account_service(
    session: AsyncSession = Depends(get_db),
) -> AccountService:
    """Get AccountService instance."""
    return AccountService(session)
