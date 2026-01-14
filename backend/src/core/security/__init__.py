"""Security Utilities - Authentication and authorization.

Components:
- JWT token generation and validation (using Authlib)
- Password hashing (using bcrypt via passlib)
- Permission checking utilities
"""

from src.core.security.constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTH_TYPE_LOCAL,
    AUTH_TYPE_SSO,
    LOCKOUT_DURATION_MINUTES,
    MAX_FAILED_LOGIN_ATTEMPTS,
    PASSWORD_BCRYPT_COST,
    PASSWORD_EXPIRY_DAYS,
    PASSWORD_HISTORY_COUNT,
    PASSWORD_MIN_LENGTH,
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ROLE_HIERARCHY,
    SSO_MAX_CONSECUTIVE_FAILURES,
    SSO_RECOVERY_CHECK_INTERVAL_MINUTES,
    SSO_TIMEOUT_SECONDS,
)
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
from src.core.security.jwt import (
    JWTManager,
    TokenPayload,
    TokenType,
    get_jwt_manager,
)
from src.core.security.password import (
    PasswordHasher,
    PasswordValidator,
    get_password_hasher,
    get_password_validator,
)

__all__ = [
    # Constants
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "AUTH_TYPE_LOCAL",
    "AUTH_TYPE_SSO",
    "LOCKOUT_DURATION_MINUTES",
    "MAX_FAILED_LOGIN_ATTEMPTS",
    "PASSWORD_BCRYPT_COST",
    "PASSWORD_EXPIRY_DAYS",
    "PASSWORD_HISTORY_COUNT",
    "PASSWORD_MIN_LENGTH",
    "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "ROLE_HIERARCHY",
    "SSO_MAX_CONSECUTIVE_FAILURES",
    "SSO_RECOVERY_CHECK_INTERVAL_MINUTES",
    "SSO_TIMEOUT_SECONDS",
    # Exceptions
    "AccountLockedError",
    "AuthenticationError",
    "InsufficientPermissionsError",
    "InvalidTokenError",
    "PasswordExpiredError",
    "PasswordHistoryViolationError",
    "PasswordTooWeakError",
    "SecurityError",
    "SSODegradedModeError",
    "SSOError",
    "TokenExpiredError",
    # JWT
    "JWTManager",
    "TokenPayload",
    "TokenType",
    "get_jwt_manager",
    # Password
    "PasswordHasher",
    "PasswordValidator",
    "get_password_hasher",
    "get_password_validator",
]
