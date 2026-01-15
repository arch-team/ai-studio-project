"""Auth domain layer - Entities, value objects, and repository interfaces."""

from .entities import LoginAttempt, PasswordHistory, User
from .exceptions import (
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
from .repositories import (
    ILoginAttemptRepository,
    IPasswordHistoryRepository,
    IUserRepository,
)
from .value_objects import AuthType, Permission, UserRole, UserStatus

__all__ = [
    # Entities
    "User",
    "LoginAttempt",
    "PasswordHistory",
    # Value Objects
    "UserStatus",
    "UserRole",
    "AuthType",
    "Permission",
    # Repository Interfaces
    "IUserRepository",
    "ILoginAttemptRepository",
    "IPasswordHistoryRepository",
    # Exceptions
    "AuthError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    "AccountLockedError",
    "AccountInactiveError",
    "PasswordExpiredError",
    "PasswordTooWeakError",
    "PasswordHistoryViolationError",
    "TokenError",
    "InvalidTokenError",
    "TokenExpiredError",
    "InsufficientPermissionsError",
    "SSOError",
    "SSODegradedModeError",
]
