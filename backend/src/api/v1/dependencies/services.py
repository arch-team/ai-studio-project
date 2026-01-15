"""Service dependencies for FastAPI endpoints."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.account_service import AccountService
from src.application.services.auth_service import AuthService
from src.application.services.checkpoint_service import CheckpointService
from src.application.services.password_service import PasswordService
from src.core.database import get_db
from src.infrastructure.persistence.repositories import (
    CheckpointRepository,
    LoginAttemptRepository,
    PasswordHistoryRepository,
    UserRepository,
)


async def get_auth_service(
    session: AsyncSession = Depends(get_db),
) -> AuthService:
    """Get AuthService instance with repository dependencies."""
    user_repo = UserRepository(session)
    login_attempt_repo = LoginAttemptRepository(session)
    return AuthService(
        user_repository=user_repo,
        login_attempt_repository=login_attempt_repo,
    )


async def get_password_service(
    session: AsyncSession = Depends(get_db),
) -> PasswordService:
    """Get PasswordService instance with repository dependencies."""
    user_repo = UserRepository(session)
    password_history_repo = PasswordHistoryRepository(session)
    return PasswordService(
        user_repository=user_repo,
        password_history_repository=password_history_repo,
    )


async def get_account_service(
    session: AsyncSession = Depends(get_db),
) -> AccountService:
    """Get AccountService instance with repository dependencies."""
    user_repo = UserRepository(session)
    password_history_repo = PasswordHistoryRepository(session)
    return AccountService(
        user_repository=user_repo,
        password_history_repository=password_history_repo,
    )


async def get_checkpoint_service(
    session: AsyncSession = Depends(get_db),
) -> CheckpointService:
    """Get CheckpointService instance with repository dependencies."""
    checkpoint_repo = CheckpointRepository(session)
    return CheckpointService(checkpoint_repository=checkpoint_repo)
