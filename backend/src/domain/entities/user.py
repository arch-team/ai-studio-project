"""User domain entity - Core business object for platform users."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class UserStatus(Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


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


@dataclass
class User:
    """User domain entity representing a platform user.

    Attributes:
        id: Unique user identifier
        username: IAM username (unique)
        email: Email address (unique)
        status: Account status
        role: Platform role determining permissions
    """

    id: int
    username: str
    email: str
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.ENGINEER
    display_name: Optional[str] = None
    iam_identity_id: Optional[str] = None
    iam_groups: list[str] = field(default_factory=list)
    resource_quota_id: Optional[int] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    def has_admin_privileges(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    def can_manage_projects(self) -> bool:
        """Check if user can manage projects."""
        return self.role.has_permission(UserRole.PROJECT_MANAGER)

    def can_create_training_job(self) -> bool:
        """Check if user can create training jobs."""
        return self.is_active() and self.role.has_permission(UserRole.ENGINEER)

    def can_view_resources(self) -> bool:
        """Check if user can view resources."""
        return self.is_active() and self.role.has_permission(UserRole.VIEWER)

    def suspend(self) -> None:
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate user account."""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def record_login(self) -> None:
        """Record user login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
