"""SageMaker Space 状态同步服务 (T090)."""

import structlog

from src.modules.spaces.application.interfaces import ISageMakerSpacesClient
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import SpaceStatus

logger = structlog.get_logger(__name__)


class SpaceSyncService:
    """SageMaker Space 状态同步服务.

    定期同步 SageMaker Space 的实际状态到本地数据库，
    确保平台显示的状态与 AWS 资源状态一致。
    建议同步间隔: 30 秒。
    """

    # SageMaker SDK 状态 → 平台状态映射
    SDK_STATUS_MAP: dict[str, str] = {
        "Pending": "pending",
        "InService": "running",
        "Stopping": "stopped",
        "Stopped": "stopped",
        "Failed": "failed",
        "Deleting": "deleted",
        "Update_Failed": "failed",
    }

    def __init__(
        self,
        space_repository: ISpaceRepository,
        sagemaker_client: ISageMakerSpacesClient,
    ) -> None:
        self._space_repository = space_repository
        self._sagemaker_client = sagemaker_client

    async def sync_space_status(self, space_id: str) -> None:
        """同步单个 Space 状态.

        从 SageMaker API 查询 Space 的实际状态，
        并更新到本地数据库。

        Args:
            space_id: 平台 Space ID
        """
        space = await self._space_repository.get_by_id(space_id)
        if not space:
            logger.warning("sync_space_not_found", space_id=space_id)
            return

        # 已删除的 Space 不需要同步
        if space.status == SpaceStatus.DELETED:
            return

        sagemaker_info = await self._sagemaker_client.describe_space(space.space_name)

        if sagemaker_info is None:
            # SageMaker 侧不存在，标记为已删除
            logger.warning("sync_space_missing_in_sagemaker", space_id=space_id, space_name=space.space_name)
            if space.status != SpaceStatus.DELETED:
                space.transition_to(SpaceStatus.DELETED)
                await self._space_repository.update(space)
            return

        # 映射 SageMaker 状态
        sagemaker_status = sagemaker_info.get("status", "Unknown")
        mapped_status_str = self.SDK_STATUS_MAP.get(sagemaker_status)

        if not mapped_status_str:
            logger.warning(
                "sync_unknown_sagemaker_status",
                space_id=space_id,
                sagemaker_status=sagemaker_status,
            )
            return

        mapped_status = SpaceStatus(mapped_status_str)

        # 状态未变化，跳过更新
        if space.status == mapped_status:
            return

        # 检查状态转换是否合法
        if space.can_transition_to(mapped_status):
            old_status = space.status.value
            space.transition_to(mapped_status)
            await self._space_repository.update(space)

            logger.info(
                "sync_space_status_updated",
                space_id=space_id,
                old_status=old_status,
                new_status=mapped_status.value,
                sagemaker_status=sagemaker_status,
            )
        else:
            logger.warning(
                "sync_invalid_transition",
                space_id=space_id,
                current_status=space.status.value,
                target_status=mapped_status.value,
                sagemaker_status=sagemaker_status,
            )

    async def sync_all_spaces(self) -> dict[str, int]:
        """同步所有活跃 Space 的状态.

        查询所有非已删除的 Space，逐个同步其 SageMaker 状态。

        Returns:
            同步统计: {"total": N, "updated": N, "failed": N, "skipped": N}
        """
        stats = {"total": 0, "updated": 0, "failed": 0, "skipped": 0}

        # 获取所有活跃 Space (非已删除状态)
        active_statuses = [SpaceStatus.PENDING, SpaceStatus.RUNNING, SpaceStatus.STOPPED, SpaceStatus.FAILED]

        for status in active_statuses:
            spaces, _ = await self._space_repository.list_spaces(
                status=status,
                page=1,
                page_size=1000,
            )

            for space in spaces:
                stats["total"] += 1
                if space.id is None:
                    stats["skipped"] += 1
                    continue
                space_id = space.id
                try:
                    old_status = space.status
                    await self.sync_space_status(space_id)

                    # 重新读取判断是否更新
                    updated_space = await self._space_repository.get_by_id(space_id)
                    if updated_space and updated_space.status != old_status:
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1

                except Exception as e:
                    stats["failed"] += 1
                    logger.error(
                        "sync_space_failed",
                        space_id=space.id,
                        error=str(e),
                    )

        logger.info("sync_all_completed", **stats)
        return stats
