"""资源所有权检查依赖 - 统一的资源访问控制。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from fastapi import HTTPException, status


@runtime_checkable
class OwnedResource(Protocol):
    """拥有 owner_id 属性的资源协议。"""

    owner_id: int


# 可绕过所有权检查的特权角色
PRIVILEGED_ROLES = frozenset({"admin", "project_manager"})


def check_resource_ownership(
    resource: OwnedResource,
    user_id: int,
    user_role: str,
    *,
    admin_bypass: bool = True,
) -> None:
    """检查用户是否有权访问资源。

    admin 和 project_manager 角色默认绕过所有权检查。
    engineer 和 viewer 只能访问自己的资源。

    Raises:
        HTTPException: 403 如果用户无权访问
    """
    # 管理员角色绕过所有权检查
    if admin_bypass and user_role in PRIVILEGED_ROLES:
        return

    if resource.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
