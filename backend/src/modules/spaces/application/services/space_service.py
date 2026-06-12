"""Space Service - 开发空间管理业务逻辑."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import TYPE_CHECKING

import structlog

from src.modules.spaces.application.interfaces import ISageMakerSpacesClient
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.exceptions import (
    DuplicateSpaceNameError,
    InvalidSpaceStateError,
)
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

        # 调用 SageMaker API 创建 Space（配置+存储），同时记录启动耗时
        ide_type = _IDE_TYPE_MAP.get(space_type, "jupyterlab")
        start_time = time.monotonic()
        result = await self._sagemaker_client.create_space(
            name=space_name,
            instance_type=instance_type.value,
            ide_type=ide_type,
            lifecycle_config_arn=data.get("lifecycle_config_arn"),
            storage_size_gb=storage_size_gb,
        )

        # 拉起 App 计算实例——Space 只是配置，App 才是真实计费资源
        try:
            await self._sagemaker_client.create_app(
                space_name=space_name,
                ide_type=ide_type,
                instance_type=instance_type.value,
                lifecycle_config_arn=data.get("lifecycle_config_arn"),
            )
        except Exception:
            # 防止孤儿 SageMaker Space：App 拉起失败时尽力清理已创建的 Space
            try:
                await self._sagemaker_client.delete_space(space_name)
            except Exception:
                logger.warning("space_orphan_cleanup_failed", space_name=space_name)
            raise
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
        """根据 ID 获取开发空间（读取前同步 SageMaker 实际状态）."""
        space = await self._get_or_raise(space_id)
        return await self._sync_status_from_sagemaker(space)

    # SageMaker App 状态 → 平台状态映射。
    # App（计算实例）是真实计费资源和状态事实源：无 App / Deleted = 已停止。
    _APP_STATUS_MAP = {
        "Pending": SpaceStatus.PENDING,
        "InService": SpaceStatus.RUNNING,
        "Deleting": SpaceStatus.STOPPED,
        "Deleted": SpaceStatus.STOPPED,
        "Failed": SpaceStatus.FAILED,
    }

    def _ide_type_of(self, space: Space) -> str:
        return _IDE_TYPE_MAP.get(space.space_type, "jupyterlab")

    async def _ensure_app_not_deleting(self, space: Space, operation: str) -> None:
        """App 处于 Deleting 时拒绝操作（SageMaker 侧会 ResourceInUse）.

        Raises:
            InvalidSpaceStateError: App 删除中，需等待完成后重试
        """
        try:
            info = await self._sagemaker_client.describe_app(
                space_name=space.space_name,
                ide_type=self._ide_type_of(space),
            )
        except Exception:
            return
        if isinstance(info, dict) and info.get("status") == "Deleting":
            raise InvalidSpaceStateError(
                space_id=space.id or "",
                current_state="stopping",
                operation=operation,
            )

    async def _sync_status_from_sagemaker(self, space: Space) -> Space:
        """按需将 SageMaker App 实际状态对齐到本地实体（lazy sync）。

        App 计算实例的状态独立演进（Pending→InService、外部停止等），平台无后台
        轮询时本地状态会滞留。读写操作前调用本方法消除偏差。对齐外部事实直接赋值，
        不走业务状态机。同步失败不阻塞主流程。
        """
        if space.status == SpaceStatus.DELETED:
            return space
        try:
            info = await self._sagemaker_client.describe_app(
                space_name=space.space_name,
                ide_type=self._ide_type_of(space),
            )
        except Exception as e:
            logger.warning("space_status_sync_failed", space_id=space.id, error=str(e))
            return space

        # App 不存在 = 无运行实例 = 已停止
        mapped = self._APP_STATUS_MAP.get(info.get("status", "")) if isinstance(info, dict) else SpaceStatus.STOPPED
        if mapped is None or mapped == space.status:
            return space

        logger.info(
            "space_status_synced",
            space_id=space.id,
            from_status=space.status.value,
            to_status=mapped.value,
        )
        space.status = mapped
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
        """列出开发空间 (支持过滤和分页)，返回前对齐 SageMaker 实际状态.

        无后台轮询时列表页是用户主要观察入口，不同步会让状态滞留 pending。
        逐空间并发同步，单个失败不影响整体返回。
        """
        spaces, total = await self._space_repository.list_spaces(
            owner_id=owner_id,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        synced = await asyncio.gather(*(self._sync_status_from_sagemaker(space) for space in spaces))
        return list(synced), total

    async def start_space(self, space_id: str) -> Space:
        """启动开发空间——真实拉起 SageMaker App 计算实例.

        同步后若 App 已在运行/启动中则幂等返回；否则 create_app 并置为
        PENDING（启动中），后续读取经懒同步推进到 RUNNING。
        """
        space = await self._get_or_raise(space_id)
        space = await self._sync_status_from_sagemaker(space)

        # 同步后已在运行或启动中：幂等返回，避免重复 create_app
        if space.status in (SpaceStatus.RUNNING, SpaceStatus.PENDING):
            return space

        # 上一个 App 仍在删除中（停止后约 1 分钟窗口），create_app 会被
        # SageMaker 以 ResourceInUse 拒绝，提前给出明确的 409
        await self._ensure_app_not_deleting(space, operation="start")

        # 校验状态机（failed/stopped 可启动），再真实拉起实例
        space.mark_starting()

        start_time = time.monotonic()
        await self._sagemaker_client.create_app(
            space_name=space.space_name,
            ide_type=self._ide_type_of(space),
            instance_type=space.instance_type.value,
            lifecycle_config_arn=space.lifecycle_config_arn,
        )
        elapsed_seconds = time.monotonic() - start_time

        logger.info(
            "space_starting",
            space_id=space_id,
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
        """停止开发空间——真实删除 SageMaker App 释放计算实例（EBS 文件保留）."""
        space = await self._get_or_raise(space_id)
        space = await self._sync_status_from_sagemaker(space)

        # 同步后发现 App 已不在（外部停止）：幂等返回
        if space.status == SpaceStatus.STOPPED:
            return space

        space.stop()

        await self._sagemaker_client.delete_app(
            space_name=space.space_name,
            ide_type=self._ide_type_of(space),
        )

        logger.info("space_stopping", space_id=space_id, space_name=space.space_name)

        return await self._space_repository.update(space)

    async def delete_space(self, space_id: str) -> None:
        """删除开发空间——清理 App 后删除 SageMaker Space（含 EBS 数据）."""
        space = await self._get_or_raise(space_id)
        space = await self._sync_status_from_sagemaker(space)

        # App 删除中时 SageMaker DeleteSpace 会被 ResourceInUse 拒绝，提前 409
        await self._ensure_app_not_deleting(space, operation="delete")

        space.delete()

        # 先确保 App 已清理（delete_app 对不存在的 App 幂等），再删 Space
        await self._sagemaker_client.delete_app(
            space_name=space.space_name,
            ide_type=self._ide_type_of(space),
        )
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
        """同步所有非终态 Space 的状态（以 App 计算实例为事实源）。"""
        active_statuses = [SpaceStatus.PENDING, SpaceStatus.RUNNING]
        spaces = await self._space_repository.list_by_statuses(active_statuses)
        for space in spaces:
            try:
                await self._sync_status_from_sagemaker(space)
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
