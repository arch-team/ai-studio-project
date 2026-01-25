"""UploadSession 仓库接口 - 上传会话数据访问契约定义。"""

from abc import ABC, abstractmethod
from datetime import datetime

from ..value_objects import UploadSession, UploadStatus


class IUploadSessionRepository(ABC):
    """UploadSession 仓库抽象接口。"""

    @abstractmethod
    async def get_by_id(self, session_id: int) -> UploadSession | None:
        """根据 ID 获取上传会话。"""

    @abstractmethod
    async def get_by_upload_id(self, upload_id: str) -> UploadSession | None:
        """根据 S3 upload_id 获取上传会话。"""

    @abstractmethod
    async def get_active_by_dataset(self, dataset_id: int) -> UploadSession | None:
        """获取数据集的活跃上传会话 (INITIATED 或 IN_PROGRESS)。

        一个数据集同时只能有一个活跃上传会话。
        """

    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: int,
        status: UploadStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UploadSession], int]:
        """列出用户的上传会话。

        Args:
            owner_id: 所有者 ID
            status: 状态过滤
            page: 页码
            page_size: 每页大小

        Returns:
            (上传会话列表, 总数)
        """

    @abstractmethod
    async def add(self, session: UploadSession) -> UploadSession:
        """添加新上传会话。

        Returns:
            添加后的上传会话（含生成的 ID）
        """

    @abstractmethod
    async def update(self, session: UploadSession) -> UploadSession:
        """更新上传会话。

        Returns:
            更新后的上传会话
        """

    @abstractmethod
    async def delete(self, session_id: int) -> bool:
        """删除上传会话。

        Returns:
            是否删除成功
        """

    @abstractmethod
    async def exists(self, session_id: int) -> bool:
        """检查上传会话是否存在。"""

    @abstractmethod
    async def list_expired(
        self,
        before: datetime,
        limit: int = 100,
    ) -> list[UploadSession]:
        """列出过期的上传会话 (用于清理)。

        Args:
            before: 过期时间阈值
            limit: 返回数量限制

        Returns:
            过期的上传会话列表
        """
