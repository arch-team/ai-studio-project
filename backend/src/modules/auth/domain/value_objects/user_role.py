"""User role value object."""

from enum import Enum


class UserRole(Enum):
    """User platform role with permission hierarchy."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"

    def has_permission(self, required_role: "UserRole") -> bool:
        """Check if this role has at least the permissions of required_role."""
        hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.PROJECT_MANAGER: 3,
            UserRole.ENGINEER: 2,
            UserRole.VIEWER: 1,
        }
        return hierarchy[self] >= hierarchy[required_role]
