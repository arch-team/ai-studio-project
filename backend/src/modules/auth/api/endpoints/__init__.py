"""Auth API 端点聚合模块."""

from fastapi import APIRouter

from .account import router as account_router
from .login import router as login_router
from .password import router as password_router

# 聚合所有子路由
router = APIRouter()
router.include_router(login_router, tags=["auth"])
router.include_router(account_router, tags=["auth"])
router.include_router(password_router, tags=["auth"])

__all__ = ["router"]
