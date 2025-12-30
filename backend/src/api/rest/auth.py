"""认证相关API端点"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse, UserInfo
from config.database import get_db
from config.settings import settings
from models.user import User
from services.auth.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="使用用户名/邮箱和密码登录,返回JWT访问令牌和刷新令牌",
)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """用户登录

    Args:
        login_data: 登录请求数据
        db: 数据库会话

    Returns:
        TokenResponse: JWT令牌响应

    Raises:
        HTTPException: 401 - 用户名或密码错误
        HTTPException: 403 - 账户未激活或已删除
    """
    # 查询用户(支持用户名或邮箱登录)
    result = await db.execute(
        select(User).where(
            (User.username == login_data.username) | (User.email == login_data.username)
        )
    )
    user = result.scalar_one_or_none()

    # 验证用户存在性和密码
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查账户状态
    if not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活或已删除",
        )

    # 生成JWT令牌
    token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """刷新访问令牌

    Args:
        refresh_data: 刷新令牌请求
        db: 数据库会话

    Returns:
        TokenResponse: 新的JWT令牌

    Raises:
        HTTPException: 401 - 刷新令牌无效
        HTTPException: 404 - 用户不存在
    """
    try:
        # 验证刷新令牌
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证用户是否存在
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

        # 检查账户状态
        if not user.is_active or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户未激活或已删除",
            )

        # 生成新的访问令牌
        token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
        access_token = create_access_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # 保持原刷新令牌
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="用户登出",
    description="登出当前用户(客户端需要清除本地令牌)",
)
async def logout() -> None:
    """用户登出

    注意: JWT令牌是无状态的,服务端无法主动使令牌失效
    此端点主要用于客户端清除本地令牌的语义化操作
    实际的令牌失效依赖于过期时间

    对于高安全性需求,可以考虑实现令牌黑名单机制
    """
    # JWT无状态特性,实际登出由客户端处理
    # 服务端可以在此记录登出日志或执行其他清理操作
    pass


@router.get(
    "/me",
    response_model=UserInfo,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfo:
    """获取当前用户信息

    Args:
        current_user: 当前登录用户

    Returns:
        UserInfo: 用户信息
    """
    return UserInfo.model_validate(current_user)


# 为了避免循环导入,在这里导入get_current_user
from api.middleware.auth import get_current_user  # noqa: E402

__all__ = ["router"]
