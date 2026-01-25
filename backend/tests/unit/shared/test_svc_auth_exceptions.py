"""Security Exceptions Unit Tests.

测试说明:
---------
所有安全异常现在都继承自 Problem 基类。
SecurityError 是 Problem 的别名，用于向后兼容。
异常使用 error_code 类属性（而非旧的 code 实例属性）。
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.shared.domain.problem import Problem
from src.shared.infrastructure.security.exceptions import (
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
    """Tests for base SecurityError (now alias to Problem)."""

    def test_security_error_is_problem_alias(self) -> None:
        """Test SecurityError is an alias to Problem."""
        assert SecurityError is Problem

    def test_security_error_is_exception(self) -> None:
        """Test SecurityError inherits from Exception."""
        error = Problem()

        assert isinstance(error, Exception)

    def test_security_error_can_be_raised(self) -> None:
        """Test SecurityError can be raised and caught."""
        # 使用具体的异常子类来测试
        with pytest.raises(Problem) as exc_info:
            raise AuthenticationError()

        assert exc_info.value.error_code == "AUTHENTICATION_FAILED"


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_authentication_error_message(self) -> None:
        """Test AuthenticationError captures message."""
        error = AuthenticationError(message="Invalid credentials")

        assert str(error) == "Invalid credentials"
        assert error.message == "Invalid credentials"

    def test_authentication_error_default_message(self) -> None:
        """Test AuthenticationError has default message."""
        error = AuthenticationError()

        assert error.message == "Authentication failed"

    def test_authentication_error_inherits_problem(self) -> None:
        """Test AuthenticationError inherits from Problem."""
        error = AuthenticationError()

        assert isinstance(error, Problem)
        assert isinstance(error, Exception)

    def test_authentication_error_code(self) -> None:
        """Test AuthenticationError has correct error_code."""
        assert AuthenticationError.error_code == "AUTHENTICATION_FAILED"


class TestTokenExpiredError:
    """Tests for TokenExpiredError exception."""

    def test_token_expired_error_message(self) -> None:
        """Test TokenExpiredError captures message."""
        error = TokenExpiredError(message="Token has expired")

        assert "expired" in str(error).lower()

    def test_token_expired_error_default_message(self) -> None:
        """Test TokenExpiredError has default message."""
        error = TokenExpiredError()

        assert error.message == "Token has expired"

    def test_token_expired_error_inherits_problem(self) -> None:
        """Test TokenExpiredError inherits from Problem."""
        error = TokenExpiredError()

        assert isinstance(error, Problem)

    def test_token_expired_error_code(self) -> None:
        """Test TokenExpiredError has correct error_code."""
        assert TokenExpiredError.error_code == "TOKEN_EXPIRED"


class TestInvalidTokenError:
    """Tests for InvalidTokenError exception."""

    def test_invalid_token_error_message(self) -> None:
        """Test InvalidTokenError captures message."""
        error = InvalidTokenError(message="Invalid token format")

        assert str(error) == "Invalid token format"

    def test_invalid_token_error_default_message(self) -> None:
        """Test InvalidTokenError has default message."""
        error = InvalidTokenError()

        assert error.message == "Invalid token"

    def test_invalid_token_error_inherits_problem(self) -> None:
        """Test InvalidTokenError inherits from Problem."""
        error = InvalidTokenError()

        assert isinstance(error, Problem)

    def test_invalid_token_error_code(self) -> None:
        """Test InvalidTokenError has correct error_code."""
        assert InvalidTokenError.error_code == "INVALID_TOKEN"


class TestAccountLockedError:
    """Tests for AccountLockedError exception."""

    def test_account_locked_error_locked_until(self) -> None:
        """Test AccountLockedError captures locked_until datetime."""
        locked_until = (datetime.now(UTC) + timedelta(minutes=30)).isoformat()
        error = AccountLockedError(locked_until=locked_until)

        assert error.locked_until == locked_until

    def test_account_locked_error_message(self) -> None:
        """Test AccountLockedError captures message."""
        error = AccountLockedError(message="Account is locked")

        assert str(error) == "Account is locked"

    def test_account_locked_error_inherits_problem(self) -> None:
        """Test AccountLockedError inherits from Problem."""
        error = AccountLockedError()

        assert isinstance(error, Problem)

    def test_account_locked_error_code(self) -> None:
        """Test AccountLockedError has correct error_code."""
        assert AccountLockedError.error_code == "ACCOUNT_LOCKED"

    def test_account_locked_error_no_locked_until(self) -> None:
        """Test AccountLockedError without locked_until."""
        error = AccountLockedError()

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

        assert "Rule 1" in str(error) and "Rule 2" in str(error)

    def test_password_too_weak_error_inherits_problem(self) -> None:
        """Test PasswordTooWeakError inherits from Problem."""
        error = PasswordTooWeakError(violations=["Test"])

        assert isinstance(error, Problem)

    def test_password_too_weak_error_code(self) -> None:
        """Test PasswordTooWeakError has correct error_code."""
        assert PasswordTooWeakError.error_code == "PASSWORD_TOO_WEAK"

    def test_password_too_weak_empty_violations(self) -> None:
        """Test PasswordTooWeakError with empty violations."""
        error = PasswordTooWeakError(violations=[])

        assert error.violations == []


class TestPasswordHistoryViolationError:
    """Tests for PasswordHistoryViolationError exception."""

    def test_password_history_violation_message(self) -> None:
        """Test PasswordHistoryViolationError captures message."""
        error = PasswordHistoryViolationError(message="Password recently used")

        assert "recently" in str(error).lower() or "used" in str(error).lower()

    def test_password_history_violation_default_message(self) -> None:
        """Test PasswordHistoryViolationError has default message."""
        error = PasswordHistoryViolationError()

        assert "reuse" in error.message.lower() or "recent" in error.message.lower()

    def test_password_history_violation_inherits_problem(self) -> None:
        """Test PasswordHistoryViolationError inherits from Problem."""
        error = PasswordHistoryViolationError()

        assert isinstance(error, Problem)

    def test_password_history_violation_code(self) -> None:
        """Test PasswordHistoryViolationError has correct error_code."""
        assert PasswordHistoryViolationError.error_code == "PASSWORD_HISTORY_VIOLATION"


class TestPasswordExpiredError:
    """Tests for PasswordExpiredError exception."""

    def test_password_expired_error_message(self) -> None:
        """Test PasswordExpiredError captures message."""
        error = PasswordExpiredError(message="Password has expired")

        assert "expired" in str(error).lower()

    def test_password_expired_error_default_message(self) -> None:
        """Test PasswordExpiredError has default message."""
        error = PasswordExpiredError()

        assert "expired" in error.message.lower()

    def test_password_expired_error_inherits_problem(self) -> None:
        """Test PasswordExpiredError inherits from Problem."""
        error = PasswordExpiredError()

        assert isinstance(error, Problem)

    def test_password_expired_error_code(self) -> None:
        """Test PasswordExpiredError has correct error_code."""
        assert PasswordExpiredError.error_code == "PASSWORD_EXPIRED"


class TestInsufficientPermissionsError:
    """Tests for InsufficientPermissionsError exception."""

    def test_insufficient_permissions_required_permission(self) -> None:
        """Test InsufficientPermissionsError captures required_permission."""
        error = InsufficientPermissionsError(required_permission="USER_CREATE")

        assert error.required_permission == "USER_CREATE"

    def test_insufficient_permissions_message(self) -> None:
        """Test InsufficientPermissionsError generates message from required_permission."""
        error = InsufficientPermissionsError(required_permission="USER_CREATE")

        assert "USER_CREATE" in str(error)
        assert "permissions" in str(error).lower()

    def test_insufficient_permissions_inherits_problem(self) -> None:
        """Test InsufficientPermissionsError inherits from Problem."""
        error = InsufficientPermissionsError(required_permission="TEST_PERMISSION")

        assert isinstance(error, Problem)

    def test_insufficient_permissions_code(self) -> None:
        """Test InsufficientPermissionsError has correct error_code."""
        assert InsufficientPermissionsError.error_code == "INSUFFICIENT_PERMISSIONS"

    def test_insufficient_permissions_stores_permission(self) -> None:
        """Test InsufficientPermissionsError stores the required permission."""
        error = InsufficientPermissionsError(required_permission="ADMIN_ACCESS")

        assert error.required_permission == "ADMIN_ACCESS"


class TestSSOError:
    """Tests for SSOError exception."""

    def test_sso_error_degraded_flag(self) -> None:
        """Test SSOError captures degraded flag."""
        error = SSOError(message="SSO service unavailable", degraded=True)

        assert error.degraded is True

    def test_sso_error_not_degraded_by_default(self) -> None:
        """Test SSOError degraded is False by default."""
        error = SSOError()

        assert error.degraded is False

    def test_sso_error_message(self) -> None:
        """Test SSOError captures message."""
        error = SSOError(message="SSO validation failed")

        assert str(error) == "SSO validation failed"

    def test_sso_error_default_message(self) -> None:
        """Test SSOError has default message."""
        error = SSOError()

        assert "SSO" in error.message or "authentication" in error.message.lower()

    def test_sso_error_inherits_problem(self) -> None:
        """Test SSOError inherits from Problem."""
        error = SSOError()

        assert isinstance(error, Problem)

    def test_sso_error_code(self) -> None:
        """Test SSOError has correct error_code."""
        assert SSOError.error_code == "SSO_ERROR"


class TestSSODegradedModeError:
    """Tests for SSODegradedModeError exception."""

    def test_sso_degraded_mode_error_message(self) -> None:
        """Test SSODegradedModeError captures message."""
        error = SSODegradedModeError(message="SSO in degraded mode")

        assert "degraded" in str(error).lower()

    def test_sso_degraded_mode_inherits_problem(self) -> None:
        """Test SSODegradedModeError inherits from Problem."""
        error = SSODegradedModeError()

        assert isinstance(error, Problem)

    def test_sso_degraded_mode_code(self) -> None:
        """Test SSODegradedModeError has correct error_code."""
        assert SSODegradedModeError.error_code == "SSO_DEGRADED_MODE"


class TestExceptionInheritance:
    """Tests for exception inheritance hierarchy."""

    def test_exception_inheritance_chain(self) -> None:
        """Test complete exception inheritance chain."""
        # All should inherit from Problem
        exceptions = [
            AuthenticationError(),
            TokenExpiredError(),
            InvalidTokenError(),
            AccountLockedError(),
            PasswordTooWeakError(violations=["test"]),
            PasswordHistoryViolationError(),
            PasswordExpiredError(),
            InsufficientPermissionsError(required_permission="test"),
            SSOError(),
            SSODegradedModeError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, Problem), f"{type(exc).__name__} should inherit from Problem"
            assert isinstance(exc, Exception), f"{type(exc).__name__} should inherit from Exception"

    def test_catching_problem_catches_all(self) -> None:
        """Test that catching Problem catches all security exceptions."""
        exceptions_to_test = [
            (AuthenticationError, (), {}),
            (TokenExpiredError, (), {}),
            (InvalidTokenError, (), {}),
            (AccountLockedError, (), {}),
            (PasswordTooWeakError, (), {"violations": ["test"]}),
            (PasswordHistoryViolationError, (), {}),
            (PasswordExpiredError, (), {}),
            (InsufficientPermissionsError, (), {"required_permission": "test"}),
            (SSOError, (), {}),
            (SSODegradedModeError, (), {}),
        ]

        for exc_class, args, kwargs in exceptions_to_test:
            try:
                raise exc_class(*args, **kwargs)
            except Problem:
                pass  # Expected
            except Exception as e:
                pytest.fail(f"{exc_class.__name__} not caught by Problem: {e}")
