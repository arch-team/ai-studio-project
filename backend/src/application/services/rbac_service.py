"""RBAC Service - Role-Based Access Control management."""

from enum import Enum
from typing import Dict, List, Optional, Set

from src.core.security.constants import ROLE_HIERARCHY
from src.core.security.exceptions import InsufficientPermissionsError


class Permission(str, Enum):
    """Permission definitions for the platform."""

    # User management
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Training job management
    TRAINING_JOB_VIEW = "training_job:view"
    TRAINING_JOB_CREATE = "training_job:create"
    TRAINING_JOB_UPDATE = "training_job:update"
    TRAINING_JOB_DELETE = "training_job:delete"
    TRAINING_JOB_CANCEL = "training_job:cancel"

    # Dataset management
    DATASET_VIEW = "dataset:view"
    DATASET_CREATE = "dataset:create"
    DATASET_UPDATE = "dataset:update"
    DATASET_DELETE = "dataset:delete"

    # Model management
    MODEL_VIEW = "model:view"
    MODEL_CREATE = "model:create"
    MODEL_UPDATE = "model:update"
    MODEL_DELETE = "model:delete"
    MODEL_DEPLOY = "model:deploy"

    # Cluster management
    CLUSTER_VIEW = "cluster:view"
    CLUSTER_CREATE = "cluster:create"
    CLUSTER_UPDATE = "cluster:update"
    CLUSTER_DELETE = "cluster:delete"
    CLUSTER_SCALE = "cluster:scale"

    # Resource quota management
    QUOTA_VIEW = "quota:view"
    QUOTA_CREATE = "quota:create"
    QUOTA_UPDATE = "quota:update"
    QUOTA_DELETE = "quota:delete"

    # Development space management
    DEV_SPACE_VIEW = "dev_space:view"
    DEV_SPACE_CREATE = "dev_space:create"
    DEV_SPACE_UPDATE = "dev_space:update"
    DEV_SPACE_DELETE = "dev_space:delete"

    # Audit log access
    AUDIT_VIEW = "audit:view"

    # System administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"


# Role to permission mapping
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    "admin": set(Permission),  # Admin has all permissions
    "project_manager": {
        # Project manager: manage jobs, datasets, models within project
        Permission.USER_VIEW,
        Permission.TRAINING_JOB_VIEW,
        Permission.TRAINING_JOB_CREATE,
        Permission.TRAINING_JOB_UPDATE,
        Permission.TRAINING_JOB_DELETE,
        Permission.TRAINING_JOB_CANCEL,
        Permission.DATASET_VIEW,
        Permission.DATASET_CREATE,
        Permission.DATASET_UPDATE,
        Permission.DATASET_DELETE,
        Permission.MODEL_VIEW,
        Permission.MODEL_CREATE,
        Permission.MODEL_UPDATE,
        Permission.MODEL_DELETE,
        Permission.MODEL_DEPLOY,
        Permission.CLUSTER_VIEW,
        Permission.QUOTA_VIEW,
        Permission.DEV_SPACE_VIEW,
        Permission.DEV_SPACE_CREATE,
        Permission.DEV_SPACE_UPDATE,
        Permission.DEV_SPACE_DELETE,
        Permission.AUDIT_VIEW,
        Permission.SYSTEM_MONITOR,
    },
    "engineer": {
        # Engineer: create and manage own jobs, view resources
        Permission.USER_VIEW,
        Permission.TRAINING_JOB_VIEW,
        Permission.TRAINING_JOB_CREATE,
        Permission.TRAINING_JOB_UPDATE,
        Permission.TRAINING_JOB_CANCEL,
        Permission.DATASET_VIEW,
        Permission.DATASET_CREATE,
        Permission.MODEL_VIEW,
        Permission.MODEL_CREATE,
        Permission.MODEL_UPDATE,
        Permission.CLUSTER_VIEW,
        Permission.QUOTA_VIEW,
        Permission.DEV_SPACE_VIEW,
        Permission.DEV_SPACE_CREATE,
        Permission.DEV_SPACE_UPDATE,
    },
    "viewer": {
        # Viewer: read-only access
        Permission.USER_VIEW,
        Permission.TRAINING_JOB_VIEW,
        Permission.DATASET_VIEW,
        Permission.MODEL_VIEW,
        Permission.CLUSTER_VIEW,
        Permission.QUOTA_VIEW,
        Permission.DEV_SPACE_VIEW,
    },
}

# K8s RBAC binding mappings
K8S_RBAC_BINDINGS: Dict[str, Dict[str, str]] = {
    "admin": {
        "cluster_role": "cluster-admin",
        "namespace_role": "admin",
    },
    "project_manager": {
        "cluster_role": "view",
        "namespace_role": "edit",
    },
    "engineer": {
        "cluster_role": "view",
        "namespace_role": "edit",
    },
    "viewer": {
        "cluster_role": "view",
        "namespace_role": "view",
    },
}


class RBACService:
    """Role-Based Access Control service for permission management."""

    def has_permission(self, role: str, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        role_lower = role.lower()
        return permission in ROLE_PERMISSIONS.get(role_lower, set())

    def has_role_level(self, role: str, required_role: str) -> bool:
        """Check if a role meets or exceeds the required role level."""
        role_lower = role.lower()
        required_lower = required_role.lower()

        role_level = ROLE_HIERARCHY.get(role_lower, 0)
        required_level = ROLE_HIERARCHY.get(required_lower, 0)

        return role_level >= required_level

    def get_permissions(self, role: str) -> Set[Permission]:
        """Get all permissions for a role."""
        role_lower = role.lower()
        return ROLE_PERMISSIONS.get(role_lower, set())

    def get_k8s_rbac_binding(self, role: str) -> Optional[Dict[str, str]]:
        """Get K8s RBAC binding for a role."""
        role_lower = role.lower()
        return K8S_RBAC_BINDINGS.get(role_lower)

    def check_permission(self, role: str, permission: Permission) -> None:
        """Check permission and raise exception if not authorized."""
        if not self.has_permission(role, permission):
            raise InsufficientPermissionsError(permission.value)

    def check_role_level(self, role: str, required_role: str) -> None:
        """Check role level and raise exception if insufficient."""
        if not self.has_role_level(role, required_role):
            raise InsufficientPermissionsError(f"role:{required_role}")

    def get_role_level(self, role: str) -> int:
        """Get numeric level for a role."""
        return ROLE_HIERARCHY.get(role.lower(), 0)

    def get_allowed_roles_for_permission(self, permission: Permission) -> List[str]:
        """Get list of roles that have a specific permission."""
        return [
            role
            for role, permissions in ROLE_PERMISSIONS.items()
            if permission in permissions
        ]


# Singleton instance
_rbac_service: Optional[RBACService] = None


def get_rbac_service() -> RBACService:
    """Get or create RBAC service singleton."""
    global _rbac_service
    if _rbac_service is None:
        _rbac_service = RBACService()
    return _rbac_service
