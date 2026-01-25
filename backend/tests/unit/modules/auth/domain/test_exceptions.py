"""Auth domain exceptions unit tests."""

import pytest
from fastapi import status

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
    SSODegradedModeError,
    SSOError,
    TokenError,
    TokenExpiredError,
    UserNotFoundError,
)
from src.shared.api.exception_handlers import SECURITY_EXCEPTION_MAP
from src.shared.infrastructure.security.exceptions import SecurityError


class TestAuthErrorInheritance:
    """验证 AuthError 继承自 SecurityError"""

    def test_auth_error_inherits_security_error(self):
        exc = AuthError("test error")
        assert isinstance(exc, SecurityError)

    def test_auth_error_has_message_attribute(self):
        exc = AuthError("test message")
        assert exc.message == "test message"

    def test_auth_error_has_code_attribute(self):
        exc = AuthError("test", code="TEST_CODE")
        assert exc.code == "TEST_CODE"

    def test_auth_error_default_code(self):
        exc = AuthError("test")
        assert exc.code == "AUTH_ERROR"


class TestUserNotFoundError:
    """UserNotFoundError 测试"""

    def test_inherits_auth_error(self):
        exc = UserNotFoundError("user123")
        assert isinstance(exc, AuthError)
        assert isinstance(exc, SecurityError)

    def test_stores_identifier(self):
        exc = UserNotFoundError("user123")
        assert exc.identifier == "user123"

    def test_integer_identifier(self):
        exc = UserNotFoundError(123)
        assert exc.identifier == 123

    def test_error_code(self):
        exc = UserNotFoundError("user123")
        assert exc.code == "USER_NOT_FOUND"

    def test_message_format(self):
        exc = UserNotFoundError("user123")
        assert "user123" in exc.message


class TestInvalidCredentialsError:
    """InvalidCredentialsError 测试"""

    def test_inherits_auth_error(self):
        exc = InvalidCredentialsError()
        assert isinstance(exc, AuthError)

    def test_default_message(self):
        exc = InvalidCredentialsError()
        assert exc.message == "Invalid credentials"

    def test_custom_message(self):
        exc = InvalidCredentialsError("Wrong password")
        assert exc.message == "Wrong password"

    def test_error_code(self):
        exc = InvalidCredentialsError()
        assert exc.code == "INVALID_CREDENTIALS"


class TestAccountLockedError:
    """AccountLockedError 测试"""

    def test_inherits_auth_error(self):
        exc = AccountLockedError()
        assert isinstance(exc, AuthError)

    def test_locked_until_attribute(self):
        exc = AccountLockedError(locked_until="2025-01-26T12:00:00Z")
        assert exc.locked_until == "2025-01-26T12:00:00Z"

    def test_locked_until_none(self):
        exc = AccountLockedError()
        assert exc.locked_until is None

    def test_message_with_locked_until(self):
        exc = AccountLockedError(locked_until="2025-01-26T12:00:00Z")
        assert "2025-01-26T12:00:00Z" in exc.message

    def test_message_without_locked_until(self):
        exc = AccountLockedError()
        assert exc.message == "Account is locked"

    def test_error_code(self):
        exc = AccountLockedError()
        assert exc.code == "ACCOUNT_LOCKED"


class TestAccountInactiveError:
    """AccountInactiveError 测试"""

    def test_inherits_auth_error(self):
        exc = AccountInactiveError()
        assert isinstance(exc, AuthError)

    def test_default_message(self):
        exc = AccountInactiveError()
        assert exc.message == "Account is not active"

    def test_error_code(self):
        exc = AccountInactiveError()
        assert exc.code == "ACCOUNT_INACTIVE"


class TestPasswordExpiredError:
    """PasswordExpiredError 测试"""

    def test_inherits_auth_error(self):
        exc = PasswordExpiredError()
        assert isinstance(exc, AuthError)

    def test_default_message(self):
        exc = PasswordExpiredError()
        assert exc.message == "Password has expired"

    def test_error_code(self):
        exc = PasswordExpiredError()
        assert exc.code == "PASSWORD_EXPIRED"


class TestPasswordTooWeakError:
    """PasswordTooWeakError 测试"""

    def test_inherits_auth_error(self):
        exc = PasswordTooWeakError(violations=["too short"])
        assert isinstance(exc, AuthError)

    def test_violations_attribute(self):
        violations = ["too short", "no uppercase"]
        exc = PasswordTooWeakError(violations=violations)
        assert exc.violations == violations

    def test_message_contains_violations(self):
        exc = PasswordTooWeakError(violations=["too short", "no number"])
        assert "too short" in exc.message
        assert "no number" in exc.message

    def test_error_code(self):
        exc = PasswordTooWeakError(violations=[])
        assert exc.code == "PASSWORD_TOO_WEAK"


class TestPasswordHistoryViolationError:
    """PasswordHistoryViolationError 测试"""

    def test_inherits_auth_error(self):
        exc = PasswordHistoryViolationError()
        assert isinstance(exc, AuthError)

    def test_default_message(self):
        exc = PasswordHistoryViolationError()
        assert exc.message == "Cannot reuse recent passwords"

    def test_error_code(self):
        exc = PasswordHistoryViolationError()
        assert exc.code == "PASSWORD_HISTORY_VIOLATION"


class TestTokenError:
    """TokenError 测试"""

    def test_inherits_auth_error(self):
        exc = TokenError()
        assert isinstance(exc, AuthError)

    def test_default_code(self):
        exc = TokenError()
        assert exc.code == "TOKEN_ERROR"


class TestInvalidTokenError:
    """InvalidTokenError 测试"""

    def test_inherits_token_error(self):
        exc = InvalidTokenError()
        assert isinstance(exc, TokenError)
        assert isinstance(exc, AuthError)

    def test_default_message(self):
        exc = InvalidTokenError()
        assert exc.message == "Invalid token"

    def test_error_code(self):
        exc = InvalidTokenError()
        assert exc.code == "INVALID_TOKEN"


class TestTokenExpiredError:
    """TokenExpiredError 测试"""

    def test_inherits_token_error(self):
        exc = TokenExpiredError()
        assert isinstance(exc, TokenError)
        assert isinstance(exc, AuthError)

    def test_default_message(self):
        exc = TokenExpiredError()
        assert exc.message == "Token has expired"

    def test_error_code(self):
        exc = TokenExpiredError()
        assert exc.code == "TOKEN_EXPIRED"


class TestInsufficientPermissionsError:
    """InsufficientPermissionsError 测试"""

    def test_inherits_auth_error(self):
        exc = InsufficientPermissionsError("admin")
        assert isinstance(exc, AuthError)

    def test_required_permission_attribute(self):
        exc = InsufficientPermissionsError("admin")
        assert exc.required_permission == "admin"

    def test_message_contains_permission(self):
        exc = InsufficientPermissionsError("admin")
        assert "admin" in exc.message

    def test_error_code(self):
        exc = InsufficientPermissionsError("admin")
        assert exc.code == "INSUFFICIENT_PERMISSIONS"


class TestSSOError:
    """SSOError 测试"""

    def test_inherits_auth_error(self):
        exc = SSOError()
        assert isinstance(exc, AuthError)

    def test_default_code(self):
        exc = SSOError()
        assert exc.code == "SSO_ERROR"


class TestSSODegradedModeError:
    """SSODegradedModeError 测试"""

    def test_inherits_sso_error(self):
        exc = SSODegradedModeError()
        assert isinstance(exc, SSOError)
        assert isinstance(exc, AuthError)

    def test_default_message(self):
        exc = SSODegradedModeError()
        assert exc.message == "SSO service is temporarily unavailable"

    def test_error_code(self):
        exc = SSODegradedModeError()
        assert exc.code == "SSO_DEGRADED_MODE"


class TestAuthExceptionsHttpMapping:
    """验证 auth 异常在 SECURITY_EXCEPTION_MAP 中有正确映射"""

    @pytest.mark.parametrize(
        "exception_class,expected_status",
        [
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
    def test_exception_maps_to_correct_status(self, exception_class, expected_status):
        """验证每个 auth 异常映射到正确的 HTTP 状态码"""
        # 需要使用别名导入的类名查找
        from src.shared.api.exception_handlers import (
            AuthAccountInactiveError,
            AuthAccountLockedError,
            AuthInsufficientPermissionsError,
            AuthInvalidCredentialsError,
            AuthInvalidTokenError,
            AuthPasswordExpiredError,
            AuthPasswordHistoryViolationError,
            AuthPasswordTooWeakError,
            AuthSSODegradedModeError,
            AuthSSOError,
            AuthTokenExpiredError,
            AuthUserNotFoundError,
        )

        # 映射本地类到别名类
        alias_map = {
            InvalidCredentialsError: AuthInvalidCredentialsError,
            UserNotFoundError: AuthUserNotFoundError,
            TokenExpiredError: AuthTokenExpiredError,
            InvalidTokenError: AuthInvalidTokenError,
            AccountLockedError: AuthAccountLockedError,
            AccountInactiveError: AuthAccountInactiveError,
            PasswordExpiredError: AuthPasswordExpiredError,
            PasswordTooWeakError: AuthPasswordTooWeakError,
            PasswordHistoryViolationError: AuthPasswordHistoryViolationError,
            InsufficientPermissionsError: AuthInsufficientPermissionsError,
            SSOError: AuthSSOError,
            SSODegradedModeError: AuthSSODegradedModeError,
        }

        alias_class = alias_map[exception_class]
        actual_status = SECURITY_EXCEPTION_MAP.get(alias_class)
        assert actual_status == expected_status, (
            f"{exception_class.__name__} should map to {expected_status}, "
            f"but got {actual_status}"
        )


class TestCatchingAuthExceptions:
    """验证可以用 SecurityError 或 AuthError 统一捕获"""

    def test_catch_all_with_security_error(self):
        """所有 auth 异常都能被 SecurityError 捕获"""
        exceptions = [
            InvalidCredentialsError(),
            UserNotFoundError("test"),
            AccountLockedError(),
            TokenExpiredError(),
            InsufficientPermissionsError("admin"),
            SSODegradedModeError(),
        ]

        for exc in exceptions:
            try:
                raise exc
            except SecurityError as caught:
                assert caught is exc
            else:
                pytest.fail(f"{type(exc).__name__} was not caught by SecurityError")

    def test_catch_all_with_auth_error(self):
        """所有 auth 异常都能被 AuthError 捕获"""
        exceptions = [
            InvalidCredentialsError(),
            UserNotFoundError("test"),
            AccountLockedError(),
            TokenExpiredError(),
            InsufficientPermissionsError("admin"),
            SSODegradedModeError(),
        ]

        for exc in exceptions:
            try:
                raise exc
            except AuthError as caught:
                assert caught is exc
            else:
                pytest.fail(f"{type(exc).__name__} was not caught by AuthError")
