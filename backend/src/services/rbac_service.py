"""RBAC (Role-Based Access Control) Service.

Task: T013b - RBAC 策略管理
定义角色层次 (admin/project_manager/engineer/viewer),
实现基于资源的权限检查,集成 Kubernetes RBAC
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """Platform roles with hierarchical permissions."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class ResourceType(str, Enum):
    """Types of resources that can be protected."""

    TRAINING_JOB = "training_job"
    DATASET = "dataset"
    MODEL = "model"
    CHECKPOINT = "checkpoint"
    SPACE = "space"
    USER = "user"
    QUOTA = "quota"
    PROJECT = "project"
    SYSTEM = "system"


class Action(str, Enum):
    """Actions that can be performed on resources."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXECUTE = "execute"  # For jobs: start, stop, pause, resume
    ADMIN = "admin"  # Administrative actions


@dataclass
class Permission:
    """Permission definition."""

    resource_type: ResourceType
    action: Action
    conditions: Optional[dict[str, bool]] = None  # e.g., {"owner_only": True}


class PermissionResult(BaseModel):
    """Result of permission check."""

    allowed: bool
    reason: Optional[str] = None
    required_role: Optional[str] = None


# Role hierarchy (higher number = more privileges)
ROLE_HIERARCHY = {
    Role.VIEWER: 1,
    Role.ENGINEER: 2,
    Role.PROJECT_MANAGER: 3,
    Role.ADMIN: 4,
}

# Kubernetes role mapping
K8S_ROLE_MAPPING = {
    Role.ADMIN: "cluster-admin",
    Role.PROJECT_MANAGER: "admin",
    Role.ENGINEER: "edit",
    Role.VIEWER: "view",
}

# Permission matrix: defines minimum role required for each action
PERMISSION_MATRIX: dict[ResourceType, dict[Action, tuple[Role, bool]]] = {
    # (minimum_role, owner_can_override)
    ResourceType.TRAINING_JOB: {
        Action.CREATE: (Role.ENGINEER, False),
        Action.READ: (
            Role.VIEWER,
            True,
        ),  # Viewers can read, owners can always read their own
        Action.UPDATE: (
            Role.ENGINEER,
            True,
        ),  # Engineers can update, owners can update their own
        Action.DELETE: (
            Role.PROJECT_MANAGER,
            True,
        ),  # PM+ can delete, owners can delete their own
        Action.LIST: (Role.VIEWER, False),
        Action.EXECUTE: (Role.ENGINEER, True),  # Start, stop, pause, resume
    },
    ResourceType.DATASET: {
        Action.CREATE: (Role.ENGINEER, False),
        Action.READ: (Role.VIEWER, False),
        Action.UPDATE: (Role.ENGINEER, True),
        Action.DELETE: (Role.PROJECT_MANAGER, True),
        Action.LIST: (Role.VIEWER, False),
    },
    ResourceType.MODEL: {
        Action.CREATE: (Role.ENGINEER, False),
        Action.READ: (Role.VIEWER, False),
        Action.UPDATE: (Role.ENGINEER, True),
        Action.DELETE: (Role.PROJECT_MANAGER, True),
        Action.LIST: (Role.VIEWER, False),
    },
    ResourceType.CHECKPOINT: {
        Action.CREATE: (Role.ENGINEER, False),
        Action.READ: (Role.VIEWER, True),
        Action.UPDATE: (Role.ENGINEER, True),
        Action.DELETE: (Role.ENGINEER, True),
        Action.LIST: (Role.VIEWER, False),
    },
    ResourceType.SPACE: {
        Action.CREATE: (Role.ENGINEER, False),
        Action.READ: (Role.VIEWER, True),
        Action.UPDATE: (Role.ENGINEER, True),
        Action.DELETE: (Role.ENGINEER, True),
        Action.LIST: (Role.VIEWER, False),
        Action.EXECUTE: (Role.ENGINEER, True),  # Start, stop space
    },
    ResourceType.USER: {
        Action.CREATE: (Role.ADMIN, False),
        Action.READ: (Role.PROJECT_MANAGER, True),  # Users can read their own info
        Action.UPDATE: (Role.ADMIN, True),  # Users can update their own profile
        Action.DELETE: (Role.ADMIN, False),
        Action.LIST: (Role.PROJECT_MANAGER, False),
        Action.ADMIN: (Role.ADMIN, False),
    },
    ResourceType.QUOTA: {
        Action.CREATE: (Role.ADMIN, False),
        Action.READ: (Role.VIEWER, False),
        Action.UPDATE: (Role.ADMIN, False),
        Action.DELETE: (Role.ADMIN, False),
        Action.LIST: (Role.VIEWER, False),
    },
    ResourceType.PROJECT: {
        Action.CREATE: (Role.ADMIN, False),
        Action.READ: (Role.VIEWER, False),
        Action.UPDATE: (Role.PROJECT_MANAGER, False),
        Action.DELETE: (Role.ADMIN, False),
        Action.LIST: (Role.VIEWER, False),
    },
    ResourceType.SYSTEM: {
        Action.READ: (Role.ADMIN, False),
        Action.UPDATE: (Role.ADMIN, False),
        Action.ADMIN: (Role.ADMIN, False),
    },
}


class RBACService:
    """Service for role-based access control."""

    def __init__(self) -> None:
        """Initialize RBAC service."""
        self._permission_cache: dict[str, PermissionResult] = {}
        # 预先计算角色值集合，避免重复生成
        self._valid_roles: set[str] = {r.value for r in Role}
        # 预先创建角色字符串到枚举的映射，避免重复转换
        self._role_enum_map: dict[str, Role] = {r.value: r for r in Role}

    def get_role_level(self, role: str) -> int:
        """Get hierarchical level for a role.

        Args:
            role: Role name string

        Returns:
            Role level (higher = more privileges)
        """
        # 使用预计算的集合和映射，提升性能
        if role in self._valid_roles:
            return ROLE_HIERARCHY.get(self._role_enum_map[role], 0)
        return 0

    def has_minimum_role(self, user_role: str, required_role: Role) -> bool:
        """Check if user role meets minimum requirement.

        Args:
            user_role: User's current role
            required_role: Minimum required role

        Returns:
            True if user has sufficient role level
        """
        user_level = self.get_role_level(user_role)
        required_level = ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level

    def check_permission(
        self,
        user_role: str,
        resource_type: ResourceType,
        action: Action,
        resource_owner_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> PermissionResult:
        """Check if user has permission for an action on a resource.

        Args:
            user_role: User's role
            resource_type: Type of resource
            action: Action to perform
            resource_owner_id: ID of resource owner (for owner checks)
            user_id: ID of requesting user

        Returns:
            PermissionResult with allowed status and reason
        """
        # 获取权限要求，使用更简洁的访问方式
        action_requirement = PERMISSION_MATRIX.get(resource_type, {}).get(action)

        if action_requirement is None:
            # 判断是资源类型错误还是操作错误
            if resource_type not in PERMISSION_MATRIX:
                return PermissionResult(
                    allowed=False,
                    reason=f"Unknown resource type: {resource_type}",
                )
            return PermissionResult(
                allowed=False,
                reason=f"Unknown action: {action} for resource {resource_type}",
            )

        minimum_role, owner_can_override = action_requirement

        # 检查所有者权限（简化条件判断）
        is_owner = owner_can_override and resource_owner_id == user_id
        if is_owner:
            return PermissionResult(
                allowed=True,
                reason="Owner access granted",
            )

        # 检查角色层级
        if self.has_minimum_role(user_role, minimum_role):
            return PermissionResult(allowed=True)

        return PermissionResult(
            allowed=False,
            reason=f"Insufficient permissions. Required role: {minimum_role.value}",
            required_role=minimum_role.value,
        )

    def get_allowed_actions(
        self,
        user_role: str,
        resource_type: ResourceType,
        is_owner: bool = False,
    ) -> list[Action]:
        """Get list of allowed actions for a user on a resource type.

        Args:
            user_role: User's role
            resource_type: Type of resource
            is_owner: Whether user owns the resource

        Returns:
            List of allowed actions
        """
        resource_permissions = PERMISSION_MATRIX.get(resource_type, {})

        # 使用列表推导式替代循环，更简洁高效
        return [
            action
            for action, (
                minimum_role,
                owner_can_override,
            ) in resource_permissions.items()
            if (is_owner and owner_can_override)
            or self.has_minimum_role(user_role, minimum_role)
        ]

    def get_kubernetes_role_binding(
        self, user_role: str, namespace: str
    ) -> dict[str, object]:
        """Generate Kubernetes RoleBinding for user.

        Args:
            user_role: Platform role
            namespace: Kubernetes namespace

        Returns:
            Kubernetes RoleBinding manifest
        """
        # 将 k8s 角色映射移到类属性中，避免每次重新创建
        k8s_role = self._get_k8s_role(user_role)

        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": f"platform-{user_role}",
                "namespace": namespace,
            },
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": k8s_role,
            },
        }

    def _get_k8s_role(self, user_role: str) -> str:
        """Map platform role to Kubernetes ClusterRole.

        Args:
            user_role: Platform role string

        Returns:
            Kubernetes ClusterRole name
        """
        # 使用预计算的映射，避免异常处理
        if user_role in self._valid_roles:
            role_enum = self._role_enum_map[user_role]
            return K8S_ROLE_MAPPING.get(role_enum, "view")
        return "view"


# Singleton instance
_rbac_service: Optional[RBACService] = None


def get_rbac_service() -> RBACService:
    """Get or create RBAC service singleton.

    Returns:
        RBACService instance
    """
    global _rbac_service
    if _rbac_service is None:
        _rbac_service = RBACService()
    return _rbac_service
