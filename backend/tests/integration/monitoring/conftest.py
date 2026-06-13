"""Monitoring 模块集成测试 fixtures - 真实数据库会话。

提供一个函数级 `db_session` fixture，连接真实 MySQL，并在每个测试后回滚，
保持数据库干净。

为什么不直接复用全局 AsyncSessionLocal:
  全局 engine 在模块导入时创建连接池，而 pytest-asyncio 为每个测试函数创建
  独立事件循环。复用池中连接会触发 "Event loop is closed"。这里为每个测试
  创建独立 engine 并使用 NullPool (不缓存连接)，规避跨事件循环复用问题。

前置条件: 可连接的 MySQL 且已 alembic upgrade head
  (docker compose up -d mysql && alembic upgrade head)。
"""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.shared.infrastructure.config import get_settings
from src.shared.infrastructure.database import import_all_models

# 确保所有 ORM 模型在建立映射前已加载
import_all_models()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供真实 MySQL 会话，测试结束自动回滚。

    使用独立 engine + NullPool，避免与全局连接池/事件循环冲突。
    """
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        poolclass=NullPool,
    )
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()

    await engine.dispose()
