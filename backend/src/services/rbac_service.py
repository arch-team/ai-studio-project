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
    conditions: Optional[dict] = None  # e.g., {"owner_only": True}


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

# Permission matrix: defines minimum role required for each action
PERMISSION_MATRIX: dict[ResourceType, dict[Action, tuple[Role, bool]]] = {
    # (minimum_role, owner_can_override)
    ResourceType.TRAINING_JOB: {
        Action.CREATE: (Role.ENGINEER, False),
        Action.READ: (Role.VIEWER, True),  # Viewers can read, owners can always read their own
        Action.UPDATE: (Role.ENGINEER, True),  # Engineers can update, owners can update their own
        Action.DELETE: (Role.PROJECT_MANAGER, True),  # PM+ can delete, owners can delete their own
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

    def __init__(self):
        """Initialize RBAC service."""
        self._permission_cache: dict[str, PermissionResult] = {}

    def get_role_level(self, role: str) -> int:
        """Get hierarchical level for a role.

        Args:
            role: Role name string

        Returns:
            Role level (higher = more privileges)
        """
        try:
            return ROLE_HIERARCHY.get(Role(role), 0)
        except ValueError:
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
        # Get permission requirements
        resource_permissions = PERMISSION_MATRIX.get(resource_type)
        if not resource_permissions:
            return PermissionResult(
                allowed=False,
                reason=f"Unknown resource type: {resource_type}",
            )

        action_requirement = resource_permissions.get(action)
        if not action_requirement:
            return PermissionResult(
                allowed=False,
                reason=f"Unknown action: {action} for resource {resource_type}",
            )

        minimum_role, owner_can_override = action_requirement

        # Check if user is the owner and owner override is allowed
        if owner_can_override and resource_owner_id and user_id:
            if resource_owner_id == user_id:
                return PermissionResult(
                    allowed=True,
                    reason="Owner access granted",
                )

        # Check role hierarchy
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
        allowed = []
        resource_permissions = PERMISSION_MATRIX.get(resource_type, {})

        for action, (minimum_role, owner_can_override) in resource_permissions.items():
            if is_owner and owner_can_override:
                allowed.append(action)
            elif self.has_minimum_role(user_role, minimum_role):
                allowed.append(action)

        return allowed

    def get_kubernetes_role_binding(self, user_role: str, namespace: str) -> dict:
        """Generate Kubernetes RoleBinding for user.

        Args:
            user_role: Platform role
            namespace: Kubernetes namespace

        Returns:
            Kubernetes RoleBinding manifest
        """
        # Map platform roles to Kubernetes ClusterRoles
        k8s_role_mapping = {
            Role.ADMIN: "cluster-admin",
            Role.PROJECT_MANAGER: "admin",
            Role.ENGINEER: "edit",
            Role.VIEWER: "view",
        }

        try:
            k8s_role = k8s_role_mapping.get(Role(user_role), "view")
        except ValueError:
            k8s_role = "view"

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
