"""Dataset 仓库实现 - SQLAlchemy 数据访问。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.datasets.domain.entities import Dataset
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)
from src.modules.datasets.infrastructure.models import DatasetModel
from src.shared.infrastructure.repository_base import EnhancedBaseRepository


class DatasetRepositoryImpl(
    EnhancedBaseRepository[Dataset, DatasetModel, int],
    IDatasetRepository,
):
    """Dataset 仓库 SQLAlchemy 实现。"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DatasetModel)

    def _to_entity(self, model: DatasetModel) -> Dataset:
        """ORM 模型转换为领域实体。"""
        return Dataset(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            storage_type=DatasetStorageType(model.storage_type.value),
            storage_uri=model.storage_uri,
            total_size_bytes=model.total_size_bytes,
            file_count=model.file_count,
            dataset_type=DatasetType(model.dataset_type.value),
            data_format=model.data_format,
            tags=model.tags,
            visibility=DatasetVisibility(model.visibility.value),
            owner_id=model.owner_id,
            status=DatasetStatus(model.status.value),
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_accessed_at=model.last_accessed_at,
        )

    def _to_model(self, entity: Dataset) -> DatasetModel:
        """领域实体转换为 ORM 模型。"""
        return DatasetModel(
            name=entity.name,
            description=entity.description,
            version=entity.version,
            storage_type=entity.storage_type,
            storage_uri=entity.storage_uri,
            total_size_bytes=entity.total_size_bytes,
            file_count=entity.file_count,
            dataset_type=entity.dataset_type,
            data_format=entity.data_format,
            tags=entity.tags,
            visibility=entity.visibility,
            owner_id=entity.owner_id,
            status=entity.status,
            last_accessed_at=entity.last_accessed_at,
        )

    def _update_model(self, model: DatasetModel, entity: Dataset) -> None:
        """更新 ORM 模型字段。"""
        model.name = entity.name
        model.description = entity.description
        model.version = entity.version
        model.storage_type = entity.storage_type
        model.storage_uri = entity.storage_uri
        model.total_size_bytes = entity.total_size_bytes
        model.file_count = entity.file_count
        model.dataset_type = entity.dataset_type
        model.data_format = entity.data_format
        model.tags = entity.tags
        model.visibility = entity.visibility
        model.status = entity.status
        model.last_accessed_at = entity.last_accessed_at

    # ========== IDatasetRepository 接口方法 ==========

    async def add(self, dataset: Dataset) -> Dataset:
        """添加新数据集（委托给 EnhancedBaseRepository.create）。"""
        return await self.create(dataset)

    # ========== 领域特定查询方法 ==========

    async def get_by_name_and_version(self, name: str, version: str) -> Dataset | None:
        """根据名称和版本获取数据集。"""
        result = await self._session.execute(
            select(DatasetModel).where(
                DatasetModel.name == name,
                DatasetModel.version == version,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

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
        """列出用户的数据集。"""
        query = select(DatasetModel).where(DatasetModel.owner_id == owner_id)
        count_query = select(func.count(DatasetModel.id)).where(DatasetModel.owner_id == owner_id)

        # 应用过滤条件
        if status is not None:
            query = query.where(DatasetModel.status == status)
            count_query = count_query.where(DatasetModel.status == status)

        if dataset_type is not None:
            query = query.where(DatasetModel.dataset_type == dataset_type)
            count_query = count_query.where(DatasetModel.dataset_type == dataset_type)

        if visibility is not None:
            query = query.where(DatasetModel.visibility == visibility)
            count_query = count_query.where(DatasetModel.visibility == visibility)

        # 获取总数
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # 应用排序
        sort_column = getattr(DatasetModel, sort_by, DatasetModel.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models], total

    async def list_public(
        self,
        dataset_type: DatasetType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Dataset], int]:
        """列出公开数据集。"""
        query = select(DatasetModel).where(
            DatasetModel.visibility == DatasetVisibility.PUBLIC,
            DatasetModel.status == DatasetStatus.AVAILABLE,
        )
        count_query = select(func.count(DatasetModel.id)).where(
            DatasetModel.visibility == DatasetVisibility.PUBLIC,
            DatasetModel.status == DatasetStatus.AVAILABLE,
        )

        # 应用类型过滤
        if dataset_type is not None:
            query = query.where(DatasetModel.dataset_type == dataset_type)
            count_query = count_query.where(DatasetModel.dataset_type == dataset_type)

        # 获取总数
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # 默认按创建时间降序排序
        query = query.order_by(DatasetModel.created_at.desc())

        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models], total

    async def exists_by_name_and_version(self, name: str, version: str) -> bool:
        """检查名称+版本是否已存在。"""
        result = await self._session.execute(
            select(func.count(DatasetModel.id)).where(
                DatasetModel.name == name,
                DatasetModel.version == version,
            )
        )
        count = result.scalar() or 0
        return count > 0
