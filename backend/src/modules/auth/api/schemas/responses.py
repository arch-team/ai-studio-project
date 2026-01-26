"""Authentication response schemas."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.auth.domain.entities import User  # noqa: F401


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class UserResponse(EntitySchema["User"]):
    """User response schema."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    display_name: str | None = Field(default=None, description="Display name")
    role: str = Field(..., description="User role")
    status: str = Field(..., description="User status")
    auth_type: str = Field(..., description="Authentication type")

    # 枚举转字符串的自定义映射
    _custom_mappings: ClassVar[dict[str, Callable[[Any], Any]]] = {
        "role": lambda e: e.role.value,
        "status": lambda e: e.status.value,
        "auth_type": lambda e: e.auth_type.value,
    }


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
