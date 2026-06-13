"""Space 后端策略接口。

两种开发环境后端（Studio / HyperPod）实现此接口，SpaceService 按 backend 分发。
"""

from abc import ABC, abstractmethod
from typing import Any

from src.modules.spaces.domain.entities import Space


class ISpaceBackendClient(ABC):
    """开发环境后端统一接口。"""

    @abstractmethod
    async def provision_space(self, space: Space) -> dict[str, Any]:
        """创建底层资源并拉起计算。

        Returns:
            需持久化的标识。studio: {"arn": ...}；hyperpod: {"namespace": ..., "workspace_name": ...}
        """

    @abstractmethod
    async def delete_space(self, space: Space) -> None:
        """删除底层资源（幂等）。"""

    @abstractmethod
    async def start_space(self, space: Space) -> None:
        """拉起计算实例。"""

    @abstractmethod
    async def stop_space(self, space: Space) -> None:
        """释放计算实例，保留存储。"""

    @abstractmethod
    async def describe_space(self, space: Space) -> dict[str, Any] | None:
        """查询底层状态，返回 {"status": <平台 SpaceStatus 值>, ...}；不存在返回 None。"""

    @abstractmethod
    async def create_access_url(self, space: Space, conn_type: str) -> str:
        """签发免登录访问 URL。conn_type: web-ui | vscode-remote。"""
