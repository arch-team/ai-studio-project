"""Permission utilities - Resource ownership and access control."""

from fastapi import HTTPException, status

from .current_user import CurrentUser

# Roles that can access any user's resources
PRIVILEGED_ROLES = frozenset({"admin", "project_manager"})


def check_resource_owner_or_privileged(
    resource_owner_id: int,
    current_user: CurrentUser,
    resource_type: str = "resource",
    action: str = "access",
) -> None:
    """检查用户是否拥有资源或具有特权访问权限。

    Raises:
        HTTPException: 403 如果用户无权限
    """
    if is_privileged_user(current_user):
        return

    if resource_owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to {action} this {resource_type}",
        )


def is_privileged_user(current_user: CurrentUser) -> bool:
    """检查用户是否具有特权角色（admin/project_manager）。"""
    return current_user.role in PRIVILEGED_ROLES


def get_owner_filter(current_user: CurrentUser) -> int | None:
    """获取列表查询的 owner_id 过滤条件。

    特权用户返回 None（不过滤），普通用户返回自己的 user_id。
    """
    if is_privileged_user(current_user):
        return None
    return current_user.user_id
