"""User domain entity - Core business object for platform users."""

from dataclasses import dataclass, field
from datetime import datetime

from src.core.utils import utc_now
from src.domain.value_objects import UserRole, UserStatus


@dataclass
class User:
    """User domain entity representing a platform user."""

    id: int
    username: str
    email: str
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.ENGINEER
    display_name: str | None = None
    iam_identity_id: str | None = None
    iam_groups: list[str] = field(default_factory=list)
    resource_quota_id: int | None = None
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

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
        self.updated_at = utc_now()

    def activate(self) -> None:
        """Activate user account."""
        self.status = UserStatus.ACTIVE
        self.updated_at = utc_now()

    def record_login(self) -> None:
        """Record user login timestamp."""
        self.last_login_at = utc_now()
        self.updated_at = utc_now()
