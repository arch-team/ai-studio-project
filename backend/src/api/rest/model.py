"""模型管理REST API端点(简化版-MVP)"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from models.user import User

router = APIRouter(prefix="/api/v1/models", tags=["models"])
logger = logging.getLogger(__name__)


# 临时依赖注入
async def get_current_user() -> User:
    """获取当前用户(临时实现)"""
    return User(id=1, username="admin", email="admin@example.com")


@router.get("/health")
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """健康检查端点"""
    return {"status": "ok", "service": "model-api"}
