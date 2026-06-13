"""Studio Spaces 后端适配器 —— 将 SageMakerSpacesClient 适配为 ISpaceBackendClient。"""

from typing import Any

import structlog

from src.modules.spaces.application.interfaces import (
    ISageMakerSpacesClient,
    ISpaceBackendClient,
)
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.value_objects import SpaceStatus, SpaceType

logger = structlog.get_logger(__name__)

_IDE_TYPE_MAP = {
    SpaceType.JUPYTER: "jupyterlab",
    SpaceType.VSCODE: "vscode",
    SpaceType.RSTUDIO: "jupyterlab",
}

# SageMaker App 状态 → 平台状态
# Deleting/Deleted 均映射为 STOPPED：计算实例已释放（或释放中），不再对外提供服务。
_APP_STATUS_MAP = {
    "Pending": SpaceStatus.PENDING,
    "InService": SpaceStatus.RUNNING,
    "Deleting": SpaceStatus.STOPPED,
    "Deleted": SpaceStatus.STOPPED,
    "Failed": SpaceStatus.FAILED,
}


class StudioSpaceBackend(ISpaceBackendClient):
    """Studio Spaces 后端实现，封装 SageMaker Studio 的 Space+App 编排逻辑。"""

    def __init__(self, sagemaker_client: ISageMakerSpacesClient) -> None:
        self._sm = sagemaker_client

    def _ide_type(self, space: Space) -> str:
        """获取 IDE 类型映射。"""
        return _IDE_TYPE_MAP.get(space.space_type, "jupyterlab")

    async def provision_space(self, space: Space) -> dict[str, Any]:
        """创建 Studio Space + App，失败时清理孤儿资源。

        Returns:
            包含 SageMaker ARN 的字典 {"arn": "..."}
        """
        ide_type = self._ide_type(space)

        # 1. 创建 Space (配置+存储)
        result = await self._sm.create_space(
            name=space.space_name,
            instance_type=space.instance_type.value,
            ide_type=ide_type,
            lifecycle_config_arn=space.lifecycle_config_arn,
            storage_size_gb=space.storage_size_gb,
        )

        # 2. 拉起 App (真实计算实例)
        try:
            await self._sm.create_app(
                space_name=space.space_name,
                ide_type=ide_type,
                instance_type=space.instance_type.value,
                lifecycle_config_arn=space.lifecycle_config_arn,
            )
        except Exception:
            # 防止孤儿 Space：App 拉起失败时尽力清理已创建的 Space
            try:
                await self._sm.delete_space(space.space_name)
            except Exception as cleanup_error:
                logger.warning(
                    "space_orphan_cleanup_failed",
                    space_name=space.space_name,
                    error=str(cleanup_error),
                    exc_info=True,
                )
            raise

        return {"arn": result.get("arn")}

    async def delete_space(self, space: Space) -> None:
        """删除 App 后删除 Space (幂等)。"""
        await self._sm.delete_app(space_name=space.space_name, ide_type=self._ide_type(space))
        await self._sm.delete_space(space.space_name)

    async def start_space(self, space: Space) -> None:
        """拉起 App 计算实例。"""
        await self._sm.create_app(
            space_name=space.space_name,
            ide_type=self._ide_type(space),
            instance_type=space.instance_type.value,
            lifecycle_config_arn=space.lifecycle_config_arn,
        )

    async def stop_space(self, space: Space) -> None:
        """释放 App 计算实例 (EBS 文件保留)。"""
        await self._sm.delete_app(space_name=space.space_name, ide_type=self._ide_type(space))

    async def describe_space(self, space: Space) -> dict[str, Any] | None:
        """查询 App 状态并映射为平台状态。

        Returns:
            {"status": <SpaceStatus 值>}；App 不存在时返回 {"status": "stopped"}（明确"已停止"）；
            状态无法映射时返回 None（无可用状态信息，下游不变更状态）。
        """
        info = await self._sm.describe_app(space_name=space.space_name, ide_type=self._ide_type(space))

        # App 不存在 = 无运行实例 = 已停止
        if not isinstance(info, dict):
            return {"status": SpaceStatus.STOPPED.value}

        # 映射 SageMaker App 状态到平台状态
        mapped = _APP_STATUS_MAP.get(info.get("status", ""))
        if mapped:
            return {"status": mapped.value}

        # 未知/无法映射的状态：返回 None，下游视为"不变更状态"
        logger.warning("unmapped_app_status", status=info.get("status"), space_name=space.space_name)
        return None

    async def create_access_url(self, space: Space, conn_type: str) -> str:
        """签发免登录访问 URL (5 分钟有效)。

        Args:
            space: 空间实体
            conn_type: 连接类型 (web-ui | vscode-remote)，Studio 当前忽略此参数

        Returns:
            presigned URL
        """
        return await self._sm.create_presigned_url(space_name=space.space_name, ide_type=self._ide_type(space))
