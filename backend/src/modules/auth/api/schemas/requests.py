"""Authentication request schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str | None = Field(None, min_length=1, max_length=64, description="Username for local login")
    password: str | None = Field(None, max_length=128, description="Password for local login")
    id_token: str | None = Field(None, description="SSO ID token")


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str = Field(..., description="Refresh token")


class LocalAccountCreateRequest(BaseModel):
    """Create local account request schema."""

    username: str = Field(..., min_length=3, max_length=64, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=12, max_length=128, description="Password")
    display_name: str | None = Field(None, max_length=128, description="Display name")
    role: str = Field(default="engineer", description="User role")


class LocalAccountUpdateRequest(BaseModel):
    """Update local account request schema."""

    email: EmailStr | None = Field(None, description="Email address")
    display_name: str | None = Field(None, max_length=128, description="Display name")
    role: str | None = Field(None, description="User role")


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""

    current_password: str = Field(..., min_length=1, max_length=128, description="Current password")
    new_password: str = Field(..., min_length=12, max_length=128, description="New password")


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation schema."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=12, max_length=128, description="New password")
