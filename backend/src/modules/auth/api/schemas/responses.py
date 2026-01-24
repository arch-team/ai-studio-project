"""Authentication response schemas."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.modules.auth.domain.entities import User


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

    @classmethod
    def from_entity(cls, user: "User") -> "UserResponse":
        """从 User 实体创建响应."""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            role=user.role.value,
            status=user.status.value,
            auth_type=user.auth_type.value,
        )


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
