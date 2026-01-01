"""Checkpoint迁移定时任务

使用Celery调度checkpoint分层存储迁移
"""

import asyncio
import logging

from celery import Celery
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import settings
from services.checkpoint.storage_migration_service import StorageMigrationService

logger = logging.getLogger(__name__)

# Celery实例
celery_app = Celery(
    "checkpoint_migration",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="run_checkpoint_migration")
def run_checkpoint_migration():
    """定时任务: 执行checkpoint分层存储迁移

    调度: 每天凌晨2点执行
    """

    async def async_run():
        # 创建异步session
        engine = create_async_engine(
            str(settings.database_url),
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        try:
            async with async_session_factory() as session:
                service = StorageMigrationService(session)
                stats = await service.run_migration_policy()
                logger.info(f"Checkpoint迁移完成: {stats}")
                return stats
        except Exception as e:
            logger.error(f"Checkpoint迁移失败: {e}", exc_info=True)
            raise
        finally:
            await engine.dispose()

    # 运行异步任务
    return asyncio.run(async_run())


# Celery调度配置
celery_app.conf.beat_schedule = {
    "checkpoint-migration-daily": {
        "task": "run_checkpoint_migration",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点
        "options": {"expires": 3600},  # 任务过期时间1小时
    },
}

# 任务路由配置
celery_app.conf.task_routes = {
    "run_checkpoint_migration": {"queue": "checkpoint_migration"},
}


__all__ = ["celery_app", "run_checkpoint_migration"]
