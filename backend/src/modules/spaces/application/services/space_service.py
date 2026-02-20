"""Space Service - 开发空间管理业务逻辑."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import TYPE_CHECKING

import structlog

from src.modules.spaces.application.interfaces import ISageMakerSpacesClient
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.exceptions import DuplicateSpaceNameError
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import (
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.shared.application import BaseApplicationService
from src.shared.utils import utc_now

if TYPE_CHECKING:
    from src.modules.spaces.application.services.sagemaker_metrics_service import SpaceMetricsService

logger = structlog.get_logger(__name__)

# Space 启动 SLA 阈值 (秒)
STARTUP_SLA_SECONDS = 180  # 3 分钟

# IDE 类型映射: SpaceType -> SageMaker IDE 类型
_IDE_TYPE_MAP = {
    SpaceType.JUPYTER: "jupyterlab",
    SpaceType.VSCODE: "vscode",
    SpaceType.RSTUDIO: "jupyterlab",  # RStudio 使用 JupyterLab 容器
}


class SpaceService(BaseApplicationService[Space, str]):
    """开发空间管理服务."""

    def __init__(
        self,
        space_repository: ISpaceRepository,
        sagemaker_client: ISageMakerSpacesClient,
        metrics_service: SpaceMetricsService | None = None,
    ):
        super().__init__(space_repository, "Space")
        self._space_repository = space_repository
        self._sagemaker_client = sagemaker_client
        self._metrics_service = metrics_service
        self._sync_task: asyncio.Task[None] | None = None
        self._sync_interval: float = 30.0

    async def create_space(self, owner_id: int, data: dict) -> Space:
        """创建新的开发空间."""
        space_name = data["space_name"]

        # 检查同一所有者下的名称重复
        existing = await self._space_repository.get_by_name_and_owner(space_name, owner_id)
        if existing:
            raise DuplicateSpaceNameError(space_name, owner_id)

        space_type = SpaceType(data.get("space_type", "jupyter"))
        instance_type = SpaceInstanceType(data.get("instance_type", "ml.g5.xlarge"))
        storage_size_gb = data.get("storage_size_gb", 20)

        # 创建域实体
        space = Space(
            id=str(uuid.uuid4()),
            space_name=space_name,
            owner_id=owner_id,
            instance_type=instance_type,
            space_type=space_type,
            storage_size_gb=storage_size_gb,
            status=SpaceStatus.PENDING,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        # 调用 SageMaker API 创建 Space，同时记录启动耗时
        ide_type = _IDE_TYPE_MAP.get(space_type, "jupyterlab")
        start_time = time.monotonic()
        result = await self._sagemaker_client.create_space(
            name=space_name,
            instance_type=instance_type.value,
            ide_type=ide_type,
            lifecycle_config_arn=data.get("lifecycle_config_arn"),
            storage_size_gb=storage_size_gb,
        )
        elapsed_seconds = time.monotonic() - start_time

        # 记录 SageMaker ARN
        space.sagemaker_space_arn = result.get("arn")
        space.lifecycle_config_arn = data.get("lifecycle_config_arn")

        logger.info(
            "space_created",
            space_id=space.id,
            space_name=space_name,
            sagemaker_arn=space.sagemaker_space_arn,
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
        await self._record_startup_metric(space.id, elapsed_seconds)

        # 保存到数据库
        return await self._space_repository.create(space)

    async def get_space(self, space_id: str) -> Space:
        """根据 ID 获取开发空间."""
        return await self._get_or_raise(space_id)

    async def list_spaces(
        self,
        owner_id: int | None = None,
        status: SpaceStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Space], int]:
        """列出开发空间 (支持过滤和分页)."""
        return await self._space_repository.list_spaces(
            owner_id=owner_id,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def start_space(self, space_id: str) -> Space:
        """启动开发空间."""
        space = await self._get_or_raise(space_id)
        space.start()

        # 调用 SageMaker API 查询并确认 Space 存在，记录启动耗时
        start_time = time.monotonic()
        sagemaker_info = await self._sagemaker_client.describe_space(space.space_name)
        elapsed_seconds = time.monotonic() - start_time

        if sagemaker_info:
            logger.info(
                "space_starting",
                space_id=space_id,
                sagemaker_status=sagemaker_info.get("status"),
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
        """停止开发空间."""
        space = await self._get_or_raise(space_id)
        space.stop()

        # 查询 SageMaker Space 当前状态
        sagemaker_info = await self._sagemaker_client.describe_space(space.space_name)
        if sagemaker_info:
            logger.info(
                "space_stopping",
                space_id=space_id,
                sagemaker_status=sagemaker_info.get("status"),
            )

        return await self._space_repository.update(space)

    async def delete_space(self, space_id: str) -> None:
        """删除开发空间 (软删除)."""
        space = await self._get_or_raise(space_id)
        space.delete()

        # 调用 SageMaker API 删除 Space
        await self._sagemaker_client.delete_space(space.space_name)

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
        """同步所有非终态 Space 的状态。"""
        active_statuses = [SpaceStatus.PENDING, SpaceStatus.RUNNING]
        spaces = await self._space_repository.list_by_statuses(active_statuses)
        for space in spaces:
            try:
                info = await self._sagemaker_client.describe_space(space.space_name)
                if info and info.get("status"):
                    sagemaker_status = info["status"].lower()
                    # 映射 SageMaker 状态到平台状态
                    if sagemaker_status == "inservice" and space.status == SpaceStatus.PENDING:
                        space.start()
                        await self._space_repository.update(space)
                    elif sagemaker_status == "failed":
                        space.mark_failed(error_message=info.get("failure_reason", "Unknown"))
                        await self._space_repository.update(space)
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
