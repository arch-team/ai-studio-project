"""Auth domain exceptions - 重导出 shared/security 异常.

职责说明:
---------
本模块重导出 shared/security 的异常，以便 auth 模块业务代码保持统一的导入路径。
同时定义了 auth 模块独有的异常类。

设计说明:
---------
- 重导出的异常类保持原有的 http_status 和 error_code 属性
- auth 模块独有的异常继承 SecurityError，获得统一的异常处理
- 这种设计避免了异常类的重复定义，同时保持 API 兼容性

使用指南:
--------
- auth 模块业务代码 → 从本模块导入异常
- 基础设施代码 (middleware, jwt) → 使用 shared/infrastructure/security/exceptions.py
"""

# 从 shared/security 重导出所有异常
from src.shared.infrastructure.security.exceptions import (
    SecurityError,
    AuthenticationError,
    UserNotFoundError,
    InvalidCredentialsError,
    AccountLockedError,
    AccountValidationError,
    TokenExpiredError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordTooWeakError,
    PasswordHistoryViolationError,
    InsufficientPermissionsError,
    SSOError,
    SSODegradedModeError,
)


# Auth 模块独有异常
class AuthError(SecurityError):
    """Auth 模块基础异常.

    继承 SecurityError 以获得正确的 HTTP 状态码映射。
    所有 auth 模块独有的业务异常应继承此类。
    """

    http_status = 401

    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        super().__init__(message, code=code)


class AccountInactiveError(AuthError):
    """账户未激活异常."""

    http_status = 401

    def __init__(self, message: str = "Account is not active"):
        super().__init__(message, code="ACCOUNT_INACTIVE")


class TokenError(AuthError):
    """Token 错误基类.

    作为 InvalidTokenError 和 TokenExpiredError 的替代基类，
    用于 auth 模块内部需要区分 Token 相关错误的场景。
    """

    http_status = 401

    def __init__(self, message: str = "Token error", code: str = "TOKEN_ERROR"):
        super().__init__(message, code=code)


__all__ = [
    # 重导出的异常（来自 shared/security）
    "SecurityError",
    "AuthenticationError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    "AccountLockedError",
    "AccountValidationError",
    "TokenExpiredError",
    "InvalidTokenError",
    "PasswordExpiredError",
    "PasswordTooWeakError",
    "PasswordHistoryViolationError",
    "InsufficientPermissionsError",
    "SSOError",
    "SSODegradedModeError",
    # Auth 模块独有异常
    "AuthError",
    "AccountInactiveError",
    "TokenError",
]
