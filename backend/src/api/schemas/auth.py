"""认证相关的Pydantic模式"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名或邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "admin",
                    "password": "admin123456",
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """令牌响应"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌过期时间(秒)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800,
                }
            ]
        }
    }


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(..., description="刷新令牌")

    model_config = {
        "json_schema_extra": {
            "examples": [{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}]
        }
    }


class UserInfo(BaseModel):
    """用户信息"""

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: str | None = Field(None, description="全名")
    role: str = Field(..., description="角色")
    status: str = Field(..., description="状态")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "full_name": "System Administrator",
                    "role": "ADMIN",
                    "status": "ACTIVE",
                    "is_active": True,
                    "is_superuser": True,
                }
            ]
        },
    }


__all__ = [
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserInfo",
]
