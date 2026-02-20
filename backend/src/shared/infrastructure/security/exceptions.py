"""Security Exceptions - Authentication and authorization errors.

使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段。

职责说明:
---------
本模块定义了基础设施层的安全异常，供以下场景使用：
- JWT 中间件 (middleware/auth.py)
- Token 验证 (jwt.py)
- 安全装饰器

业务层（如 auth 模块）应使用 modules/auth/domain/exceptions.py 中的异常，
这些异常从本模块重导出，以便获得统一的 HTTP 状态码映射。
"""

from dataclasses import dataclass, field
from typing import Any

from src.shared.domain.problem import Problem, problem

# SecurityError 作为 Problem 的别名，用于向后兼容
SecurityError = Problem

# =============================================================================
# 认证异常
# =============================================================================


@problem(401, "AUTHENTICATION_FAILED")
@dataclass
class AuthenticationError(Problem):
    """认证失败."""

    message: str = field(default="Authentication failed")


@problem(401, "INVALID_CREDENTIALS")
@dataclass
class InvalidCredentialsError(Problem):
    """凭证无效."""

    message: str = field(default="Invalid username or password")


@problem(401, "TOKEN_EXPIRED")
@dataclass
class TokenExpiredError(Problem):
    """令牌过期."""

    message: str = field(default="Token has expired")


@problem(401, "INVALID_TOKEN")
@dataclass
class InvalidTokenError(Problem):
    """令牌无效."""

    message: str = field(default="Invalid token")


@problem(401, "PASSWORD_EXPIRED")
@dataclass
class PasswordExpiredError(Problem):
    """密码已过期."""

    message: str = field(default="Password has expired")


# =============================================================================
# 账户异常
# =============================================================================


@problem(404, "USER_NOT_FOUND", "User with id '{user_id}' not found")
@dataclass
class UserNotFoundError(Problem):
    """用户未找到."""

    user_id: str | int


@problem(400, "ACCOUNT_VALIDATION_FAILED")
@dataclass
class AccountValidationError(Problem):
    """账户验证失败."""

    message: str


@problem(423, "ACCOUNT_LOCKED")
@dataclass
class AccountLockedError(Problem):
    """账户被锁定."""

    message: str = field(default="Account is locked")
    locked_until: str | None = None

    def get_details(self) -> dict[str, Any] | None:
        """仅当 locked_until 存在时返回详情."""
        if self.locked_until:
            return {"locked_until": self.locked_until}
        return None


# =============================================================================
# 密码异常
# =============================================================================


@problem(400, "PASSWORD_TOO_WEAK")
@dataclass
class PasswordTooWeakError(Problem):
    """密码强度不足."""

    violations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """根据 violations 生成消息."""
        self.message = "Password does not meet requirements: " + "; ".join(self.violations)
        super().__post_init__()

    def get_details(self) -> dict[str, Any]:
        """返回违规列表."""
        return {"violations": self.violations}


@problem(400, "PASSWORD_HISTORY_VIOLATION")
@dataclass
class PasswordHistoryViolationError(Problem):
    """密码历史违规."""

    message: str = field(default="Cannot reuse recent passwords")


# =============================================================================
# 授权异常
# =============================================================================


@problem(403, "INSUFFICIENT_PERMISSIONS", "Insufficient permissions: requires {required_permission}")
@dataclass
class InsufficientPermissionsError(Problem):
    """权限不足."""

    required_permission: str


# =============================================================================
# SSO 异常
# =============================================================================


@problem(401, "SSO_ERROR")
@dataclass
class SSOError(Problem):
    """SSO 认证失败."""

    message: str = field(default="SSO authentication failed")
    degraded: bool = False


@problem(503, "SSO_DEGRADED_MODE")
@dataclass
class SSODegradedModeError(Problem):
    """SSO 降级模式."""

    message: str = field(default="SSO service is temporarily unavailable")
