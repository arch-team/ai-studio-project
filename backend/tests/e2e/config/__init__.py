"""E2E 测试配置模块

提供集中化的配置管理：
- Pydantic Settings 配置类
- 环境变量加载
- 配置验证
"""

from tests.e2e.config.settings import E2ETestSettings, get_e2e_settings

__all__ = [
    "E2ETestSettings",
    "get_e2e_settings",
]
