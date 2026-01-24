"""Authentication Endpoints - 向后兼容入口.

此模块已重构为 endpoints/ 包，按功能拆分为:
- endpoints/login.py: 登录、登出、Token 管理
- endpoints/account.py: 账户管理
- endpoints/password.py: 密码管理

保留此文件以支持现有导入。
"""

from .endpoints import router

__all__ = ["router"]
