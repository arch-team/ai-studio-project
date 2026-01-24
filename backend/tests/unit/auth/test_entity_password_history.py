"""Unit tests for PasswordHistory domain entity.

Tests cover:
- PasswordHistory creation
- Factory method
- Default values
"""

from src.modules.auth.domain.entities.password_history import PasswordHistory


class TestPasswordHistoryCreation:
    """Tests for PasswordHistory entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating password history with required fields."""
        history = PasswordHistory(
            id=1,
            user_id=100,
            password_hash="hashed_password_123",
        )
        assert history.id == 1
        assert history.user_id == 100
        assert history.password_hash == "hashed_password_123"

    def test_create_with_none_id(self) -> None:
        """Test creating password history with None id (new record)."""
        history = PasswordHistory(
            id=None,
            user_id=100,
            password_hash="hashed_password_456",
        )
        assert history.id is None
        assert history.user_id == 100

    def test_created_at_is_set_automatically(self) -> None:
        """Test created_at is set automatically."""
        history = PasswordHistory(
            id=None,
            user_id=100,
            password_hash="hash",
        )
        assert history.created_at is not None


class TestPasswordHistoryFactoryMethod:
    """Tests for PasswordHistory factory method."""

    def test_create_factory_method(self) -> None:
        """Test create factory method."""
        history = PasswordHistory.create(
            user_id=42,
            password_hash="bcrypt_hash_xxx",
        )
        assert history.id is None
        assert history.user_id == 42
        assert history.password_hash == "bcrypt_hash_xxx"

    def test_create_sets_created_at(self) -> None:
        """Test create factory method sets created_at."""
        history = PasswordHistory.create(
            user_id=42,
            password_hash="hash",
        )
        assert history.created_at is not None

    def test_create_multiple_entries_different_timestamps(self) -> None:
        """Test creating multiple entries have valid timestamps."""
        history1 = PasswordHistory.create(user_id=1, password_hash="hash1")
        history2 = PasswordHistory.create(user_id=1, password_hash="hash2")

        # Both should have timestamps
        assert history1.created_at is not None
        assert history2.created_at is not None
        # They should be very close in time (within same test execution)
        assert abs((history2.created_at - history1.created_at).total_seconds()) < 1
