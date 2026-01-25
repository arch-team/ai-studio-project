"""Dataset 仓库接口 - 数据访问契约定义。"""

from abc import ABC, abstractmethod

from ..entities import Dataset
from ..value_objects import DatasetStatus, DatasetType, DatasetVisibility


class IDatasetRepository(ABC):
    """Dataset 仓库抽象接口。"""

    @abstractmethod
    async def get_by_id(self, dataset_id: int) -> Dataset | None:
        """根据 ID 获取数据集。"""

    @abstractmethod
    async def get_by_name_and_version(self, name: str, version: str) -> Dataset | None:
        """根据名称和版本获取数据集（名称+版本唯一）。"""

    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: int,
        status: DatasetStatus | None = None,
        dataset_type: DatasetType | None = None,
        visibility: DatasetVisibility | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Dataset], int]:
        """列出用户的数据集。

        Args:
            owner_id: 所有者 ID
            status: 状态过滤
            dataset_type: 类型过滤
            visibility: 可见性过滤
            page: 页码
            page_size: 每页大小
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)

        Returns:
            (数据集列表, 总数)
        """

    @abstractmethod
    async def list_public(
        self,
        dataset_type: DatasetType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Dataset], int]:
        """列出公开数据集。

        Returns:
            (数据集列表, 总数)
        """

    @abstractmethod
    async def add(self, dataset: Dataset) -> Dataset:
        """添加新数据集。

        Returns:
            添加后的数据集（含生成的 ID）
        """

    @abstractmethod
    async def update(self, dataset: Dataset) -> Dataset:
        """更新数据集。

        Returns:
            更新后的数据集
        """

    @abstractmethod
    async def delete(self, dataset_id: int) -> bool:
        """删除数据集。

        Returns:
            是否删除成功
        """

    @abstractmethod
    async def exists(self, dataset_id: int) -> bool:
        """检查数据集是否存在。"""

    @abstractmethod
    async def exists_by_name_and_version(self, name: str, version: str) -> bool:
        """检查名称+版本是否已存在。"""
