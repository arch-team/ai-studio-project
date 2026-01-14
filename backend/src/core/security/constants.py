"""Security Constants - Centralized security configuration."""

# Password Policy
PASSWORD_MIN_LENGTH = 12
PASSWORD_BCRYPT_COST = 12
PASSWORD_HISTORY_COUNT = 5
PASSWORD_EXPIRY_DAYS = 90

# Account Lockout Policy
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Token Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 15

# SSO Configuration
SSO_TIMEOUT_SECONDS = 5
SSO_MAX_CONSECUTIVE_FAILURES = 3
SSO_RECOVERY_CHECK_INTERVAL_MINUTES = 5

# RBAC Role Hierarchy (higher value = more privileges)
ROLE_HIERARCHY = {
    "admin": 4,
    "project_manager": 3,
    "engineer": 2,
    "viewer": 1,
}

# Authentication Types
AUTH_TYPE_SSO = "sso"
AUTH_TYPE_LOCAL = "local"
