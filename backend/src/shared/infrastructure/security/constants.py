"""Security Constants - Centralized security configuration."""

from typing import Final

# ============================================================================
# 密码策略
# ============================================================================

PASSWORD_MIN_LENGTH: Final[int] = 12
PASSWORD_BCRYPT_COST: Final[int] = 12
PASSWORD_HISTORY_COUNT: Final[int] = 5
PASSWORD_EXPIRY_DAYS: Final[int] = 90

# ============================================================================
# 账户锁定策略
# ============================================================================

MAX_FAILED_LOGIN_ATTEMPTS: Final[int] = 5
LOCKOUT_DURATION_MINUTES: Final[int] = 30

# ============================================================================
# Token 配置
# ============================================================================

ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 7
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: Final[int] = 15

# ============================================================================
# SSO 配置
# ============================================================================

SSO_TIMEOUT_SECONDS: Final[int] = 5
SSO_MAX_CONSECUTIVE_FAILURES: Final[int] = 3
SSO_RECOVERY_CHECK_INTERVAL_MINUTES: Final[int] = 5

# ============================================================================
# RBAC 角色层级（数值越大权限越高）
# ============================================================================

ROLE_HIERARCHY: Final[dict[str, int]] = {
    "admin": 4,
    "project_manager": 3,
    "engineer": 2,
    "viewer": 1,
}

# ============================================================================
# 认证类型
# ============================================================================

AUTH_TYPE_SSO: Final[str] = "sso"
AUTH_TYPE_LOCAL: Final[str] = "local"
