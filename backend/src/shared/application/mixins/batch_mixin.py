"""批量操作相关的 Mixin 类."""

from typing import Any, TypeVar

T = TypeVar("T")  # 实体类型
ID = TypeVar("ID")  # ID 类型


class BatchOperationsMixin:
    """提供批量操作功能的 Mixin 类.

    提供的功能：
    - 批量创建实体
    - 批量获取实体
    """

    # 这些属性由主类提供
    _repository: Any

    async def create_many(
        self,
        items: list[dict[str, Any]],
        unique_fields: list[str] | None = None,
    ) -> list[T]:
        """创建多个实体.

        注意: 唯一性验证需要 ValidationMixin.
        """
        # 验证所有项目的唯一字段 (如果主类有 ValidationMixin)
        if unique_fields and hasattr(self, "_validate_unique_field"):
            for item in items:
                for field in unique_fields:
                    if field in item:
                        await self._validate_unique_field(field, item[field])

        # 创建所有实体
        if hasattr(self._repository, "create_many"):
            return await self._repository.create_many(items)  # type: ignore[no-any-return]
        else:
            # 回退到单独创建
            results = []
            for item in items:
                result = await self._repository.create(item)
                results.append(result)
            return results

    async def get_by_ids(self, entity_ids: list[ID]) -> list[T]:
        """根据多个 ID 获取实体."""
        if hasattr(self._repository, "get_by_ids"):
            return await self._repository.get_by_ids(entity_ids)  # type: ignore
        else:
            # 回退到单独获取
            results = []
            for entity_id in entity_ids:
                entity = await self._repository.get_by_id(entity_id)
                if entity:
                    results.append(entity)
            return results
