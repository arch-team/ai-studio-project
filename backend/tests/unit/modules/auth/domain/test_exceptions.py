"""Auth domain exceptions unit tests.

测试说明:
---------
所有 auth 异常现在都继承自 Problem 基类。
SecurityError 是 Problem 的别名，用于向后兼容。
异常使用 error_code 类属性（而非旧的 code 实例属性）。
"""

import pytest
from fastapi import status

from src.shared.domain.problem import Problem
from src.modules.auth.domain.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    AuthError,
    InsufficientPermissionsError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    SecurityError,
    SSODegradedModeError,
    SSOError,
    TokenError,
    TokenExpiredError,
    UserNotFoundError,
)


class TestAuthErrorInheritance:
    """验证 AuthError 继承自 Problem"""

    def test_auth_error_inherits_problem(self):
        exc = AuthError()
        assert isinstance(exc, Problem)

    def test_auth_error_has_message_attribute(self):
        exc = AuthError(message="test message")
        assert exc.message == "test message"

    def test_auth_error_has_error_code(self):
        assert AuthError.error_code == "AUTH_ERROR"


class TestUserNotFoundError:
    """UserNotFoundError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = UserNotFoundError(user_id="user123")
        assert isinstance(exc, Problem)

    def test_stores_user_id(self):
        exc = UserNotFoundError(user_id="user123")
        assert exc.user_id == "user123"

    def test_integer_user_id(self):
        exc = UserNotFoundError(user_id=123)
        assert exc.user_id == 123

    def test_error_code(self):
        assert UserNotFoundError.error_code == "USER_NOT_FOUND"

    def test_message_format(self):
        exc = UserNotFoundError(user_id="user123")
        assert "user123" in exc.message


class TestInvalidCredentialsError:
    """InvalidCredentialsError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = InvalidCredentialsError()
        assert isinstance(exc, Problem)

    def test_default_message(self):
        exc = InvalidCredentialsError()
        assert exc.message == "Invalid username or password"

    def test_custom_message(self):
        exc = InvalidCredentialsError(message="Wrong password")
        assert exc.message == "Wrong password"

    def test_error_code(self):
        assert InvalidCredentialsError.error_code == "INVALID_CREDENTIALS"


class TestAccountLockedError:
    """AccountLockedError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = AccountLockedError()
        assert isinstance(exc, Problem)

    def test_locked_until_attribute(self):
        exc = AccountLockedError(locked_until="2025-01-26T12:00:00Z")
        assert exc.locked_until == "2025-01-26T12:00:00Z"

    def test_locked_until_none(self):
        exc = AccountLockedError()
        assert exc.locked_until is None

    def test_message_without_locked_until(self):
        exc = AccountLockedError()
        assert exc.message == "Account is locked"

    def test_error_code(self):
        assert AccountLockedError.error_code == "ACCOUNT_LOCKED"


class TestAccountInactiveError:
    """AccountInactiveError 测试 (auth 模块独有)"""

    def test_inherits_problem(self):
        exc = AccountInactiveError()
        assert isinstance(exc, Problem)

    def test_default_message(self):
        exc = AccountInactiveError()
        assert exc.message == "Account is not active"

    def test_error_code(self):
        assert AccountInactiveError.error_code == "ACCOUNT_INACTIVE"


class TestPasswordExpiredError:
    """PasswordExpiredError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = PasswordExpiredError()
        assert isinstance(exc, Problem)

    def test_default_message(self):
        exc = PasswordExpiredError()
        assert exc.message == "Password has expired"

    def test_error_code(self):
        assert PasswordExpiredError.error_code == "PASSWORD_EXPIRED"


class TestPasswordTooWeakError:
    """PasswordTooWeakError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = PasswordTooWeakError(violations=["too short"])
        assert isinstance(exc, Problem)

    def test_violations_attribute(self):
        violations = ["too short", "no uppercase"]
        exc = PasswordTooWeakError(violations=violations)
        assert exc.violations == violations

    def test_message_contains_violations(self):
        exc = PasswordTooWeakError(violations=["too short", "no number"])
        assert "too short" in exc.message
        assert "no number" in exc.message

    def test_error_code(self):
        assert PasswordTooWeakError.error_code == "PASSWORD_TOO_WEAK"


class TestPasswordHistoryViolationError:
    """PasswordHistoryViolationError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = PasswordHistoryViolationError()
        assert isinstance(exc, Problem)

    def test_default_message(self):
        exc = PasswordHistoryViolationError()
        assert exc.message == "Cannot reuse recent passwords"

    def test_error_code(self):
        assert PasswordHistoryViolationError.error_code == "PASSWORD_HISTORY_VIOLATION"


class TestTokenError:
    """TokenError 测试 (auth 模块独有基类)"""

    def test_inherits_problem(self):
        exc = TokenError()
        assert isinstance(exc, Problem)

    def test_error_code(self):
        assert TokenError.error_code == "TOKEN_ERROR"


class TestInvalidTokenError:
    """InvalidTokenError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = InvalidTokenError()
        assert isinstance(exc, Problem)

    def test_default_message(self):
        exc = InvalidTokenError()
        assert exc.message == "Invalid token"

    def test_error_code(self):
        assert InvalidTokenError.error_code == "INVALID_TOKEN"


class TestTokenExpiredError:
    """TokenExpiredError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = TokenExpiredError()
        assert isinstance(exc, Problem)

    def test_default_message(self):
        exc = TokenExpiredError()
        assert exc.message == "Token has expired"

    def test_error_code(self):
        assert TokenExpiredError.error_code == "TOKEN_EXPIRED"


class TestInsufficientPermissionsError:
    """InsufficientPermissionsError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = InsufficientPermissionsError(required_permission="admin")
        assert isinstance(exc, Problem)

    def test_required_permission_attribute(self):
        exc = InsufficientPermissionsError(required_permission="admin")
        assert exc.required_permission == "admin"

    def test_message_contains_permission(self):
        exc = InsufficientPermissionsError(required_permission="admin")
        assert "admin" in exc.message

    def test_error_code(self):
        assert InsufficientPermissionsError.error_code == "INSUFFICIENT_PERMISSIONS"


class TestSSOError:
    """SSOError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = SSOError()
        assert isinstance(exc, Problem)

    def test_error_code(self):
        assert SSOError.error_code == "SSO_ERROR"


class TestSSODegradedModeError:
    """SSODegradedModeError 测试 (重导出自 shared/security)"""

    def test_inherits_problem(self):
        exc = SSODegradedModeError()
        assert isinstance(exc, Problem)

    def test_default_message(self):
        exc = SSODegradedModeError()
        assert exc.message == "SSO service is temporarily unavailable"

    def test_error_code(self):
        assert SSODegradedModeError.error_code == "SSO_DEGRADED_MODE"


class TestAuthExceptionsHttpStatus:
    """验证 auth 异常的 http_status 类属性"""

    @pytest.mark.parametrize(
        "exception_class,expected_status",
        [
            (AuthError, status.HTTP_401_UNAUTHORIZED),
            (InvalidCredentialsError, status.HTTP_401_UNAUTHORIZED),
            (UserNotFoundError, status.HTTP_404_NOT_FOUND),
            (TokenExpiredError, status.HTTP_401_UNAUTHORIZED),
            (InvalidTokenError, status.HTTP_401_UNAUTHORIZED),
            (AccountLockedError, status.HTTP_423_LOCKED),
            (AccountInactiveError, status.HTTP_401_UNAUTHORIZED),
            (PasswordExpiredError, status.HTTP_401_UNAUTHORIZED),
            (PasswordTooWeakError, status.HTTP_400_BAD_REQUEST),
            (PasswordHistoryViolationError, status.HTTP_400_BAD_REQUEST),
            (InsufficientPermissionsError, status.HTTP_403_FORBIDDEN),
            (SSOError, status.HTTP_401_UNAUTHORIZED),
            (SSODegradedModeError, status.HTTP_503_SERVICE_UNAVAILABLE),
        ],
    )
    def test_exception_has_correct_http_status(self, exception_class, expected_status):
        """验证每个 auth 异常类的 http_status 属性正确"""
        assert exception_class.http_status == expected_status, (
            f"{exception_class.__name__}.http_status should be {expected_status}, "
            f"but got {exception_class.http_status}"
        )


class TestCatchingAuthExceptions:
    """验证可以用 Problem 统一捕获"""

    def test_catch_all_with_problem(self):
        """所有 auth 异常都能被 Problem 捕获"""
        exceptions = [
            InvalidCredentialsError(),
            UserNotFoundError(user_id="test"),
            AccountLockedError(),
            TokenExpiredError(),
            InsufficientPermissionsError(required_permission="admin"),
            SSODegradedModeError(),
            # Auth 独有异常
            AuthError(),
            AccountInactiveError(),
            TokenError(),
        ]

        for exc in exceptions:
            try:
                raise exc
            except Problem as caught:
                assert caught is exc
            else:
                pytest.fail(f"{type(exc).__name__} was not caught by Problem")

    def test_security_error_is_problem_alias(self):
        """SecurityError 是 Problem 的别名"""
        assert SecurityError is Problem
