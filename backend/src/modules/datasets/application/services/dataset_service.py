"""数据集服务 - 管理数据集的业务逻辑。"""

from src.modules.datasets.domain.entities import Dataset
from src.modules.datasets.domain.exceptions import DatasetNotFoundError
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)
from src.shared.application.base_service_unified import BaseApplicationService
from src.shared.domain.exceptions import DuplicateEntityError
from src.shared.utils import utc_now


class DatasetService(BaseApplicationService[Dataset, int]):
    """数据集管理服务。"""

    def __init__(self, repository: IDatasetRepository):
        super().__init__(repository, "Dataset")
        self._not_found_error_factory = lambda id_: DatasetNotFoundError(dataset_id=id_)

    async def create_dataset(self, owner_id: int, data: dict) -> Dataset:
        """创建新数据集。

        Raises:
            DuplicateEntityError: 如果 name+version 已存在
        """
        name = data["name"]
        version = data.get("version", "v1")

        # 确保数据集名称和版本唯一
        if await self._repository.exists_by_name_and_version(name, version):
            raise DuplicateEntityError("Dataset", f"{name}/{version}")

        # 构建数据集实体
        dataset = Dataset(
            id=0,  # 数据库分配
            name=name,
            version=version,
            description=data.get("description"),
            storage_type=self.convert_enum(data["storage_type"], DatasetStorageType, DatasetStorageType.S3),
            storage_uri=data["storage_uri"],
            dataset_type=self.convert_enum(data["dataset_type"], DatasetType, DatasetType.CUSTOM),
            data_format=data.get("data_format"),
            tags=data.get("tags"),
            visibility=self.convert_enum(data.get("visibility"), DatasetVisibility, DatasetVisibility.PRIVATE),
            status=DatasetStatus.PREPARING,
            owner_id=owner_id,
        )
        return await self._repository.add(dataset)

    async def get_dataset(self, dataset_id: int) -> Dataset:
        """根据 ID 获取数据集。"""
        return await self._get_or_raise(dataset_id)

    async def list_datasets(
        self,
        owner_id: int | None = None,
        status: DatasetStatus | None = None,
        dataset_type: DatasetType | None = None,
        visibility: DatasetVisibility | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Dataset], int]:
        """列出用户数据集，支持过滤和分页。owner_id 为 None 时列出所有数据集。"""
        return await self._repository.list_by_owner(
            owner_id=owner_id if owner_id is not None else 0,  # 0 表示列出所有
            status=status,
            dataset_type=dataset_type,
            visibility=visibility,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update_dataset(self, dataset_id: int, data: dict) -> Dataset:
        """更新数据集元数据。

        Raises:
            DatasetNotFoundError: 如果数据集不存在
        """
        dataset = await self._get_or_raise(dataset_id)

        # 应用更新
        if "description" in data:
            dataset.description = data["description"]
        if "tags" in data:
            dataset.tags = data["tags"]
        if "visibility" in data and data["visibility"] is not None:
            dataset.visibility = self.convert_enum(data["visibility"], DatasetVisibility, dataset.visibility)

        dataset.updated_at = utc_now()
        return await self._repository.update(dataset)

    async def delete_dataset(self, dataset_id: int) -> None:
        """删除（归档）数据集。

        Raises:
            DatasetNotFoundError: 如果数据集不存在
        """
        dataset = await self._get_or_raise(dataset_id)

        # Soft delete by archiving
        if dataset.can_transition_to(DatasetStatus.ARCHIVED):
            dataset.archive()
        else:
            # Already archived or in error state - just update timestamp
            dataset.updated_at = utc_now()

        await self._repository.update(dataset)

    async def create_version(
        self,
        dataset_id: int,
        version: str,
        storage_uri: str | None = None,
        description: str | None = None,
    ) -> Dataset:
        """基于现有数据集创建新版本。

        Raises:
            DatasetNotFoundError: 如果源数据集不存在
            DuplicateEntityError: 如果版本号已存在
        """
        # Get source dataset
        source = await self._get_or_raise(dataset_id)

        # Validate unique name+version
        if await self._repository.exists_by_name_and_version(source.name, version):
            raise DuplicateEntityError("Dataset", f"{source.name}/{version}")

        # Create new version from source
        new_dataset = Dataset(
            id=0,
            name=source.name,
            version=version,
            description=description or source.description,
            storage_type=source.storage_type,
            storage_uri=storage_uri or source.storage_uri,
            dataset_type=source.dataset_type,
            data_format=source.data_format,
            tags=source.tags.copy() if source.tags else None,
            visibility=source.visibility,
            status=DatasetStatus.PREPARING,
            owner_id=source.owner_id,
        )

        return await self._repository.add(new_dataset)

    async def mark_available(self, dataset_id: int) -> Dataset:
        """标记数据集为可用状态。

        Raises:
            DatasetNotFoundError: 如果数据集不存在
            InvalidStateTransitionError: 如果状态转换无效
        """
        dataset = await self._get_or_raise(dataset_id)
        dataset.mark_available()
        return await self._repository.update(dataset)

    async def mark_error(self, dataset_id: int) -> Dataset:
        """标记数据集为错误状态。

        Raises:
            DatasetNotFoundError: 如果数据集不存在
            InvalidStateTransitionError: 如果状态转换无效
        """
        dataset = await self._get_or_raise(dataset_id)
        dataset.mark_error()
        return await self._repository.update(dataset)
