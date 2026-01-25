"""Auth domain exceptions.

职责说明:
---------
本模块定义了 auth 模块的业务层异常，供以下场景使用：
- AuthService (登录、Token 刷新)
- AccountService (账户管理)
- PasswordService (密码管理)
- RBACService (权限检查)

所有异常继承自 SecurityError，以便：
1. 被 security_exception_handler 统一处理
2. 获得正确的 HTTP 状态码映射
3. 携带 error_code 字段供前端程序化处理

设计说明:
---------
每个异常类包含以下类属性：
- http_status: 对应的 HTTP 状态码

异常处理器会自动读取这些属性，无需维护映射表。
新增异常只需定义 http_status 类属性即可。

使用指南:
--------
- auth 模块业务代码 → 使用本模块异常
- 基础设施代码 (middleware, jwt) → 使用 shared/infrastructure/security/exceptions.py
"""

from src.shared.infrastructure.security.exceptions import SecurityError


class AuthError(SecurityError):
    """Base exception for authentication errors.

    继承 SecurityError 以获得正确的 HTTP 状态码映射。
    所有 auth 模块业务异常应继承此类。
    """

    http_status = 401

    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        super().__init__(message, code=code)


class UserNotFoundError(AuthError):
    """Raised when user is not found."""

    http_status = 404

    def __init__(self, identifier: str | int):
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}", code="USER_NOT_FOUND")


class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""

    http_status = 401

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, code="INVALID_CREDENTIALS")


class AccountLockedError(AuthError):
    """Raised when account is locked."""

    http_status = 423

    def __init__(self, locked_until: str | None = None):
        self.locked_until = locked_until
        message = f"Account is locked until {locked_until}" if locked_until else "Account is locked"
        super().__init__(message, code="ACCOUNT_LOCKED")


class AccountInactiveError(AuthError):
    """Raised when account is not active."""

    http_status = 401

    def __init__(self, message: str = "Account is not active"):
        super().__init__(message, code="ACCOUNT_INACTIVE")


class PasswordExpiredError(AuthError):
    """Raised when password has expired."""

    http_status = 401

    def __init__(self, message: str = "Password has expired"):
        super().__init__(message, code="PASSWORD_EXPIRED")


class PasswordTooWeakError(AuthError):
    """Raised when password doesn't meet strength requirements."""

    http_status = 400

    def __init__(self, violations: list[str]):
        self.violations = violations
        super().__init__(f"Password too weak: {', '.join(violations)}", code="PASSWORD_TOO_WEAK")


class PasswordHistoryViolationError(AuthError):
    """Raised when new password was recently used."""

    http_status = 400

    def __init__(self, message: str = "Cannot reuse recent passwords"):
        super().__init__(message, code="PASSWORD_HISTORY_VIOLATION")


class TokenError(AuthError):
    """Base exception for token errors."""

    http_status = 401

    def __init__(self, message: str = "Token error", code: str = "TOKEN_ERROR"):
        super().__init__(message, code=code)


class InvalidTokenError(TokenError):
    """Raised when token is invalid."""

    http_status = 401

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, code="INVALID_TOKEN")


class TokenExpiredError(TokenError):
    """Raised when token has expired."""

    http_status = 401

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, code="TOKEN_EXPIRED")


class InsufficientPermissionsError(AuthError):
    """Raised when user lacks required permissions."""

    http_status = 403

    def __init__(self, required_permission: str):
        self.required_permission = required_permission
        super().__init__(f"Insufficient permissions: requires {required_permission}", code="INSUFFICIENT_PERMISSIONS")


class SSOError(AuthError):
    """Base exception for SSO errors."""

    http_status = 401

    def __init__(self, message: str = "SSO error", code: str = "SSO_ERROR"):
        super().__init__(message, code=code)


class SSODegradedModeError(SSOError):
    """Raised when SSO service is in degraded mode."""

    http_status = 503

    def __init__(self, message: str = "SSO service is temporarily unavailable"):
        super().__init__(message, code="SSO_DEGRADED_MODE")
