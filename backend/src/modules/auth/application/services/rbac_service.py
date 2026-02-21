"""RBAC Service - Role-Based Access Control management."""

from functools import lru_cache

from src.shared.infrastructure.security import ROLE_HIERARCHY

from ...domain.exceptions import InsufficientPermissionsError
from ...domain.value_objects import Permission

# Role to permission mapping
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
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
# cluster_role: 自定义 ClusterRole (定义在 infrastructure/k8s/rbac/cluster-roles.yaml)
# namespace_role: 内置 K8s Role (命名空间级别通用操作)
K8S_RBAC_BINDINGS: dict[str, dict[str, str]] = {
    "admin": {
        "cluster_role": "platform-admin",
        "namespace_role": "admin",
    },
    "project_manager": {
        "cluster_role": "tenant-admin",
        "namespace_role": "edit",
    },
    "engineer": {
        "cluster_role": "training-user",
        "namespace_role": "edit",
    },
    "viewer": {
        "cluster_role": "viewer",
        "namespace_role": "view",
    },
}


class RBACService:
    """Role-Based Access Control service for permission management."""

    @staticmethod
    def _normalize_role(role: str) -> str:
        """Normalize role to lowercase."""
        return role.lower()

    def has_permission(self, role: str, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        return permission in ROLE_PERMISSIONS.get(self._normalize_role(role), set())

    def has_role_level(self, role: str, required_role: str) -> bool:
        """Check if a role meets or exceeds the required role level."""
        role_level = ROLE_HIERARCHY.get(self._normalize_role(role), 0)
        required_level = ROLE_HIERARCHY.get(self._normalize_role(required_role), 0)
        return role_level >= required_level

    def get_permissions(self, role: str) -> set[Permission]:
        """Get all permissions for a role."""
        return ROLE_PERMISSIONS.get(self._normalize_role(role), set())

    def get_k8s_rbac_binding(self, role: str) -> dict[str, str] | None:
        """Get K8s RBAC binding for a role."""
        return K8S_RBAC_BINDINGS.get(self._normalize_role(role))

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
        return ROLE_HIERARCHY.get(self._normalize_role(role), 0)

    def get_allowed_roles_for_permission(self, permission: Permission) -> list[str]:
        """Get list of roles that have a specific permission."""
        return [role for role, permissions in ROLE_PERMISSIONS.items() if permission in permissions]


@lru_cache
def get_rbac_service() -> RBACService:
    """Get cached RBAC service instance."""
    return RBACService()
