"""统一的基础仓库实现 - 合并 BaseRepositoryImpl 和 EnhancedBaseRepository."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.exceptions import EntityNotFoundError
from src.shared.infrastructure.query_builder import QueryBuilder
from src.shared.utils import utc_now

EntityT = TypeVar("EntityT")
ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT", int, str)


class BaseRepository(ABC, Generic[EntityT, ModelT, IdT]):
    """统一的基础仓库实现，提供完整的 CRUD 和查询功能。

    合并了原来的 BaseRepositoryImpl 和 EnhancedBaseRepository，
    消除重复代码，提供一致的接口。

    子类只需实现：
    - _to_entity(): ORM 模型到领域实体的转换
    - _to_model(): 领域实体到 ORM 模型的转换
    - _update_model(): 更新 ORM 模型字段
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelT]):
        """初始化仓库。

        Args:
            session: SQLAlchemy 异步会话
            model_class: ORM 模型类
        """
        self._session = session
        self._model_class = model_class

    @abstractmethod
    def _to_entity(self, model: ModelT) -> EntityT:
        """转换 ORM 模型到领域实体。子类必须实现。"""

    @abstractmethod
    def _to_model(self, entity: EntityT) -> ModelT:
        """转换领域实体到 ORM 模型。子类必须实现。"""

    @abstractmethod
    def _update_model(self, model: ModelT, entity: EntityT) -> None:
        """从实体更新 ORM 模型字段。子类必须实现。

        仅更新可变字段，不包括 ID 和时间戳。
        """

    def _get_id_column(self) -> Any:
        """获取主键列。如果主键不是 'id'，子类应覆盖此方法。"""
        return getattr(self._model_class, "id")

    def _get_entity_type_name(self) -> str:
        """获取实体类型名称用于错误消息。"""
        return self._model_class.__name__.replace("Model", "")

    # ========== 基础 CRUD 操作 ==========

    async def get_by_id(self, id: IdT) -> EntityT | None:
        """根据主键获取实体。"""
        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column == id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id_or_raise(self, id: IdT) -> EntityT:
        """根据主键获取实体，不存在则抛出异常。"""
        entity = await self.get_by_id(id)
        if entity is None:
            raise EntityNotFoundError(self._get_entity_type_name(), str(id))
        return entity

    async def create(self, entity: EntityT) -> EntityT:
        """创建新实体。"""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: EntityT) -> EntityT:
        """更新现有实体。"""
        id_value = getattr(entity, "id")
        id_column = self._get_id_column()

        result = await self._session.execute(select(self._model_class).where(id_column == id_value))
        model = result.scalar_one_or_none()

        if model is None:
            raise EntityNotFoundError(self._get_entity_type_name(), str(id_value))

        self._update_model(model, entity)

        # 更新时间戳
        if hasattr(model, "updated_at"):
            model.updated_at = utc_now()

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: IdT) -> bool:
        """硬删除实体。"""
        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column == id))
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def soft_delete(self, id: IdT) -> bool:
        """软删除实体（如果支持）。"""
        if not hasattr(self._model_class, "deleted_at"):
            return await self.delete(id)

        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column == id))
        model = result.scalar_one_or_none()

        if model is None:
            return False

        # 使用 setattr 来设置属性，因为 TypeVar 无法推断具体属性
        setattr(model, "deleted_at", utc_now())
        if hasattr(model, "updated_at"):
            setattr(model, "updated_at", utc_now())

        await self._session.flush()
        return True

    # ========== 存在性检查 ==========

    async def exists(self, id: IdT) -> bool:
        """检查实体是否存在。"""
        id_column = self._get_id_column()
        result = await self._session.execute(select(func.count(id_column)).where(id_column == id))
        count = result.scalar() or 0
        return count > 0

    async def exists_by(self, column_name: str, value: Any) -> bool:
        """根据任意列值检查实体是否存在。"""
        column = getattr(self._model_class, column_name, None)
        if column is None:
            return False

        query = select(func.count(self._get_id_column())).where(column == value)

        # 应用软删除过滤
        if hasattr(self._model_class, "deleted_at"):
            deleted_at_col = getattr(self._model_class, "deleted_at")
            query = query.where(deleted_at_col.is_(None))

        result = await self._session.execute(query)
        count = result.scalar() or 0
        return count > 0

    # ========== 查询构建辅助 ==========

    def _create_query_builder(self) -> QueryBuilder[ModelT]:
        """创建查询构建器实例。"""
        query = select(self._model_class)
        return QueryBuilder(query, self._model_class)

    async def list_with_filters(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_soft_deleted: bool = False,
    ) -> tuple[list[EntityT], int]:
        """带过滤和分页的列表查询。"""
        builder = self._create_query_builder()

        # 应用软删除过滤
        if not include_soft_deleted:
            builder = builder.with_soft_delete_filter()

        # 应用自定义过滤
        if filters:
            for column_name, value in filters.items():
                if value is not None:
                    builder = builder.with_filter(column_name, value)

        # 应用排序
        builder = builder.with_order_by(sort_by, sort_order)

        # 获取总数
        total = await builder.count(self._session)

        # 应用分页
        builder = builder.with_pagination(page, page_size)

        # 执行查询
        items = await builder.execute(self._session)

        # 转换为实体
        entities = [self._to_entity(item) for item in items]

        return entities, total

    # ========== 批量操作 ==========

    async def create_many(self, entities: list[EntityT]) -> list[EntityT]:
        """批量创建多个实体。"""
        models = [self._to_model(entity) for entity in entities]
        self._session.add_all(models)
        await self._session.flush()

        # 刷新所有模型以获取生成的 ID
        for model in models:
            await self._session.refresh(model)

        return [self._to_entity(model) for model in models]

    async def get_by_ids(self, ids: list[IdT]) -> list[EntityT]:
        """根据多个 ID 获取实体。"""
        if not ids:
            return []

        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column.in_(ids)))
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]
