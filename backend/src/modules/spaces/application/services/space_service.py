"""Space Service - 开发空间管理业务逻辑."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import TYPE_CHECKING

import structlog

from src.modules.spaces.application.interfaces import ISpaceBackendClient
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.exceptions import (
    DuplicateSpaceNameError,
    InvalidSpaceStateError,
    SpaceQuotaExceededError,
)
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import (
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.shared.application import BaseApplicationService
from src.shared.domain.interfaces import IQuotaChecker
from src.shared.utils import utc_now

if TYPE_CHECKING:
    from src.modules.spaces.application.services.sagemaker_metrics_service import SpaceMetricsService

logger = structlog.get_logger(__name__)

# Space 启动 SLA 阈值 (秒)
STARTUP_SLA_SECONDS = 180  # 3 分钟


class SpaceService(BaseApplicationService[Space, str]):
    """开发空间管理服务 - backend 无关，策略分发。"""

    def __init__(
        self,
        space_repository: ISpaceRepository,
        backends: dict[SpaceBackend, ISpaceBackendClient],
        quota_checker: IQuotaChecker | None = None,
        metrics_service: SpaceMetricsService | None = None,
    ):
        super().__init__(space_repository, "Space")
        self._space_repository = space_repository
        self._backends = backends
        self._quota_checker = quota_checker
        self._metrics_service = metrics_service
        self._sync_task: asyncio.Task[None] | None = None
        self._sync_interval: float = 30.0

    async def create_space(self, owner_id: int, data: dict) -> Space:
        """创建新的开发空间 - backend 无关，策略分发 + 配额校验。"""
        space_name = data["space_name"]

        # 检查同一所有者下的名称重复
        existing = await self._space_repository.get_by_name_and_owner(space_name, owner_id)
        if existing:
            raise DuplicateSpaceNameError(space_name, owner_id)

        space_type = SpaceType(data.get("space_type", "jupyter"))
        instance_type = SpaceInstanceType(data.get("instance_type", "ml.g5.xlarge"))
        storage_size_gb = data.get("storage_size_gb", 20)
        backend_str = data.get("backend", "studio")
        backend = SpaceBackend(backend_str)

        # 创建域实体
        space = Space(
            id=str(uuid.uuid4()),
            space_name=space_name,
            owner_id=owner_id,
            instance_type=instance_type,
            space_type=space_type,
            backend=backend,
            storage_size_gb=storage_size_gb,
            status=SpaceStatus.PENDING,
            lifecycle_config_arn=data.get("lifecycle_config_arn"),
            # HyperPod 专属字段
            namespace=data.get("namespace"),
            queue_name=data.get("queue_name"),
            workspace_template=data.get("workspace_template"),
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        # HyperPod backend: 配额校验（仅校验 GPU，若 gpu_count=0 的实例类型可跳过）
        if backend == SpaceBackend.HYPERPOD and self._quota_checker:
            requirements = space.get_resource_requirements()
            gpu_count = requirements["gpu_count"]
            if gpu_count > 0:
                has_quota = await self._quota_checker.check_quota(
                    user_id=owner_id,
                    resource_type="gpu",
                    amount=gpu_count,
                )
                if not has_quota:
                    available = await self._quota_checker.get_available_quota(owner_id, "gpu")
                    raise SpaceQuotaExceededError(
                        resource="gpu",
                        required=gpu_count,
                        available=available,
                    )

        # 取对应 backend 并调用 provision_space
        backend_client = self._backends[backend]
        start_time = time.monotonic()
        result = await backend_client.provision_space(space)
        elapsed_seconds = time.monotonic() - start_time

        # 回填 backend 返回的标识
        if backend == SpaceBackend.STUDIO:
            space.sagemaker_space_arn = result.get("arn")
        elif backend == SpaceBackend.HYPERPOD:
            space.namespace = result.get("namespace")
            # workspace_name 已在 space_name 中

        logger.info(
            "space_created",
            space_id=space.id,
            space_name=space_name,
            backend=backend.value,
            elapsed_seconds=round(elapsed_seconds, 2),
        )

        # 检查是否超过启动 SLA
        if elapsed_seconds > STARTUP_SLA_SECONDS:
            logger.warning(
                "space_creation_sla_exceeded",
                space_id=space.id,
                elapsed_seconds=round(elapsed_seconds, 2),
                sla_seconds=STARTUP_SLA_SECONDS,
            )

        # 上报启动耗时到 CloudWatch Metrics
        await self._record_startup_metric(space.id or space_name, elapsed_seconds)

        # 保存到数据库
        return await self._space_repository.create(space)

    async def get_space(self, space_id: str) -> Space:
        """根据 ID 获取开发空间（读取前同步底层实际状态）."""
        space = await self._get_or_raise(space_id)
        return await self._sync_status(space)

    async def _sync_status(self, space: Space) -> Space:
        """按需将底层实际状态对齐到本地实体（lazy sync - backend 无关）。

        按 describe_space 三态契约消费:
        - {"status": <SpaceStatus 值>} → 同步该状态
        - {"status": "stopped"} (资源不存在) → 同步为 stopped
        - None (无法映射) → 不变更状态
        """
        if space.status == SpaceStatus.DELETED:
            return space

        backend = self._backends.get(space.backend)
        if not backend:
            logger.warning("space_backend_missing", space_id=space.id, backend=space.backend.value)
            return space

        try:
            info = await backend.describe_space(space)
        except Exception as e:
            logger.warning("space_status_sync_failed", space_id=space.id, error=str(e))
            return space

        # 消费三态契约
        if info is None or not isinstance(info, dict):
            # None 或非 dict → 无可用状态，不变更
            return space

        status_str = info.get("status")
        if status_str is None:
            # status 为 None → 不变更
            return space

        try:
            mapped_status = SpaceStatus(status_str)
        except ValueError:
            logger.warning("unmapped_space_status", space_id=space.id, status=status_str)
            return space

        # 状态无变化 → 不变更
        if mapped_status == space.status:
            return space

        logger.info(
            "space_status_synced",
            space_id=space.id,
            from_status=space.status.value,
            to_status=mapped_status.value,
        )
        space.status = mapped_status
        space.touch()
        return await self._space_repository.update(space)

    async def list_spaces(
        self,
        owner_id: int | None = None,
        status: SpaceStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Space], int]:
        """列出开发空间 (支持过滤和分页)，返回前对齐底层实际状态。"""
        spaces, total = await self._space_repository.list_spaces(
            owner_id=owner_id,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        synced = await asyncio.gather(*(self._sync_status(space) for space in spaces))
        return list(synced), total

    async def start_space(self, space_id: str) -> Space:
        """启动开发空间 - backend 无关分发。"""
        space = await self._get_or_raise(space_id)
        space = await self._sync_status(space)

        # 同步后已在运行或启动中：幂等返回
        if space.status in (SpaceStatus.RUNNING, SpaceStatus.PENDING):
            return space

        # 校验状态机（failed/stopped 可启动）
        space.mark_starting()

        backend = self._backends[space.backend]
        start_time = time.monotonic()
        await backend.start_space(space)
        elapsed_seconds = time.monotonic() - start_time

        logger.info(
            "space_starting",
            space_id=space_id,
            backend=space.backend.value,
            elapsed_seconds=round(elapsed_seconds, 2),
        )

        # 检查是否超过启动 SLA
        if elapsed_seconds > STARTUP_SLA_SECONDS:
            logger.warning(
                "space_startup_sla_exceeded",
                space_id=space_id,
                elapsed_seconds=round(elapsed_seconds, 2),
                sla_seconds=STARTUP_SLA_SECONDS,
            )

        # 上报启动耗时到 CloudWatch Metrics
        await self._record_startup_metric(space_id, elapsed_seconds)

        return await self._space_repository.update(space)

    async def stop_space(self, space_id: str) -> Space:
        """停止开发空间 - backend 无关分发。"""
        space = await self._get_or_raise(space_id)
        space = await self._sync_status(space)

        # 同步后发现已停止：幂等返回
        if space.status == SpaceStatus.STOPPED:
            return space

        space.stop()

        backend = self._backends[space.backend]
        await backend.stop_space(space)

        logger.info("space_stopping", space_id=space_id, space_name=space.space_name)

        return await self._space_repository.update(space)

    async def get_space_access_url(self, space_id: str, conn_type: str = "web-ui") -> str:
        """签发空间 IDE 的免登录访问 URL（仅运行中可用）- backend 无关分发。

        Args:
            space_id: 空间 ID
            conn_type: 连接类型 (web-ui | vscode-remote)

        Raises:
            InvalidSpaceStateError: 空间非运行中
        """
        space = await self._get_or_raise(space_id)
        space = await self._sync_status(space)

        if space.status != SpaceStatus.RUNNING:
            raise InvalidSpaceStateError(
                space_id=space.id or "",
                current_state=space.status.value,
                operation="open",
            )

        backend = self._backends[space.backend]
        return await backend.create_access_url(space, conn_type)

    async def delete_space(self, space_id: str) -> None:
        """删除开发空间 - backend 无关分发。"""
        space = await self._get_or_raise(space_id)
        space = await self._sync_status(space)

        space.delete()

        backend = self._backends[space.backend]
        await backend.delete_space(space)

        logger.info("space_deleted", space_id=space_id, space_name=space.space_name)

        await self._space_repository.soft_delete(space_id)

    # ── 定期状态同步 ──────────────────────────────────────────────

    async def start_periodic_sync(self, interval_seconds: float = 30.0) -> None:
        """启动定期 Space 状态同步后台任务 (默认 30 秒间隔)."""
        self._sync_interval = interval_seconds
        self._sync_task = asyncio.create_task(self._periodic_sync_loop())
        logger.info("space_sync_started", interval_seconds=interval_seconds)

    async def _periodic_sync_loop(self) -> None:
        """定期同步所有活跃 Space 的 SageMaker 状态。"""
        while True:
            try:
                await self._sync_all_active_spaces()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("space_periodic_sync_failed")
            await asyncio.sleep(self._sync_interval)

    async def _sync_all_active_spaces(self) -> None:
        """同步所有非终态 Space 的状态（backend 无关）。"""
        active_statuses = [SpaceStatus.PENDING, SpaceStatus.RUNNING]
        spaces = await self._space_repository.list_by_statuses(active_statuses)
        for space in spaces:
            try:
                await self._sync_status(space)
            except Exception:
                logger.warning("space_sync_single_failed", space_id=space.id)

    async def stop_periodic_sync(self) -> None:
        """停止定期同步。"""
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
        logger.info("space_sync_stopped")

    # ── Metrics ──────────────────────────────────────────────────

    async def _record_startup_metric(self, space_id: str, elapsed_seconds: float) -> None:
        """上报 Space 启动耗时到 CloudWatch Metrics (可选依赖)."""
        if self._metrics_service is None:
            return
        try:
            await self._metrics_service.record_startup_time(
                space_id=space_id,
                startup_seconds=elapsed_seconds,
            )
        except Exception:
            # Metrics 上报失败不影响主流程
            logger.warning("space_startup_metric_record_failed", space_id=space_id)
