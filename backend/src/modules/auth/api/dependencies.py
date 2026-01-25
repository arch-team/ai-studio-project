"""Auth API dependencies - FastAPI dependency injection."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db

from ..application.services import (
    AccountService,
    AuthService,
    PasswordService,
    UserService,
    get_rbac_service,
)
from ..domain.repositories import (
    ILoginAttemptRepository,
    IPasswordHistoryRepository,
    IUserRepository,
)
from ..domain.value_objects import Permission
from ..infrastructure.repositories import (
    LoginAttemptRepositoryImpl,
    PasswordHistoryRepositoryImpl,
    UserRepositoryImpl,
)
from .current_user import CurrentUser


# Repository dependencies
async def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> IUserRepository:
    """Get user repository instance."""
    return UserRepositoryImpl(session)


async def get_login_attempt_repository(
    session: AsyncSession = Depends(get_db),
) -> ILoginAttemptRepository:
    """Get login attempt repository instance."""
    return LoginAttemptRepositoryImpl(session)


async def get_password_history_repository(
    session: AsyncSession = Depends(get_db),
) -> IPasswordHistoryRepository:
    """Get password history repository instance."""
    return PasswordHistoryRepositoryImpl(session)


# Service dependencies
async def get_auth_service(
    user_repo: IUserRepository = Depends(get_user_repository),
    attempt_repo: ILoginAttemptRepository = Depends(get_login_attempt_repository),
) -> AuthService:
    """Get auth service instance."""
    return AuthService(user_repo, attempt_repo)


async def get_password_service(
    user_repo: IUserRepository = Depends(get_user_repository),
    history_repo: IPasswordHistoryRepository = Depends(get_password_history_repository),
) -> PasswordService:
    """Get password service instance."""
    return PasswordService(user_repo, history_repo)


async def get_account_service(
    user_repo: IUserRepository = Depends(get_user_repository),
    history_repo: IPasswordHistoryRepository = Depends(get_password_history_repository),
) -> AccountService:
    """Get account service instance."""
    return AccountService(user_repo, history_repo)


async def get_user_service(
    user_repo: IUserRepository = Depends(get_user_repository),
) -> UserService:
    """Get user service instance."""
    return UserService(user_repo)


# User authentication dependencies
def get_current_user(request: Request) -> CurrentUser | None:
    """Get current user from request (optional)."""
    return CurrentUser.from_request(request)


def get_current_active_user(request: Request) -> CurrentUser:
    """Get current active user from request (required)."""
    if user := CurrentUser.from_request(request):
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Permission dependencies
class RequirePermission:
    """Dependency to require a specific permission."""

    def __init__(self, permission: Permission):
        self.permission = permission

    def __call__(
        self,
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        """Check if user has the required permission."""
        rbac = get_rbac_service()
        if not rbac.has_permission(current_user.role, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires {self.permission.value}",
            )
        return current_user


class RequireRole:
    """Dependency to require a minimum role level."""

    def __init__(self, role: str):
        self.role = role

    def __call__(
        self,
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        """Check if user has at least the required role level."""
        rbac = get_rbac_service()
        if not rbac.has_role_level(current_user.role, self.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires role {self.role} or higher",
            )
        return current_user


def require_permission(permission: Permission):
    """Factory function for permission dependency."""
    return RequirePermission(permission)


def require_role(role: str):
    """Factory function for role dependency."""
    return RequireRole(role)


# Common role dependencies
require_admin = RequireRole("admin")
require_project_manager = RequireRole("project_manager")
require_engineer = RequireRole("engineer")


# Common permission dependencies
require_user_management = RequirePermission(Permission.USER_CREATE)
require_audit_view = RequirePermission(Permission.AUDIT_VIEW)
require_system_config = RequirePermission(Permission.SYSTEM_CONFIG)
