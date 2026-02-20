"""SSO 中间件快捷导入 - 代理到 shared.api.middleware.sso.

login.py 通过 src.api.middleware.sso 导入，此模块将所有公开接口
代理到实际实现位置 src.shared.api.middleware.sso。
"""

from src.shared.api.middleware.sso import (  # noqa: F401
    GROUP_ROLE_MAPPING,
    SSOHealthTracker,
    SSOService,
    SSOUserInfo,
    get_sso_health_tracker,
    get_sso_service,
    map_groups_to_role,
    reset_sso_singletons,
)

__all__ = [
    "GROUP_ROLE_MAPPING",
    "SSOHealthTracker",
    "SSOService",
    "SSOUserInfo",
    "get_sso_health_tracker",
    "get_sso_service",
    "map_groups_to_role",
    "reset_sso_singletons",
]
