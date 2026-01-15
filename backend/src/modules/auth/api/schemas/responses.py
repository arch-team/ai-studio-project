"""Authentication response schemas."""

from pydantic import BaseModel, Field


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


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str = Field(..., description="Response message")


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str = Field(..., description="Error detail message")
