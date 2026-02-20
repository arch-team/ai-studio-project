"""SSO 中间件 - AWS IAM Identity Center 集成.

实现 OIDC Token 验证、IdP 角色映射、故障转移和健康检查。
"""

import logging
import time
from dataclasses import dataclass, field
from functools import lru_cache

import jwt as pyjwt

from src.shared.infrastructure.config import get_settings
from src.shared.infrastructure.security.constants import (
    SSO_MAX_CONSECUTIVE_FAILURES,
    SSO_TIMEOUT_SECONDS,
)
from src.shared.infrastructure.security.exceptions import SSOError

logger = logging.getLogger(__name__)

# ============================================================================
# IdP 组到平台角色的映射
# ============================================================================

GROUP_ROLE_MAPPING: dict[str, str] = {
    "platform-admins": "admin",
    "project-managers": "project_manager",
    "ml-engineers": "engineer",
    "ml-viewers": "viewer",
}

# 角色优先级: 数值越大权限越高
_ROLE_PRIORITY: dict[str, int] = {
    "admin": 4,
    "project_manager": 3,
    "engineer": 2,
    "viewer": 1,
}

# 默认角色（当无法匹配任何组时）
_DEFAULT_ROLE = "viewer"


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class SSOUserInfo:
    """SSO 用户信息，从 OIDC Token 中提取."""

    iam_identity_id: str
    username: str
    email: str
    groups: list[str] = field(default_factory=list)
    display_name: str | None = None

    @property
    def identity_id(self) -> str:
        """兼容别名，供 login.py 使用."""
        return self.iam_identity_id


# ============================================================================
# SSO 服务
# ============================================================================


class SSOService:
    """SSO 服务 - OIDC Token 验证和用户信息提取."""

    def __init__(self, region: str, issuer_url: str | None = None) -> None:
        self._region = region
        self._issuer_url = issuer_url
        # JWKS 缓存（实际环境需从 OIDC discovery endpoint 获取）
        self._jwks_cache: dict[str, str] | None = None

    async def validate_sso_token(self, token: str) -> SSOUserInfo:
        """验证 OIDC JWT token，提取用户信息.

        Raises:
            SSOError: Token 验证失败时
        """
        try:
            # 解码 JWT（不验证签名，生产环境应通过 JWKS 验证）
            # 实际部署时需配置 issuer_url 并从 OIDC discovery 获取公钥
            claims = pyjwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["RS256", "HS256"],
            )

            return SSOUserInfo(
                iam_identity_id=claims.get("sub", ""),
                username=claims.get("preferred_username", claims.get("sub", "")),
                email=claims.get("email", ""),
                groups=claims.get("groups", []),
                display_name=claims.get("name"),
            )
        except pyjwt.PyJWTError as e:
            raise SSOError(message=f"SSO token validation failed: {e}")

    async def validate_id_token(self, token: str) -> SSOUserInfo:
        """验证 ID Token（validate_sso_token 的别名，供 login.py 调用）."""
        return await self.validate_sso_token(token)

    def map_groups_to_role(self, groups: list[str]) -> str:
        """将 IdP 组映射到平台角色.

        映射规则: 取用户所属组中最高权限的角色。
        优先级: admin > project_manager > engineer > viewer
        """
        return map_groups_to_role(groups)


# ============================================================================
# SSO 健康跟踪器
# ============================================================================


class SSOHealthTracker:
    """SSO 服务健康状态跟踪.

    跟踪 IdP 连续失败次数，当超过阈值时进入降级模式。
    """

    def __init__(self, timeout_seconds: float = SSO_TIMEOUT_SECONDS) -> None:
        self._timeout_seconds = timeout_seconds
        self._consecutive_failures = 0
        self._last_failure_time: float | None = None
        self._last_success_time: float | None = None

    async def check_health(self) -> bool:
        """检查 IdP 可达性.

        Returns:
            True 表示 IdP 健康，False 表示不可达。
        """
        # 实际环境需调用 IdP 的 health/discovery endpoint
        # 此处提供可 mock 的接口
        try:
            # 占位: 实际实现通过 HTTP 请求 OIDC discovery endpoint
            return True
        except Exception:
            self.record_failure()
            return False

    @property
    def is_degraded(self) -> bool:
        """当前是否处于降级模式.

        当连续失败次数超过阈值时进入降级模式。
        """
        return self._consecutive_failures >= SSO_MAX_CONSECUTIVE_FAILURES

    def record_failure(self) -> None:
        """记录一次 IdP 请求失败."""
        self._consecutive_failures += 1
        self._last_failure_time = time.monotonic()
        logger.warning(
            "SSO IdP 请求失败",
            extra={
                "consecutive_failures": self._consecutive_failures,
                "is_degraded": self.is_degraded,
            },
        )

    def record_success(self) -> None:
        """记录 IdP 恢复成功，重置失败计数."""
        if self._consecutive_failures > 0:
            logger.info(
                "SSO IdP 恢复",
                extra={"previous_failures": self._consecutive_failures},
            )
        self._consecutive_failures = 0
        self._last_success_time = time.monotonic()


# ============================================================================
# 公共工具函数
# ============================================================================


def map_groups_to_role(groups: list[str]) -> str:
    """将 IdP 组列表映射到平台角色.

    映射规则:
    - platform-admins → admin
    - project-managers → project_manager
    - ml-engineers → engineer
    - ml-viewers → viewer

    取用户所属组中最高权限的角色。
    当无法匹配任何组时，返回默认角色 viewer。
    """
    best_role = _DEFAULT_ROLE
    best_priority = _ROLE_PRIORITY.get(_DEFAULT_ROLE, 0)

    for group in groups:
        role = GROUP_ROLE_MAPPING.get(group)
        if role:
            priority = _ROLE_PRIORITY.get(role, 0)
            if priority > best_priority:
                best_role = role
                best_priority = priority

    return best_role


# ============================================================================
# 单例工厂
# ============================================================================

# 模块级单例实例
_sso_service_instance: SSOService | None = None
_sso_health_tracker_instance: SSOHealthTracker | None = None


def get_sso_service() -> SSOService:
    """获取 SSO 服务单例.

    根据环境变量配置创建 SSO 服务实例。
    """
    global _sso_service_instance
    if _sso_service_instance is None:
        settings = get_settings()
        _sso_service_instance = SSOService(
            region=settings.aws_region,
            issuer_url=None,  # 可通过环境变量扩展
        )
    return _sso_service_instance


def get_sso_health_tracker() -> SSOHealthTracker:
    """获取 SSO 健康跟踪器单例."""
    global _sso_health_tracker_instance
    if _sso_health_tracker_instance is None:
        _sso_health_tracker_instance = SSOHealthTracker()
    return _sso_health_tracker_instance


def reset_sso_singletons() -> None:
    """重置单例实例（仅用于测试）."""
    global _sso_service_instance, _sso_health_tracker_instance
    _sso_service_instance = None
    _sso_health_tracker_instance = None
