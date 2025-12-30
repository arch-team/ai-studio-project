"""基于角色的访问控制(RBAC)

定义权限和角色检查逻辑
"""

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User, UserRole


class Permission(str, Enum):
    """权限枚举"""

    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 团队管理
    TEAM_CREATE = "team:create"
    TEAM_READ = "team:read"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    TEAM_MANAGE_MEMBERS = "team:manage_members"

    # 项目管理
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    # 训练任务
    TRAINING_JOB_CREATE = "training_job:create"
    TRAINING_JOB_READ = "training_job:read"
    TRAINING_JOB_UPDATE = "training_job:update"
    TRAINING_JOB_DELETE = "training_job:delete"
    TRAINING_JOB_START = "training_job:start"
    TRAINING_JOB_STOP = "training_job:stop"

    # 数据集管理
    DATASET_CREATE = "dataset:create"
    DATASET_READ = "dataset:read"
    DATASET_UPDATE = "dataset:update"
    DATASET_DELETE = "dataset:delete"
    DATASET_UPLOAD = "dataset:upload"

    # 资源管理
    RESOURCE_QUOTA_CREATE = "resource_quota:create"
    RESOURCE_QUOTA_READ = "resource_quota:read"
    RESOURCE_QUOTA_UPDATE = "resource_quota:update"
    RESOURCE_QUOTA_DELETE = "resource_quota:delete"
    RESOURCE_MONITOR = "resource:monitor"

    # 成本分析
    COST_READ = "cost:read"
    COST_ANALYZE = "cost:analyze"

    # 开发环境
    DEV_ENV_CREATE = "dev_env:create"
    DEV_ENV_USE = "dev_env:use"


# 角色权限映射
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "admin": {
        # 管理员拥有所有权限
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.TEAM_CREATE,
        Permission.TEAM_READ,
        Permission.TEAM_UPDATE,
        Permission.TEAM_DELETE,
        Permission.TEAM_MANAGE_MEMBERS,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.TRAINING_JOB_CREATE,
        Permission.TRAINING_JOB_READ,
        Permission.TRAINING_JOB_UPDATE,
        Permission.TRAINING_JOB_DELETE,
        Permission.TRAINING_JOB_START,
        Permission.TRAINING_JOB_STOP,
        Permission.DATASET_CREATE,
        Permission.DATASET_READ,
        Permission.DATASET_UPDATE,
        Permission.DATASET_DELETE,
        Permission.DATASET_UPLOAD,
        Permission.RESOURCE_QUOTA_CREATE,
        Permission.RESOURCE_QUOTA_READ,
        Permission.RESOURCE_QUOTA_UPDATE,
        Permission.RESOURCE_QUOTA_DELETE,
        Permission.RESOURCE_MONITOR,
        Permission.COST_READ,
        Permission.COST_ANALYZE,
        Permission.DEV_ENV_CREATE,
        Permission.DEV_ENV_USE,
    },
    "project_manager": {
        # 项目经理权限
        Permission.USER_READ,
        Permission.TEAM_CREATE,
        Permission.TEAM_READ,
        Permission.TEAM_UPDATE,
        Permission.TEAM_MANAGE_MEMBERS,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.TRAINING_JOB_READ,
        Permission.TRAINING_JOB_UPDATE,
        Permission.TRAINING_JOB_START,
        Permission.TRAINING_JOB_STOP,
        Permission.DATASET_READ,
        Permission.RESOURCE_QUOTA_READ,
        Permission.RESOURCE_MONITOR,
        Permission.COST_READ,
        Permission.COST_ANALYZE,
    },
    "algorithm_engineer": {
        # 算法工程师权限
        Permission.USER_READ,
        Permission.TEAM_READ,
        Permission.PROJECT_READ,
        Permission.TRAINING_JOB_CREATE,
        Permission.TRAINING_JOB_READ,
        Permission.TRAINING_JOB_UPDATE,
        Permission.TRAINING_JOB_START,
        Permission.TRAINING_JOB_STOP,
        Permission.DATASET_READ,
        Permission.RESOURCE_MONITOR,
        Permission.DEV_ENV_CREATE,
        Permission.DEV_ENV_USE,
    },
    "data_engineer": {
        # 数据工程师权限
        Permission.USER_READ,
        Permission.TEAM_READ,
        Permission.PROJECT_READ,
        Permission.TRAINING_JOB_READ,
        Permission.DATASET_CREATE,
        Permission.DATASET_READ,
        Permission.DATASET_UPDATE,
        Permission.DATASET_DELETE,
        Permission.DATASET_UPLOAD,
        Permission.RESOURCE_MONITOR,
    },
    "viewer": {
        # 查看者权限
        Permission.USER_READ,
        Permission.TEAM_READ,
        Permission.PROJECT_READ,
        Permission.TRAINING_JOB_READ,
        Permission.DATASET_READ,
        Permission.RESOURCE_MONITOR,
        Permission.COST_READ,
    },
}


def has_permission(user: "User", permission: Permission) -> bool:
    """检查用户是否拥有指定权限

    Args:
        user: 用户对象
        permission: 权限

    Returns:
        bool: True表示拥有权限
    """
    # 超级用户拥有所有权限
    if user.is_superuser:
        return True

    # 检查角色权限
    role_perms = ROLE_PERMISSIONS.get(user.role.value, set())
    return permission in role_perms


def has_any_permission(user: "User", permissions: list[Permission]) -> bool:
    """检查用户是否拥有任意一个权限

    Args:
        user: 用户对象
        permissions: 权限列表

    Returns:
        bool: True表示拥有至少一个权限
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: "User", permissions: list[Permission]) -> bool:
    """检查用户是否拥有所有权限

    Args:
        user: 用户对象
        permissions: 权限列表

    Returns:
        bool: True表示拥有所有权限
    """
    return all(has_permission(user, perm) for perm in permissions)


def require_permission(permission: Permission):
    """权限装饰器

    Args:
        permission: 所需权限

    Returns:
        装饰器函数

    Example:
        @require_permission(Permission.USER_CREATE)
        async def create_user(...):
            pass
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            user = kwargs.get("current_user")
            if not user:
                raise ValueError("User not found in kwargs")

            if not has_permission(user, permission):
                raise PermissionError(f"Permission denied: {permission.value}")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "Permission",
    "ROLE_PERMISSIONS",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
    "require_permission",
]
