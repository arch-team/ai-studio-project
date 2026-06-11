"""Dataset 仓库实现 - SQLAlchemy 数据访问。"""

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import Dataset
from ...domain.repositories import IDatasetRepository
from ...domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)
from ..models import DatasetModel


class DatasetRepositoryImpl(PydanticRepository[Dataset, DatasetModel, int], IDatasetRepository):
    """Dataset 仓库 SQLAlchemy 实现。

    使用 PydanticRepository 自动处理 Entity ↔ Model 转换。
    """

    _entity_class = Dataset
    _updatable_fields = [
        "name",
        "description",
        "version",
        "storage_type",
        "storage_uri",
        "total_size_bytes",
        "file_count",
        "dataset_type",
        "data_format",
        "tags",
        "visibility",
        "status",
        "last_accessed_at",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, DatasetModel)

    # ========== IDatasetRepository 接口方法 ==========

    async def add(self, dataset: Dataset) -> Dataset:
        """添加新数据集（委托给 PydanticRepository.create）。"""
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
        storage_type: DatasetStorageType | None = None,
        visibility: DatasetVisibility | None = None,
        search: str | None = None,
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

        if storage_type is not None:
            query = query.where(DatasetModel.storage_type == storage_type)
            count_query = count_query.where(DatasetModel.storage_type == storage_type)

        if visibility is not None:
            query = query.where(DatasetModel.visibility == visibility)
            count_query = count_query.where(DatasetModel.visibility == visibility)

        # 全文搜索 - 使用 MySQL MATCH...AGAINST（利用 ft_name_desc 索引）
        if search is not None:
            ft_condition = text("MATCH(name, description) AGAINST(:search IN BOOLEAN MODE)").bindparams(search=search)
            query = query.where(ft_condition)
            count_query = count_query.where(ft_condition)

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
