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

__all__ = [
    # Requests
    "LoginRequest",
    "RefreshTokenRequest",
    "LocalAccountCreateRequest",
    "LocalAccountUpdateRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    # Responses
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "MessageResponse",
    "ErrorResponse",
]
