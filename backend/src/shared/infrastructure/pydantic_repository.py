"""统一仓库基类 - 支持自动和手动 Entity ↔ Model 转换。"""

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.exceptions import EntityNotFoundError
from src.shared.infrastructure.query_builder import QueryBuilder
from src.shared.utils import utc_now

EntityT = TypeVar("EntityT")
ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT", int, str)


class PydanticRepository(Generic[EntityT, ModelT, IdT]):
    """统一仓库基类 - 支持自动和手动 Entity ↔ Model 转换。

    模式一（自动转换）: 设置 _entity_class 为 PydanticEntity 子类
    ```python
    class UserRepository(PydanticRepository[User, UserModel, int]):
        _entity_class = User
        _updatable_fields = ["username", "email", "status"]

        def __init__(self, session: AsyncSession):
            super().__init__(session, UserModel)
    ```

    模式二（手动转换）: 不设置 _entity_class，覆盖 _to_entity/_to_model/_update_model
    ```python
    class UploadSessionRepository(PydanticRepository[UploadSession, UploadSessionModel, int]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, UploadSessionModel)

        def _to_entity(self, model): ...
        def _to_model(self, entity): ...
        def _update_model(self, model, entity): ...
    ```
    """

    # 子类配置 - 可选（设置后启用自动转换）
    _entity_class: type[EntityT] | None = None

    # 子类配置 - 可选
    _updatable_fields: list[str] | None = None
    _exclude_from_model: set[str] = {"created_at", "updated_at"}

    # 默认排除的更新字段
    _default_exclude_fields: set[str] = {"id", "created_at", "updated_at", "owner_id"}

    def __init__(self, session: AsyncSession, model_class: type[ModelT]):
        self._session = session
        self._model_class = model_class

    def _to_entity(self, model: ModelT) -> EntityT:
        """ORM 模型 → 领域实体。子类可覆盖。"""
        if self._entity_class is not None and hasattr(self._entity_class, "from_orm"):
            return self._entity_class.from_orm(model)
        raise NotImplementedError("子类必须实现 _to_entity() 或设置 _entity_class")

    def _to_model(self, entity: EntityT) -> ModelT:
        """领域实体 → ORM 模型。子类可覆盖。"""
        if self._entity_class is not None and hasattr(entity, "to_model_dict"):
            exclude = self._exclude_from_model.copy()
            if getattr(entity, "id", None) is None:
                exclude.add("id")
            # convert_enums=False: 保留 enum 对象传给 ORM。
            # SQLAlchemy Enum() 列直接接受 enum 成员，由 SA 处理到数据库值的转换。
            # 这避免了 enum 值大小写与数据库 ENUM 列定义不匹配的问题。
            data = entity.to_model_dict(exclude=exclude, convert_enums=False)
            return self._model_class(**data)
        raise NotImplementedError("子类必须实现 _to_model() 或设置 _entity_class")

    def _update_model(self, model: ModelT, entity: EntityT) -> None:
        """更新 ORM 模型。子类可覆盖。"""
        if self._entity_class is not None and hasattr(self._entity_class, "model_fields"):
            for field_name in self._get_updatable_fields():
                if hasattr(entity, field_name):
                    setattr(model, field_name, getattr(entity, field_name))
            return
        raise NotImplementedError("子类必须实现 _update_model() 或设置 _entity_class")

    def _get_updatable_fields(self) -> list[str]:
        """获取可更新的字段列表。"""
        if self._updatable_fields:
            return self._updatable_fields
        return [f for f in self._entity_class.model_fields.keys() if f not in self._default_exclude_fields]

    def _get_id_column(self) -> Any:
        """获取主键列。"""
        return getattr(self._model_class, "id")

    def _get_entity_type_name(self) -> str:
        """获取实体类型名称用于错误消息。"""
        if self._entity_class is not None:
            return self._entity_class.__name__
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

        now = utc_now()
        setattr(model, "deleted_at", now)
        if hasattr(model, "updated_at"):
            setattr(model, "updated_at", now)

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

        if not include_soft_deleted:
            builder = builder.with_soft_delete_filter()

        if filters:
            for column_name, value in filters.items():
                if value is not None:
                    builder = builder.with_filter(column_name, value)

        builder = builder.with_order_by(sort_by, sort_order)
        total = await builder.count(self._session)
        builder = builder.with_pagination(page, page_size)
        items = await builder.execute(self._session)

        return [self._to_entity(item) for item in items], total

    # ========== 批量操作 ==========

    async def create_many(self, entities: list[EntityT]) -> list[EntityT]:
        """批量创建多个实体。"""
        models = [self._to_model(entity) for entity in entities]
        self._session.add_all(models)
        await self._session.flush()

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
