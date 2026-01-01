"""数据库配置和连接管理

使用SQLAlchemy 2.0异步引擎实现数据库连接池管理
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from .logging import get_logger
from .settings import settings

logger = get_logger(__name__)

# 全局异步引擎实例
_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """获取或创建异步数据库引擎

    Returns:
        AsyncEngine: SQLAlchemy异步引擎实例
    """
    global _async_engine

    if _async_engine is None:
        logger.info("创建数据库引擎")

        # 根据环境选择连接池策略
        if settings.is_development:
            # 开发环境使用NullPool避免连接池问题
            poolclass = NullPool
            logger.info("使用NullPool连接池（开发环境）")
        else:
            # 生产环境使用QueuePool
            poolclass = QueuePool
            logger.info(
                f"使用QueuePool连接池 (pool_size={settings.database_pool_size}, "
                f"max_overflow={settings.database_max_overflow})"
            )

        # 构建引擎参数
        engine_kwargs = {
            "echo": settings.database_echo,
            "poolclass": poolclass,
        }

        # NullPool不需要pool_size和max_overflow参数
        if not settings.is_development:
            engine_kwargs.update({
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_pre_ping": True,  # 连接前测试
                "pool_recycle": 3600,  # 1小时回收连接
            })

        _async_engine = create_async_engine(
            str(settings.database_url),
            **engine_kwargs
        )

    return _async_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取或创建会话工厂

    Returns:
        async_sessionmaker: 异步会话工厂
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("创建会话工厂")

    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入）

    用于FastAPI的依赖注入，自动管理会话生命周期

    Yields:
        AsyncSession: 数据库会话

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库连接

    在应用启动时调用，用于测试数据库连接
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            # 测试连接
            await conn.execute(text("SELECT 1"))
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


async def close_db() -> None:
    """关闭数据库连接

    在应用关闭时调用，清理连接池
    """
    global _async_engine, _async_session_factory

    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
        logger.info("数据库连接已关闭")


__all__ = [
    "get_engine",
    "get_session_factory",
    "get_db",
    "init_db",
    "close_db",
]
