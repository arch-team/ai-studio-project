"""Unit tests for LoginAttempt domain entity.

Tests cover:
- LoginAttempt creation
- Factory methods for success/failure
- Attribute validation
"""

import pytest

from src.modules.auth.domain.entities.login_attempt import LoginAttempt


class TestLoginAttemptCreation:
    """Tests for LoginAttempt entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating login attempt with required fields."""
        attempt = LoginAttempt(
            id=1,
            username="testuser",
            ip_address="192.168.1.1",
            success=True,
        )
        assert attempt.id == 1
        assert attempt.username == "testuser"
        assert attempt.ip_address == "192.168.1.1"
        assert attempt.success is True

    def test_create_with_all_fields(self) -> None:
        """Test creating login attempt with all fields."""
        attempt = LoginAttempt(
            id=1,
            username="testuser",
            ip_address="192.168.1.1",
            success=False,
            user_id=100,
            user_agent="Mozilla/5.0",
            failure_reason="Invalid password",
        )
        assert attempt.user_id == 100
        assert attempt.user_agent == "Mozilla/5.0"
        assert attempt.failure_reason == "Invalid password"

    def test_default_optional_fields_are_none(self) -> None:
        """Test default optional fields are None."""
        attempt = LoginAttempt(
            id=None,
            username="testuser",
            ip_address="192.168.1.1",
            success=True,
        )
        assert attempt.user_id is None
        assert attempt.user_agent is None
        assert attempt.failure_reason is None

    def test_created_at_is_set_automatically(self) -> None:
        """Test created_at is set automatically."""
        attempt = LoginAttempt(
            id=None,
            username="testuser",
            ip_address="192.168.1.1",
            success=True,
        )
        assert attempt.created_at is not None


class TestLoginAttemptFactoryMethods:
    """Tests for LoginAttempt factory methods."""

    def test_create_failed_sets_correct_attributes(self) -> None:
        """Test create_failed factory method."""
        attempt = LoginAttempt.create_failed(
            username="testuser",
            ip_address="10.0.0.1",
            failure_reason="Invalid credentials",
            user_id=None,
            user_agent="curl/7.68.0",
        )
        assert attempt.id is None
        assert attempt.username == "testuser"
        assert attempt.ip_address == "10.0.0.1"
        assert attempt.success is False
        assert attempt.failure_reason == "Invalid credentials"
        assert attempt.user_agent == "curl/7.68.0"
        assert attempt.user_id is None

    def test_create_failed_with_user_id(self) -> None:
        """Test create_failed with known user_id."""
        attempt = LoginAttempt.create_failed(
            username="knownuser",
            ip_address="10.0.0.1",
            failure_reason="Account locked",
            user_id=42,
        )
        assert attempt.user_id == 42
        assert attempt.success is False

    def test_create_successful_sets_correct_attributes(self) -> None:
        """Test create_successful factory method."""
        attempt = LoginAttempt.create_successful(
            username="testuser",
            ip_address="192.168.1.100",
            user_id=123,
            user_agent="Chrome/120.0",
        )
        assert attempt.id is None
        assert attempt.username == "testuser"
        assert attempt.ip_address == "192.168.1.100"
        assert attempt.success is True
        assert attempt.user_id == 123
        assert attempt.user_agent == "Chrome/120.0"
        assert attempt.failure_reason is None

    def test_create_successful_without_user_agent(self) -> None:
        """Test create_successful without user_agent."""
        attempt = LoginAttempt.create_successful(
            username="testuser",
            ip_address="192.168.1.100",
            user_id=123,
        )
        assert attempt.user_agent is None
        assert attempt.success is True


class TestLoginAttemptAttributes:
    """Tests for LoginAttempt attribute behaviors."""

    @pytest.fixture
    def failed_attempt(self) -> LoginAttempt:
        """Create a failed login attempt for testing."""
        return LoginAttempt.create_failed(
            username="baduser",
            ip_address="10.10.10.10",
            failure_reason="Too many attempts",
        )

    @pytest.fixture
    def successful_attempt(self) -> LoginAttempt:
        """Create a successful login attempt for testing."""
        return LoginAttempt.create_successful(
            username="gooduser",
            ip_address="192.168.0.1",
            user_id=1,
        )

    def test_failed_attempt_has_failure_reason(
        self, failed_attempt: LoginAttempt
    ) -> None:
        """Test failed attempt has failure_reason set."""
        assert failed_attempt.failure_reason is not None
        assert failed_attempt.failure_reason == "Too many attempts"

    def test_successful_attempt_has_no_failure_reason(
        self, successful_attempt: LoginAttempt
    ) -> None:
        """Test successful attempt has no failure_reason."""
        assert successful_attempt.failure_reason is None

    def test_successful_attempt_has_user_id(
        self, successful_attempt: LoginAttempt
    ) -> None:
        """Test successful attempt always has user_id."""
        assert successful_attempt.user_id is not None
        assert successful_attempt.user_id == 1
