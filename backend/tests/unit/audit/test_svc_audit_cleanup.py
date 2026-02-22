"""AuditCleanupService 单元测试。

验证清理服务的执行逻辑、失败计数、告警触发等核心行为。
"""

from unittest.mock import AsyncMock

import pytest

from src.modules.audit.application.services.audit_cleanup_service import (
    MAX_CONSECUTIVE_FAILURES,
    AlertService,
    AuditCleanupService,
)


@pytest.fixture
def mock_repository() -> AsyncMock:
    """创建 Mock IAuditLogRepository。"""
    repo = AsyncMock()
    repo.delete_expired = AsyncMock(return_value=5)
    return repo


@pytest.fixture
def mock_alert_service() -> AsyncMock:
    """创建 Mock AlertService。"""
    return AsyncMock(spec=AlertService)


@pytest.fixture
def service(mock_repository: AsyncMock, mock_alert_service: AsyncMock) -> AuditCleanupService:
    """创建 AuditCleanupService 实例。"""
    return AuditCleanupService(
        repository=mock_repository,
        alert_service=mock_alert_service,
    )


class TestExecuteCleanup:
    """测试 execute_cleanup 方法。"""

    async def test_execute_cleanup_success(
        self,
        service: AuditCleanupService,
        mock_repository: AsyncMock,
    ) -> None:
        """成功清理返回正确结果。"""
        mock_repository.delete_expired.return_value = 10

        result = await service.execute_cleanup()

        assert result["success"] is True
        assert result["deleted_count"] == 10
        assert "elapsed_ms" in result
        assert "executed_at" in result
        mock_repository.delete_expired.assert_called_once()

    async def test_execute_cleanup_updates_last_cleanup_time(
        self,
        service: AuditCleanupService,
        mock_repository: AsyncMock,
    ) -> None:
        """成功清理后更新 last_cleanup_at。"""
        assert service.last_cleanup_at is None

        await service.execute_cleanup()

        assert service.last_cleanup_at is not None

    async def test_execute_cleanup_failure_returns_error(
        self,
        service: AuditCleanupService,
        mock_repository: AsyncMock,
    ) -> None:
        """清理失败返回错误信息。"""
        mock_repository.delete_expired.side_effect = RuntimeError("数据库连接失败")

        result = await service.execute_cleanup()

        assert result["success"] is False
        assert "数据库连接失败" in result["error"]
        assert "elapsed_ms" in result

    async def test_execute_cleanup_zero_records(
        self,
        service: AuditCleanupService,
        mock_repository: AsyncMock,
    ) -> None:
        """无过期记录时也返回成功。"""
        mock_repository.delete_expired.return_value = 0

        result = await service.execute_cleanup()

        assert result["success"] is True
        assert result["deleted_count"] == 0


class TestConsecutiveFailures:
    """测试连续失败计数。"""

    async def test_initial_consecutive_failures_is_zero(
        self,
        service: AuditCleanupService,
    ) -> None:
        """初始连续失败次数为 0。"""
        assert service.consecutive_failures == 0

    async def test_max_consecutive_failures_threshold(self) -> None:
        """连续失败阈值为 3。"""
        assert MAX_CONSECUTIVE_FAILURES == 3


class TestScheduledCleanup:
    """测试定时清理启停。"""

    async def test_start_and_stop_cleanup(
        self,
        service: AuditCleanupService,
    ) -> None:
        """启动和停止清理任务不抛异常。"""
        await service.start_scheduled_cleanup()
        await service.stop_scheduled_cleanup()

    async def test_stop_without_start(
        self,
        service: AuditCleanupService,
    ) -> None:
        """未启动时停止不抛异常。"""
        await service.stop_scheduled_cleanup()


class TestSecondsUntilNextRun:
    """测试下次运行时间计算。"""

    def test_seconds_until_next_run_positive(
        self,
        service: AuditCleanupService,
    ) -> None:
        """返回值应为正数且 >= 60 秒。"""
        seconds = service._seconds_until_next_run()

        assert seconds >= 60.0
        # 最多不超过 24 小时 + 缓冲
        assert seconds <= 86400 + 60
