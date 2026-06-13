"""CRUD 操作相关的 Mixin 类."""

from collections.abc import Callable
from typing import Any, TypeVar

from src.shared.domain.exceptions import EntityNotFoundError

T = TypeVar("T")  # 实体类型
ID = TypeVar("ID")  # ID 类型


class CRUDOperationsMixin:
    """提供 CRUD 操作功能的 Mixin 类.

    提供的功能：
    - 根据 ID 获取实体
    - 根据字段获取实体
    - 创建实体
    - 更新实体
    - 删除实体 (支持软删除)
    - 列表查询 (支持分页和过滤)
    """

    # 这些属性由主类提供
    _repository: Any
    _entity_type: str
    _not_found_error_factory: Callable[[str], Exception] | None

    def _create_not_found_error(self, entity_id: str) -> Exception:
        """创建未找到错误.

        可通过 _not_found_error_factory 自定义.
        """
        if self._not_found_error_factory is not None:
            return self._not_found_error_factory(entity_id)
        return EntityNotFoundError(self._entity_type, entity_id)

    async def _get_or_raise(self, entity_id: ID) -> T:
        """根据 ID 获取实体或抛出未找到错误."""
        entity = await self._repository.get_by_id(entity_id)
        if entity is None:
            raise self._create_not_found_error(str(entity_id))
        return entity  # type: ignore

    async def _get_by_field_or_none(self, field_name: str, field_value: Any) -> Any:
        """根据任意字段获取实体.

        返回类型为 Any: 仓库的 get_by_{field} 方法通过 getattr 动态解析，
        实体类型由具体子类决定，无法在 Mixin 层静态约束。
        """
        method_name = f"get_by_{field_name}"
        if hasattr(self._repository, method_name):
            method = getattr(self._repository, method_name)
            result = await method(field_value)
            return result
        return None

    async def _get_by_field_or_raise(self, field_name: str, field_value: Any) -> T:
        """根据任意字段获取实体或抛出未找到错误."""
        entity: T | None = await self._get_by_field_or_none(field_name, field_value)
        if entity is None:
            raise self._create_not_found_error(f"{field_name}={field_value}")
        return entity

    async def _ensure_exists(self, entity_id: ID) -> None:
        """确保实体存在，否则抛出未找到错误."""
        if hasattr(self._repository, "exists"):
            exists_method = getattr(self._repository, "exists")
            if not await exists_method(entity_id):
                raise self._create_not_found_error(str(entity_id))
        else:
            await self._get_or_raise(entity_id)

    async def get_by_id(self, entity_id: ID) -> T:
        """根据 ID 获取实体."""
        return await self._get_or_raise(entity_id)

    async def list_entities(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[T], int]:
        """列出带过滤和分页的实体."""
        # 尝试使用仓库的 list_with_filters 方法
        if hasattr(self._repository, "list_with_filters"):
            return await self._repository.list_with_filters(  # type: ignore
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        # 回退到通用的 list 方法
        elif hasattr(self._repository, "list"):
            return await self._repository.list(  # type: ignore
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        else:
            # 如果没有可用的列表方法，返回空列表
            return [], 0

    async def create_entity(
        self,
        data: dict[str, Any],
        unique_fields: list[str] | None = None,
    ) -> T:
        """创建带验证的新实体.

        注意: 唯一性验证需要 ValidationMixin.
        """
        # 验证唯一字段 (如果主类有 ValidationMixin)
        if unique_fields and hasattr(self, "_validate_unique_field"):
            for field in unique_fields:
                if field in data:
                    await self._validate_unique_field(field, data[field])

        # 创建实体
        return await self._repository.create(data)  # type: ignore

    async def update_entity(
        self,
        entity_id: ID,
        data: dict[str, Any],
    ) -> T:
        """更新现有实体."""
        entity: T = await self._get_or_raise(entity_id)

        # 更新实体属性
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # 保存更改
        return await self._repository.update(entity)  # type: ignore

    async def delete_entity(
        self,
        entity_id: ID,
        soft_delete: bool = True,
    ) -> None:
        """删除实体."""
        await self._get_or_raise(entity_id)  # 验证存在

        if soft_delete and hasattr(self._repository, "soft_delete"):
            soft_delete_method = getattr(self._repository, "soft_delete")
            await soft_delete_method(entity_id)
        elif hasattr(self._repository, "delete"):
            delete_method = getattr(self._repository, "delete")
            await delete_method(entity_id)
