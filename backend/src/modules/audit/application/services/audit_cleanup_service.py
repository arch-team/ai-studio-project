"""审计日志自动清理服务。

实现定时清理过期审计日志, 支持连续失败告警。
每日凌晨 2:00 (UTC 18:00) 执行, 清理超过 90 天的审计日志。
清理统计记录到 CloudWatch Logs (通过 structlog JSON 输出)。
"""

import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.modules.audit.domain.repositories import IAuditLogRepository

logger = structlog.get_logger(__name__)

# 清理配置
CLEANUP_INTERVAL_HOURS = 24  # 每 24 小时执行一次
CLEANUP_HOUR_UTC = 18  # UTC 18:00 = 北京时间 02:00
MAX_CONSECUTIVE_FAILURES = 3  # 连续失败告警阈值


class AlertService:
    """告警服务接口。"""

    async def send_alert(self, severity: str, title: str, message: str) -> None:
        """发送告警通知。"""
        logger.warning("alert_sent", severity=severity, title=title, message=message)


class AuditCleanupService:
    """审计日志自动清理服务。

    支持定时清理过期审计日志, 连续失败超过阈值时触发告警。
    可通过 repository 直接注入（用于测试/手动调用），
    或通过 session_factory 自动创建 session（用于后台定时任务）。
    """

    def __init__(
        self,
        repository: IAuditLogRepository,
        alert_service: AlertService | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._repository = repository
        self._alert_service = alert_service
        self._session_factory = session_factory
        self._consecutive_failures = 0
        self._cleanup_task: asyncio.Task[None] | None = None
        self._last_cleanup_at: datetime | None = None

    @property
    def consecutive_failures(self) -> int:
        """当前连续失败次数。"""
        return self._consecutive_failures

    @property
    def last_cleanup_at(self) -> datetime | None:
        """上次成功清理的时间。"""
        return self._last_cleanup_at

    async def start_scheduled_cleanup(self) -> None:
        """启动定时清理后台任务。"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            "audit_cleanup_scheduled",
            interval_hours=CLEANUP_INTERVAL_HOURS,
            cleanup_hour_utc=CLEANUP_HOUR_UTC,
        )

    async def stop_scheduled_cleanup(self) -> None:
        """停止定时清理。"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("audit_cleanup_stopped")

    async def execute_cleanup(self) -> dict:
        """执行一次清理, 返回清理结果。

        如果提供了 session_factory（后台任务模式），会为每次清理创建独立的 session。
        否则使用注入的 repository（API 调用模式）。
        """
        start = datetime.now(UTC)
        try:
            if self._session_factory:
                # 后台任务模式：创建独立 session 避免连接泄漏
                from src.modules.audit.infrastructure import AuditLogRepositoryImpl

                async with self._session_factory() as session:
                    repo = AuditLogRepositoryImpl(session)
                    deleted_count = await repo.delete_expired()
                    await session.commit()
            else:
                deleted_count = await self._repository.delete_expired()

            elapsed_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            self._last_cleanup_at = start
            return {
                "success": True,
                "deleted_count": deleted_count,
                "elapsed_ms": round(elapsed_ms, 2),
                "executed_at": start.isoformat(),
            }
        except Exception as e:
            elapsed_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            return {
                "success": False,
                "error": str(e),
                "elapsed_ms": round(elapsed_ms, 2),
            }

    async def _cleanup_loop(self) -> None:
        """清理循环, 每日凌晨 2:00 (UTC 18:00) 执行。"""
        while True:
            try:
                wait_seconds = self._seconds_until_next_run()
                await asyncio.sleep(wait_seconds)
                result = await self.execute_cleanup()

                if result["success"]:
                    self._consecutive_failures = 0
                    logger.info("audit_cleanup_success", **result)
                else:
                    self._consecutive_failures += 1
                    logger.error(
                        "audit_cleanup_failed",
                        consecutive_failures=self._consecutive_failures,
                        **result,
                    )

                    if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        await self._send_failure_alert()

            except asyncio.CancelledError:
                break
            except Exception:
                self._consecutive_failures += 1
                logger.exception(
                    "audit_cleanup_unexpected_error",
                    consecutive_failures=self._consecutive_failures,
                )

    async def _send_failure_alert(self) -> None:
        """连续失败超过阈值时发送告警。"""
        logger.critical(
            "audit_cleanup_consecutive_failures",
            consecutive_failures=self._consecutive_failures,
            threshold=MAX_CONSECUTIVE_FAILURES,
        )
        if self._alert_service:
            await self._alert_service.send_alert(
                severity="critical",
                title="审计日志清理连续失败",
                message=f"审计日志清理已连续失败 {self._consecutive_failures} 次, 超过阈值 {MAX_CONSECUTIVE_FAILURES}",
            )

    def _seconds_until_next_run(self) -> float:
        """计算距离下次执行 (UTC 18:00) 的秒数。"""
        now = datetime.now(UTC)
        # 计算今天的目标时间
        target = now.replace(hour=CLEANUP_HOUR_UTC, minute=0, second=0, microsecond=0)
        # 如果已过今天的目标时间, 设为明天
        if now >= target:
            target = target.replace(day=target.day + 1)
        diff = (target - now).total_seconds()
        # 安全保底: 至少等 60 秒, 避免无限快速循环
        return max(60.0, diff)
