"""Pydantic V2 优化的仓库基类 - 自动化 Entity ↔ Model 转换。"""

from enum import Enum
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.exceptions import EntityNotFoundError
from src.shared.domain.pydantic_entity import PydanticEntity
from src.shared.infrastructure.query_builder import QueryBuilder
from src.shared.utils import utc_now

EntityT = TypeVar("EntityT", bound=PydanticEntity)
ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT", int, str)


class PydanticRepository(Generic[EntityT, ModelT, IdT]):
    """Pydantic V2 优化的仓库基类。

    利用 PydanticEntity 的 from_orm 和 to_model_dict 实现自动转换。

    子类只需定义类属性：
    - _entity_class: 实体类型（必须）
    - _updatable_fields: 允许更新的字段列表（可选，默认自动推断）
    - _exclude_from_model: 创建模型时排除的字段（可选）

    使用示例:
    ```python
    class UserRepository(PydanticRepository[User, UserModel, int]):
        _entity_class = User
        _updatable_fields = ["username", "email", "status"]

        def __init__(self, session: AsyncSession):
            super().__init__(session, UserModel)
    ```
    """

    # 子类配置 - 必须定义
    _entity_class: type[EntityT]

    # 子类配置 - 可选
    _updatable_fields: list[str] | None = None
    _exclude_from_model: set[str] = {"created_at", "updated_at"}

    def __init__(self, session: AsyncSession, model_class: type[ModelT]):
        """初始化仓库。"""
        self._session = session
        self._model_class = model_class

    def _to_entity(self, model: ModelT) -> EntityT:
        """ORM 模型 → 领域实体（自动转换）。"""
        return self._entity_class.from_orm(model)

    def _to_model(self, entity: EntityT) -> ModelT:
        """领域实体 → ORM 模型（新建时）。"""
        exclude = self._exclude_from_model.copy()
        if entity.id is None:
            exclude.add("id")

        data = entity.to_model_dict(exclude=exclude)
        return self._model_class(**data)

    def _update_model(self, model: ModelT, entity: EntityT) -> None:
        """更新 ORM 模型（只更新指定字段）。"""
        if self._updatable_fields:
            fields = self._updatable_fields
        else:
            # 默认：排除 id, created_at, updated_at, owner_id
            exclude = {"id", "created_at", "updated_at", "owner_id"}
            fields = [f for f in entity.model_fields.keys() if f not in exclude]

        for field_name in fields:
            if hasattr(entity, field_name):
                value = getattr(entity, field_name)
                # SQLAlchemy Enum 列可以直接接收枚举值
                setattr(model, field_name, value)

    def _get_id_column(self) -> Any:
        """获取主键列。"""
        return getattr(self._model_class, "id")

    def _get_entity_type_name(self) -> str:
        """获取实体类型名称用于错误消息。"""
        return self._entity_class.__name__

    # ========== 基础 CRUD 操作 ==========

    async def get_by_id(self, id: IdT) -> EntityT | None:
        """根据主键获取实体。"""
        id_column = self._get_id_column()
        result = await self._session.execute(
            select(self._model_class).where(id_column == id)
        )
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
        id_value = entity.id
        id_column = self._get_id_column()

        result = await self._session.execute(
            select(self._model_class).where(id_column == id_value)
        )
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
        result = await self._session.execute(
            select(self._model_class).where(id_column == id)
        )
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
        result = await self._session.execute(
            select(self._model_class).where(id_column == id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.deleted_at = utc_now()
        if hasattr(model, "updated_at"):
            model.updated_at = utc_now()

        await self._session.flush()
        return True

    # ========== 存在性检查 ==========

    async def exists(self, id: IdT) -> bool:
        """检查实体是否存在。"""
        id_column = self._get_id_column()
        result = await self._session.execute(
            select(func.count(id_column)).where(id_column == id)
        )
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
            query = query.where(self._model_class.deleted_at.is_(None))

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

        for model in models:
            await self._session.refresh(model)

        return [self._to_entity(model) for model in models]

    async def get_by_ids(self, ids: list[IdT]) -> list[EntityT]:
        """根据多个 ID 获取实体。"""
        if not ids:
            return []

        id_column = self._get_id_column()
        result = await self._session.execute(
            select(self._model_class).where(id_column.in_(ids))
        )
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]
