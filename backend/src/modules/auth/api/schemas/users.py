"""User management schemas - requests and responses for user CRUD API."""

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, EmailStr, Field

from src.shared.api.pagination import PaginatedResponse
from src.shared.api.schemas import AutoMappingEntitySchema

if TYPE_CHECKING:
    from src.modules.auth.domain.entities import User


class UserRoleEnum(str, Enum):
    """User role enum for validation."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class UserStatusEnum(str, Enum):
    """User status enum for validation."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# === Request Schemas ===


class CreateUserRequest(BaseModel):
    """Create user request schema (T056)."""

    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    display_name: str | None = Field(None, max_length=128, description="显示名称")
    role: UserRoleEnum = Field(..., description="用户角色")
    resource_quota_id: int | None = Field(None, ge=1, description="资源配额 ID")


class UpdateUserRequest(BaseModel):
    """Update user request schema (T057)."""

    role: UserRoleEnum | None = Field(None, description="用户角色")
    status: UserStatusEnum | None = Field(None, description="用户状态")
    display_name: str | None = Field(None, max_length=128, description="显示名称")
    resource_quota_id: int | None = Field(None, ge=1, description="资源配额 ID")


# === Response Schemas ===


class UserDetailResponse(AutoMappingEntitySchema["User"]):
    """User detail response schema."""

    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    display_name: str | None = Field(None, description="显示名称")
    role: str = Field(..., description="用户角色")
    status: str = Field(..., description="用户状态")
    auth_type: str = Field(..., description="认证类型")
    resource_quota_id: int | None = Field(None, description="资源配额 ID")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 枚举转字符串的自定义映射
    _custom_mappings: ClassVar[dict[str, Callable[[Any], Any]]] = {
        "role": lambda e: e.role.value,
        "status": lambda e: e.status.value,
        "auth_type": lambda e: e.auth_type.value,
    }


class UserSummaryResponse(BaseModel):
    """User summary for list response."""

    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    display_name: str | None = Field(None, description="显示名称")
    role: str = Field(..., description="用户角色")
    status: str = Field(..., description="用户状态")
    auth_type: str = Field(..., description="认证类型")
    created_at: datetime = Field(..., description="创建时间")

    @classmethod
    def from_entity(cls, entity: "User") -> "UserSummaryResponse":
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            display_name=entity.display_name,
            role=entity.role.value,
            status=entity.status.value,
            auth_type=entity.auth_type.value,
            created_at=entity.created_at,
        )


class UserListResponse(PaginatedResponse[UserSummaryResponse]):
    """User list response schema (T055)."""

    pass
