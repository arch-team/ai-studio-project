"""Unit tests for User domain entity.

Tests cover:
- User creation with defaults
- Status transitions (activate, suspend)
- Permission checks based on role
- Login tracking and locking
- Password management
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects import AuthType, UserRole, UserStatus


class TestUserStatusEnum:
    """Tests for UserStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all required statuses are defined."""
        expected_statuses = {"ACTIVE", "SUSPENDED", "INACTIVE"}
        actual_statuses = {s.name for s in UserStatus}
        assert actual_statuses == expected_statuses


class TestUserRoleEnum:
    """Tests for UserRole enum."""

    def test_all_roles_defined(self) -> None:
        """Verify all required roles are defined."""
        expected_roles = {"ADMIN", "PROJECT_MANAGER", "ENGINEER", "VIEWER"}
        actual_roles = {r.name for r in UserRole}
        assert actual_roles == expected_roles


class TestAuthTypeEnum:
    """Tests for AuthType enum."""

    def test_all_auth_types_defined(self) -> None:
        """Verify all authentication types are defined."""
        expected_types = {"SSO", "LOCAL"}
        actual_types = {t.name for t in AuthType}
        assert actual_types == expected_types


class TestUserCreation:
    """Tests for User entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating user with only required fields."""
        user = User(id=1, username="testuser", email="test@example.com")
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_default_status_is_active(self) -> None:
        """Test default status is ACTIVE."""
        user = User(id=1, username="testuser", email="test@example.com")
        assert user.status == UserStatus.ACTIVE

    def test_default_role_is_engineer(self) -> None:
        """Test default role is ENGINEER."""
        user = User(id=1, username="testuser", email="test@example.com")
        assert user.role == UserRole.ENGINEER

    def test_default_auth_type_is_sso(self) -> None:
        """Test default auth type is SSO."""
        user = User(id=1, username="testuser", email="test@example.com")
        assert user.auth_type == AuthType.SSO

    def test_default_failed_login_count_is_zero(self) -> None:
        """Test default failed login count is 0."""
        user = User(id=1, username="testuser", email="test@example.com")
        assert user.failed_login_count == 0

    def test_create_with_all_optional_fields(self) -> None:
        """Test creating user with all fields."""
        user = User(
            id=1,
            username="admin",
            email="admin@example.com",
            status=UserStatus.ACTIVE,
            role=UserRole.ADMIN,
            display_name="Admin User",
            iam_identity_id="arn:aws:iam::123456789012:user/admin",
            iam_groups=["admins", "developers"],
            auth_type=AuthType.LOCAL,
        )
        assert user.display_name == "Admin User"
        assert user.role == UserRole.ADMIN
        assert user.iam_groups == ["admins", "developers"]
        assert user.auth_type == AuthType.LOCAL


class TestUserStatusMethods:
    """Tests for User status-related methods."""

    @pytest.fixture
    def user(self) -> User:
        """Create a basic user for testing."""
        return User(id=1, username="testuser", email="test@example.com")

    def test_is_active_when_active(self, user: User) -> None:
        """Test is_active returns True for ACTIVE status."""
        assert user.is_active()

    def test_is_active_when_suspended(self, user: User) -> None:
        """Test is_active returns False for SUSPENDED status."""
        user.suspend()
        assert not user.is_active()

    def test_suspend_changes_status(self, user: User) -> None:
        """Test suspend changes status to SUSPENDED."""
        assert user.status == UserStatus.ACTIVE
        user.suspend()
        assert user.status == UserStatus.SUSPENDED

    def test_activate_changes_status(self, user: User) -> None:
        """Test activate changes status to ACTIVE."""
        user.suspend()
        assert user.status == UserStatus.SUSPENDED
        user.activate()
        assert user.status == UserStatus.ACTIVE


class TestUserPermissions:
    """Tests for User permission methods."""

    def test_has_admin_privileges_for_admin(self) -> None:
        """Test has_admin_privileges returns True for ADMIN role."""
        user = User(id=1, username="admin", email="admin@example.com", role=UserRole.ADMIN)
        assert user.has_admin_privileges()

    def test_has_admin_privileges_for_engineer(self) -> None:
        """Test has_admin_privileges returns False for ENGINEER role."""
        user = User(id=1, username="engineer", email="eng@example.com", role=UserRole.ENGINEER)
        assert not user.has_admin_privileges()

    def test_can_create_training_job_when_active_engineer(self) -> None:
        """Test ENGINEER can create training jobs when active."""
        user = User(id=1, username="engineer", email="eng@example.com", role=UserRole.ENGINEER)
        assert user.can_create_training_job()

    def test_cannot_create_training_job_when_suspended(self) -> None:
        """Test user cannot create training jobs when suspended."""
        user = User(id=1, username="engineer", email="eng@example.com", role=UserRole.ENGINEER)
        user.suspend()
        assert not user.can_create_training_job()

    def test_viewer_cannot_create_training_job(self) -> None:
        """Test VIEWER cannot create training jobs."""
        user = User(id=1, username="viewer", email="viewer@example.com", role=UserRole.VIEWER)
        assert not user.can_create_training_job()

    def test_can_view_resources_when_active(self) -> None:
        """Test active user can view resources."""
        user = User(id=1, username="viewer", email="viewer@example.com", role=UserRole.VIEWER)
        assert user.can_view_resources()

    def test_cannot_view_resources_when_suspended(self) -> None:
        """Test suspended user cannot view resources."""
        user = User(id=1, username="viewer", email="viewer@example.com", role=UserRole.VIEWER)
        user.suspend()
        assert not user.can_view_resources()


class TestUserLoginTracking:
    """Tests for User login tracking methods."""

    @pytest.fixture
    def user(self) -> User:
        """Create a basic user for testing."""
        return User(id=1, username="testuser", email="test@example.com")

    def test_record_login_updates_timestamp(self, user: User) -> None:
        """Test record_login updates last_login_at."""
        assert user.last_login_at is None
        user.record_login()
        assert user.last_login_at is not None

    def test_record_failed_login_increments_count(self, user: User) -> None:
        """Test record_failed_login increments failed_login_count."""
        assert user.failed_login_count == 0
        user.record_failed_login()
        assert user.failed_login_count == 1
        user.record_failed_login()
        assert user.failed_login_count == 2

    def test_reset_login_failures_clears_count(self, user: User) -> None:
        """Test reset_login_failures resets failed_login_count to 0."""
        user.record_failed_login()
        user.record_failed_login()
        assert user.failed_login_count == 2
        user.reset_login_failures()
        assert user.failed_login_count == 0


class TestUserAccountLocking:
    """Tests for User account locking methods."""

    @pytest.fixture
    def user(self) -> User:
        """Create a basic user for testing."""
        return User(id=1, username="testuser", email="test@example.com")

    def test_is_locked_when_not_locked(self, user: User) -> None:
        """Test is_locked returns False when not locked."""
        assert not user.is_locked()

    def test_is_locked_when_locked(self, user: User) -> None:
        """Test is_locked returns True when locked."""
        future_time = datetime.now(UTC) + timedelta(hours=1)
        user.lock_account(future_time)
        assert user.is_locked()

    def test_is_locked_when_lock_expired(self, user: User) -> None:
        """Test is_locked returns False when lock has expired."""
        past_time = datetime.now(UTC) - timedelta(hours=1)
        user.lock_account(past_time)
        assert not user.is_locked()

    def test_reset_login_failures_unlocks_account(self, user: User) -> None:
        """Test reset_login_failures also unlocks account."""
        future_time = datetime.now(UTC) + timedelta(hours=1)
        user.lock_account(future_time)
        assert user.is_locked()
        user.reset_login_failures()
        assert not user.is_locked()


class TestUserPasswordManagement:
    """Tests for User password management methods."""

    @pytest.fixture
    def local_user(self) -> User:
        """Create a local auth user for testing."""
        return User(
            id=1,
            username="localuser",
            email="local@example.com",
            auth_type=AuthType.LOCAL,
        )

    def test_is_local_account_for_local_auth(self, local_user: User) -> None:
        """Test is_local_account returns True for LOCAL auth type."""
        assert local_user.is_local_account()

    def test_is_local_account_for_sso_auth(self) -> None:
        """Test is_local_account returns False for SSO auth type."""
        user = User(id=1, username="ssouser", email="sso@example.com")
        assert not user.is_local_account()

    def test_is_password_expired_when_not_set(self, local_user: User) -> None:
        """Test is_password_expired returns False when no expiration set."""
        assert not local_user.is_password_expired()

    def test_is_password_expired_when_expired(self, local_user: User) -> None:
        """Test is_password_expired returns True when password has expired."""
        past_time = datetime.now(UTC) - timedelta(days=1)
        local_user.password_expires_at = past_time
        assert local_user.is_password_expired()

    def test_is_password_expired_when_not_expired(self, local_user: User) -> None:
        """Test is_password_expired returns False when password is valid."""
        future_time = datetime.now(UTC) + timedelta(days=30)
        local_user.password_expires_at = future_time
        assert not local_user.is_password_expired()

    def test_update_password_sets_hash_and_expiration(self, local_user: User) -> None:
        """Test update_password sets password_hash and password_expires_at."""
        future_time = datetime.now(UTC) + timedelta(days=90)
        local_user.update_password("new_hash", future_time)
        assert local_user.password_hash == "new_hash"
        assert local_user.password_expires_at == future_time

    def test_update_password_resets_failed_count_and_lock(self, local_user: User) -> None:
        """Test update_password resets failed_login_count and locked_until."""
        local_user.record_failed_login()
        local_user.record_failed_login()
        lock_time = datetime.now(UTC) + timedelta(hours=1)
        local_user.lock_account(lock_time)

        future_time = datetime.now(UTC) + timedelta(days=90)
        local_user.update_password("new_hash", future_time)

        assert local_user.failed_login_count == 0
        assert local_user.locked_until is None
