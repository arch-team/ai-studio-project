"""Security Utilities - Authentication and authorization.

Components:
- JWT token generation and validation (using Authlib)
- Password hashing (using bcrypt via passlib)
- Permission checking utilities
"""

from src.shared.infrastructure.security.constants import (
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
from src.shared.infrastructure.security.jwt import (
    JWTManager,
    TokenPayload,
    TokenType,
    get_jwt_manager,
)
from src.shared.infrastructure.security.password import (
    PasswordHasher,
    PasswordValidator,
    get_password_hasher,
    get_password_validator,
)
from src.shared.infrastructure.security.paths import (
    AUDIT_EXEMPT_PATHS,
    AUDIT_EXEMPT_PREFIXES,
    AUTH_EXEMPT_PATHS,
    AUTH_EXEMPT_PATTERNS,
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
    # Path constants
    "AUTH_EXEMPT_PATHS",
    "AUTH_EXEMPT_PATTERNS",
    "AUDIT_EXEMPT_PATHS",
    "AUDIT_EXEMPT_PREFIXES",
    # Exceptions
    "AccountLockedError",
    "AccountValidationError",
    "AuthenticationError",
    "InsufficientPermissionsError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "PasswordExpiredError",
    "PasswordHistoryViolationError",
    "PasswordTooWeakError",
    "SecurityError",
    "SSODegradedModeError",
    "SSOError",
    "TokenExpiredError",
    "UserNotFoundError",
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
