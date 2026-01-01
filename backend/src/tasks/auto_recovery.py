"""训练任务自动恢复定时任务

定期扫描失败的训练任务并尝试自动恢复
"""

import asyncio
import logging

from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import settings
from services.training.auto_recovery_service import AutoRecoveryService

logger = logging.getLogger(__name__)

# Celery实例(复用checkpoint_migration的celery_app)
from tasks.checkpoint_migration import celery_app


@celery_app.task(name="check_and_recover_failed_jobs")
def check_and_recover_failed_jobs():
    """定期任务: 检查并恢复失败的训练任务

    调度: 每5分钟执行一次
    """
    logger.info("开始执行自动恢复定时任务")

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
                service = AutoRecoveryService(session)
                stats = await service.process_failed_jobs()

                logger.info(
                    f"自动恢复任务完成: "
                    f"total_failed={stats['total_failed']}, "
                    f"recovered={stats['recovered']}, "
                    f"failed={stats['failed']}, "
                    f"skipped={stats['skipped']}"
                )

                return stats

        except Exception as e:
            logger.error(f"自动恢复任务执行失败: {e}", exc_info=True)
            raise
        finally:
            await engine.dispose()

    # 运行异步任务
    return asyncio.run(async_run())


# 更新Celery调度配置(添加自动恢复任务)
celery_app.conf.beat_schedule["auto-recovery"] = {
    "task": "check_and_recover_failed_jobs",
    "schedule": 300.0,  # 每5分钟执行一次
    "options": {"expires": 300},  # 任务过期时间5分钟
}

# 任务路由配置(添加自动恢复任务路由)
celery_app.conf.task_routes.update({
    "check_and_recover_failed_jobs": {"queue": "auto_recovery"},
})


__all__ = ["check_and_recover_failed_jobs"]
