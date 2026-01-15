"""Authentication Schemas - Request/response models for auth endpoints."""

from pydantic import BaseModel, EmailStr, Field

from src.api.v1.schemas.common import ErrorResponse

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "RefreshTokenRequest",
    "LocalAccountCreateRequest",
    "LocalAccountUpdateRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "MessageResponse",
    "ErrorResponse",
]


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str | None = Field(
        None, min_length=1, max_length=64, description="Username for local login"
    )
    password: str | None = Field(None, description="Password for local login")
    id_token: str | None = Field(None, description="SSO ID token")


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class UserResponse(BaseModel):
    """User response schema."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    display_name: str | None = Field(None, description="Display name")
    role: str = Field(..., description="User role")
    status: str = Field(..., description="User status")
    auth_type: str = Field(..., description="Authentication type")


class LoginResponse(BaseModel):
    """Login response schema."""

    tokens: TokenResponse = Field(..., description="Access and refresh tokens")
    user: UserResponse = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str = Field(..., description="Refresh token")


class LocalAccountCreateRequest(BaseModel):
    """Create local account request schema."""

    username: str = Field(..., min_length=3, max_length=64, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=12, description="Password")
    display_name: str | None = Field(None, max_length=128, description="Display name")
    role: str = Field(default="engineer", description="User role")


class LocalAccountUpdateRequest(BaseModel):
    """Update local account request schema."""

    email: EmailStr | None = Field(None, description="Email address")
    display_name: str | None = Field(None, max_length=128, description="Display name")
    role: str | None = Field(None, description="User role")


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=12, description="New password")


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation schema."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=12, description="New password")


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str = Field(..., description="Response message")
