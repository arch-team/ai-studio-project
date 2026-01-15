"""Auth API layer exports."""

from .current_user import CurrentUser
from .dependencies import (
    get_account_service,
    get_auth_service,
    get_current_active_user,
    get_current_user,
    get_login_attempt_repository,
    get_password_history_repository,
    get_password_service,
    get_user_repository,
    require_admin,
    require_engineer,
    require_permission,
    require_project_manager,
    require_role,
)
from .endpoints import router
from .permissions import (
    PRIVILEGED_ROLES,
    check_resource_owner_or_privileged,
    get_owner_filter,
    is_privileged_user,
)
from .schemas import (
    ErrorResponse,
    LocalAccountCreateRequest,
    LocalAccountUpdateRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)

__all__ = [
    # Router
    "router",
    # Current User
    "CurrentUser",
    # Dependencies
    "get_auth_service",
    "get_password_service",
    "get_account_service",
    "get_user_repository",
    "get_login_attempt_repository",
    "get_password_history_repository",
    "get_current_user",
    "get_current_active_user",
    "require_permission",
    "require_role",
    "require_admin",
    "require_project_manager",
    "require_engineer",
    # Permissions
    "PRIVILEGED_ROLES",
    "check_resource_owner_or_privileged",
    "is_privileged_user",
    "get_owner_filter",
    # Schemas
    "LoginRequest",
    "RefreshTokenRequest",
    "LocalAccountCreateRequest",
    "LocalAccountUpdateRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "MessageResponse",
    "ErrorResponse",
]
