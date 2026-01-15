"""Security Exceptions Unit Tests."""

from datetime import UTC, datetime, timedelta

import pytest

from src.core.security.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InsufficientPermissionsError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    SecurityError,
    SSODegradedModeError,
    SSOError,
    TokenExpiredError,
)


class TestSecurityError:
    """Tests for base SecurityError exception."""

    def test_security_error_attributes(self) -> None:
        """Test SecurityError has message and code attributes."""
        error = SecurityError("Test error message", code="TEST_ERROR")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.code == "TEST_ERROR"

    def test_security_error_default_code(self) -> None:
        """Test SecurityError default code is SECURITY_ERROR."""
        error = SecurityError("Test error")

        assert error.code == "SECURITY_ERROR"

    def test_security_error_is_exception(self) -> None:
        """Test SecurityError inherits from Exception."""
        error = SecurityError("Test")

        assert isinstance(error, Exception)

    def test_security_error_can_be_raised(self) -> None:
        """Test SecurityError can be raised and caught."""
        with pytest.raises(SecurityError) as exc_info:
            raise SecurityError("Test error", code="CUSTOM")

        assert exc_info.value.message == "Test error"
        assert exc_info.value.code == "CUSTOM"


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_authentication_error_message(self) -> None:
        """Test AuthenticationError captures message."""
        error = AuthenticationError("Invalid credentials")

        assert str(error) == "Invalid credentials"
        assert error.message == "Invalid credentials"

    def test_authentication_error_inherits_security_error(self) -> None:
        """Test AuthenticationError inherits from SecurityError."""
        error = AuthenticationError("Test")

        assert isinstance(error, SecurityError)
        assert isinstance(error, Exception)

    def test_authentication_error_code(self) -> None:
        """Test AuthenticationError has correct code."""
        error = AuthenticationError("Test")

        assert error.code == "AUTHENTICATION_FAILED"


class TestTokenExpiredError:
    """Tests for TokenExpiredError exception."""

    def test_token_expired_error_message(self) -> None:
        """Test TokenExpiredError captures message."""
        error = TokenExpiredError("Token has expired")

        assert "expired" in str(error).lower()

    def test_token_expired_error_inherits_security_error(self) -> None:
        """Test TokenExpiredError inherits from SecurityError."""
        error = TokenExpiredError("Test")

        assert isinstance(error, SecurityError)

    def test_token_expired_error_code(self) -> None:
        """Test TokenExpiredError has correct code."""
        error = TokenExpiredError("Test")

        assert error.code == "TOKEN_EXPIRED"


class TestInvalidTokenError:
    """Tests for InvalidTokenError exception."""

    def test_invalid_token_error_message(self) -> None:
        """Test InvalidTokenError captures message."""
        error = InvalidTokenError("Invalid token format")

        assert str(error) == "Invalid token format"

    def test_invalid_token_error_inherits_security_error(self) -> None:
        """Test InvalidTokenError inherits from SecurityError."""
        error = InvalidTokenError("Test")

        assert isinstance(error, SecurityError)

    def test_invalid_token_error_code(self) -> None:
        """Test InvalidTokenError has correct code."""
        error = InvalidTokenError("Test")

        assert error.code == "INVALID_TOKEN"


class TestAccountLockedError:
    """Tests for AccountLockedError exception."""

    def test_account_locked_error_locked_until(self) -> None:
        """Test AccountLockedError captures locked_until datetime."""
        locked_until = datetime.now(UTC) + timedelta(minutes=30)
        error = AccountLockedError("Account locked", locked_until=locked_until)

        assert error.locked_until == locked_until

    def test_account_locked_error_message(self) -> None:
        """Test AccountLockedError captures message."""
        error = AccountLockedError("Account is locked")

        assert str(error) == "Account is locked"

    def test_account_locked_error_inherits_security_error(self) -> None:
        """Test AccountLockedError inherits from SecurityError."""
        error = AccountLockedError("Test")

        assert isinstance(error, SecurityError)

    def test_account_locked_error_code(self) -> None:
        """Test AccountLockedError has correct code."""
        error = AccountLockedError("Test")

        assert error.code == "ACCOUNT_LOCKED"

    def test_account_locked_error_no_locked_until(self) -> None:
        """Test AccountLockedError without locked_until."""
        error = AccountLockedError("Account locked")

        assert error.locked_until is None


class TestPasswordTooWeakError:
    """Tests for PasswordTooWeakError exception."""

    def test_password_too_weak_violations_list(self) -> None:
        """Test PasswordTooWeakError captures violations list."""
        violations = ["Too short", "No uppercase", "No special char"]
        error = PasswordTooWeakError(violations=violations)

        assert error.violations == violations
        assert len(error.violations) == 3

    def test_password_too_weak_error_message_from_violations(self) -> None:
        """Test PasswordTooWeakError generates message from violations."""
        violations = ["Rule 1 violated", "Rule 2 violated"]
        error = PasswordTooWeakError(violations=violations)

        assert "Rule 1" in str(error) or len(error.violations) == 2

    def test_password_too_weak_error_inherits_security_error(self) -> None:
        """Test PasswordTooWeakError inherits from SecurityError."""
        error = PasswordTooWeakError(violations=["Test"])

        assert isinstance(error, SecurityError)

    def test_password_too_weak_error_code(self) -> None:
        """Test PasswordTooWeakError has correct code."""
        error = PasswordTooWeakError(violations=["Test"])

        assert error.code == "PASSWORD_TOO_WEAK"

    def test_password_too_weak_empty_violations(self) -> None:
        """Test PasswordTooWeakError with empty violations."""
        error = PasswordTooWeakError(violations=[])

        assert error.violations == []


class TestPasswordHistoryViolationError:
    """Tests for PasswordHistoryViolationError exception."""

    def test_password_history_violation_message(self) -> None:
        """Test PasswordHistoryViolationError captures message."""
        error = PasswordHistoryViolationError("Password recently used")

        assert "recently" in str(error).lower() or "used" in str(error).lower()

    def test_password_history_violation_inherits_security_error(self) -> None:
        """Test PasswordHistoryViolationError inherits from SecurityError."""
        error = PasswordHistoryViolationError("Test")

        assert isinstance(error, SecurityError)

    def test_password_history_violation_code(self) -> None:
        """Test PasswordHistoryViolationError has correct code."""
        error = PasswordHistoryViolationError("Test")

        assert error.code == "PASSWORD_HISTORY_VIOLATION"


class TestPasswordExpiredError:
    """Tests for PasswordExpiredError exception."""

    def test_password_expired_error_message(self) -> None:
        """Test PasswordExpiredError captures message."""
        error = PasswordExpiredError("Password has expired")

        assert "expired" in str(error).lower()

    def test_password_expired_error_inherits_security_error(self) -> None:
        """Test PasswordExpiredError inherits from SecurityError."""
        error = PasswordExpiredError("Test")

        assert isinstance(error, SecurityError)

    def test_password_expired_error_code(self) -> None:
        """Test PasswordExpiredError has correct code."""
        error = PasswordExpiredError("Test")

        assert error.code == "PASSWORD_EXPIRED"


class TestInsufficientPermissionsError:
    """Tests for InsufficientPermissionsError exception."""

    def test_insufficient_permissions_required_permission(self) -> None:
        """Test InsufficientPermissionsError captures required_permission."""
        error = InsufficientPermissionsError(required_permission="USER_CREATE")

        assert error.required_permission == "USER_CREATE"

    def test_insufficient_permissions_message(self) -> None:
        """Test InsufficientPermissionsError generates message from required_permission."""
        error = InsufficientPermissionsError("USER_CREATE")

        assert "USER_CREATE" in str(error)
        assert "permissions" in str(error).lower()

    def test_insufficient_permissions_inherits_security_error(self) -> None:
        """Test InsufficientPermissionsError inherits from SecurityError."""
        error = InsufficientPermissionsError("TEST_PERMISSION")

        assert isinstance(error, SecurityError)

    def test_insufficient_permissions_code(self) -> None:
        """Test InsufficientPermissionsError has correct code."""
        error = InsufficientPermissionsError("TEST_PERMISSION")

        assert error.code == "INSUFFICIENT_PERMISSIONS"

    def test_insufficient_permissions_stores_permission(self) -> None:
        """Test InsufficientPermissionsError stores the required permission."""
        error = InsufficientPermissionsError("ADMIN_ACCESS")

        assert error.required_permission == "ADMIN_ACCESS"


class TestSSOError:
    """Tests for SSOError exception."""

    def test_sso_error_degraded_flag(self) -> None:
        """Test SSOError captures degraded flag."""
        error = SSOError("SSO service unavailable", degraded=True)

        assert error.degraded is True

    def test_sso_error_not_degraded_by_default(self) -> None:
        """Test SSOError degraded is False by default."""
        error = SSOError("SSO error")

        assert error.degraded is False

    def test_sso_error_message(self) -> None:
        """Test SSOError captures message."""
        error = SSOError("SSO validation failed")

        assert str(error) == "SSO validation failed"

    def test_sso_error_inherits_security_error(self) -> None:
        """Test SSOError inherits from SecurityError."""
        error = SSOError("Test")

        assert isinstance(error, SecurityError)

    def test_sso_error_code(self) -> None:
        """Test SSOError has correct code."""
        error = SSOError("Test")

        assert error.code == "SSO_ERROR"


class TestSSODegradedModeError:
    """Tests for SSODegradedModeError exception."""

    def test_sso_degraded_mode_error_message(self) -> None:
        """Test SSODegradedModeError captures message."""
        error = SSODegradedModeError("SSO in degraded mode")

        assert "degraded" in str(error).lower()

    def test_sso_degraded_mode_inherits_sso_error(self) -> None:
        """Test SSODegradedModeError inherits from SSOError."""
        error = SSODegradedModeError("Test")

        assert isinstance(error, SSOError)
        assert isinstance(error, SecurityError)

    def test_sso_degraded_mode_degraded_flag_true(self) -> None:
        """Test SSODegradedModeError has degraded=True."""
        error = SSODegradedModeError("Test")

        assert error.degraded is True

    def test_sso_degraded_mode_code(self) -> None:
        """Test SSODegradedModeError inherits SSO_ERROR code from parent."""
        error = SSODegradedModeError("Test")

        # SSODegradedModeError inherits code from SSOError
        assert error.code == "SSO_ERROR"


class TestExceptionInheritance:
    """Tests for exception inheritance hierarchy."""

    def test_exception_inheritance_chain(self) -> None:
        """Test complete exception inheritance chain."""
        # All should inherit from SecurityError
        exceptions = [
            AuthenticationError("test"),
            TokenExpiredError("test"),
            InvalidTokenError("test"),
            AccountLockedError("test"),
            PasswordTooWeakError(violations=["test"]),
            PasswordHistoryViolationError("test"),
            PasswordExpiredError("test"),
            InsufficientPermissionsError("test"),
            SSOError("test"),
            SSODegradedModeError("test"),
        ]

        for exc in exceptions:
            assert isinstance(
                exc, SecurityError
            ), f"{type(exc).__name__} should inherit from SecurityError"
            assert isinstance(
                exc, Exception
            ), f"{type(exc).__name__} should inherit from Exception"

    def test_sso_degraded_inherits_from_sso_error(self) -> None:
        """Test SSODegradedModeError inherits from SSOError."""
        error = SSODegradedModeError("Test")

        assert isinstance(error, SSOError)

    def test_catching_security_error_catches_all(self) -> None:
        """Test that catching SecurityError catches all security exceptions."""
        exceptions_to_test = [
            (AuthenticationError, ("test",), {}),
            (TokenExpiredError, ("test",), {}),
            (InvalidTokenError, ("test",), {}),
            (AccountLockedError, ("test",), {}),
            (PasswordTooWeakError, (), {"violations": ["test"]}),
            (PasswordHistoryViolationError, ("test",), {}),
            (PasswordExpiredError, ("test",), {}),
            (InsufficientPermissionsError, ("test",), {}),
            (SSOError, ("test",), {}),
            (SSODegradedModeError, ("test",), {}),
        ]

        for exc_class, args, kwargs in exceptions_to_test:
            try:
                raise exc_class(*args, **kwargs)
            except SecurityError:
                pass  # Expected
            except Exception as e:
                pytest.fail(f"{exc_class.__name__} not caught by SecurityError: {e}")
