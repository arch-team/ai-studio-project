"""Auth API schemas."""

from .requests import (
    LocalAccountCreateRequest,
    LocalAccountUpdateRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
)
from .responses import (
    ErrorResponse,
    LoginResponse,
    MessageResponse,
    TokenResponse,
    UserResponse,
)
from .users import (
    CreateUserRequest,
    UpdateUserRequest,
    UserDetailResponse,
    UserListResponse,
    UserRoleEnum,
    UserStatusEnum,
    UserSummaryResponse,
)

__all__ = [
    # Requests
    "LoginRequest",
    "RefreshTokenRequest",
    "LocalAccountCreateRequest",
    "LocalAccountUpdateRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    # User Management Requests
    "CreateUserRequest",
    "UpdateUserRequest",
    # User Management Responses
    "UserDetailResponse",
    "UserListResponse",
    "UserSummaryResponse",
    "UserRoleEnum",
    "UserStatusEnum",
    # Responses
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "MessageResponse",
    "ErrorResponse",
]
