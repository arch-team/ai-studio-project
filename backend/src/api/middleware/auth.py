"""JWT认证中间件

提供基于JWT的认证功能和依赖注入
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from models.user import User
from services.auth.security import verify_token

# HTTP Bearer认证方案
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """获取当前认证用户

    从JWT令牌中提取用户信息并从数据库加载完整用户对象

    Args:
        credentials: HTTP Bearer认证凭据
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败（401）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 验证令牌
        token = credentials.credentials
        payload = verify_token(token, token_type="access")

        # 从payload中提取用户ID
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # 从数据库加载用户
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        # 检查用户状态
        if not user.is_active or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive or deleted",
            )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        raise credentials_exception from e


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前活跃用户

    确保用户处于活跃状态

    Args:
        current_user: 当前用户

    Returns:
        User: 活跃的用户对象

    Raises:
        HTTPException: 用户未激活（403）
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """获取当前管理员用户

    确保用户具有管理员权限

    Args:
        current_user: 当前用户

    Returns:
        User: 管理员用户对象

    Raises:
        HTTPException: 权限不足（403）
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges. Admin access required.",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """获取当前超级用户

    确保用户是超级用户

    Args:
        current_user: 当前用户

    Returns:
        User: 超级用户对象

    Raises:
        HTTPException: 权限不足（403）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


# 类型别名，方便使用
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
CurrentSuperUser = Annotated[User, Depends(get_current_superuser)]


__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_superuser",
    "CurrentUser",
    "CurrentActiveUser",
    "CurrentAdminUser",
    "CurrentSuperUser",
]
