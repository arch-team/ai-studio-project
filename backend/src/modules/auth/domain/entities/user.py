"""User domain entity - Core business object for platform users."""

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.utils import utc_now

from ..value_objects import AuthType, UserRole, UserStatus


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

    # Authentication fields (for local accounts)
    auth_type: AuthType = AuthType.SSO
    password_hash: str | None = None
    password_expires_at: datetime | None = None
    locked_until: datetime | None = None
    failed_login_count: int = 0

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

    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        return self.locked_until is not None and utc_now() < self.locked_until

    def is_password_expired(self) -> bool:
        """Check if password has expired."""
        return self.password_expires_at is not None and utc_now() > self.password_expires_at

    def is_local_account(self) -> bool:
        """Check if this is a local authentication account."""
        return self.auth_type == AuthType.LOCAL

    def record_failed_login(self) -> None:
        """Record a failed login attempt."""
        self.failed_login_count += 1
        self.updated_at = utc_now()

    def lock_account(self, until: datetime) -> None:
        """Lock the account until specified time."""
        self.locked_until = until
        self.updated_at = utc_now()

    def reset_login_failures(self) -> None:
        """Reset failed login count and unlock account."""
        self.failed_login_count = 0
        self.locked_until = None
        self.updated_at = utc_now()

    def update_password(self, password_hash: str, expires_at: datetime) -> None:
        """Update password hash and expiration."""
        self.password_hash = password_hash
        self.password_expires_at = expires_at
        self.failed_login_count = 0
        self.locked_until = None
        self.updated_at = utc_now()
