"""Auth domain exceptions - 重导出 shared/security 异常.

使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段。

职责说明:
---------
本模块重导出 shared/security 的异常，以便 auth 模块业务代码保持统一的导入路径。
同时定义了 auth 模块独有的异常类。

使用指南:
--------
- auth 模块业务代码 → 从本模块导入异常
- 基础设施代码 (middleware, jwt) → 使用 shared/infrastructure/security/exceptions.py
"""

from dataclasses import dataclass, field

from src.shared.domain.problem import Problem, problem

# 从 shared/security 重导出所有异常
from src.shared.infrastructure.security.exceptions import (
    AccountLockedError,
    AccountValidationError,
    AuthenticationError,
    InsufficientPermissionsError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    SecurityError,
    SSODegradedModeError,
    SSOError,
    TokenExpiredError,
    UserNotFoundError,
)

# =============================================================================
# Auth 模块独有异常
# =============================================================================


@problem(401, "ACCOUNT_INACTIVE")
@dataclass
class AccountInactiveError(Problem):
    """账户未激活."""

    message: str = field(default="Account is not active")


@problem(401, "AUTH_ERROR")
@dataclass
class AuthError(Problem):
    """Auth 模块基础异常."""

    message: str = field(default="Authentication error")


@problem(401, "TOKEN_ERROR")
@dataclass
class TokenError(Problem):
    """Token 错误基类."""

    message: str = field(default="Token error")


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
