"""Authentication Dependencies - FastAPI dependency injection for auth."""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from src.api.middleware.auth import CurrentUser
from src.application.services.rbac_service import Permission, get_rbac_service


def get_current_user(request: Request) -> Optional[CurrentUser]:
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
def require_user_management():
    """Require user management permission."""
    return RequirePermission(Permission.USER_CREATE)


def require_audit_view():
    """Require audit view permission."""
    return RequirePermission(Permission.AUDIT_VIEW)


def require_system_config():
    """Require system configuration permission."""
    return RequirePermission(Permission.SYSTEM_CONFIG)
