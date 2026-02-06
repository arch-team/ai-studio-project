"""验证相关的 Mixin 类."""

from typing import Any, TypeVar

from src.shared.domain.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
)
from src.shared.domain.interfaces import IEntityExistenceChecker

ID = TypeVar("ID")  # ID 类型


class ValidationMixin:
    """提供验证相关功能的 Mixin 类.

    提供的功能：
    - 字段唯一性验证
    - 实体存在性验证
    - 批量实体存在性验证
    """

    # 这些属性由主类提供
    _repository: Any
    _entity_type: str

    def _create_duplicate_error(self, field: str, value: str) -> Exception:
        """创建重复实体错误."""
        return DuplicateEntityError(self._entity_type, f"{field}={value}")

    async def _validate_unique_field(self, field_name: str, field_value: Any) -> None:
        """验证字段值唯一性.

        按以下顺序尝试:
        1. 特定的 exists_by_xxx 方法
        2. 通用的 exists_by 方法
        """
        # 尝试特定的 exists_by_xxx 方法
        method_name = f"exists_by_{field_name}"
        if hasattr(self._repository, method_name):
            exists_method = getattr(self._repository, method_name)
            if await exists_method(field_value):
                raise self._create_duplicate_error(field_name, str(field_value))
        # 回退到通用的 exists_by 方法
        elif hasattr(self._repository, "exists_by"):
            if await self._repository.exists_by(field_name, field_value):
                raise self._create_duplicate_error(field_name, str(field_value))

    async def _validate_entity_exists(
        self,
        checker: IEntityExistenceChecker | None,
        entity_type: str,
        entity_id: ID,
    ) -> None:
        """验证相关实体存在."""
        if checker and not await checker.exists(entity_id):  # type: ignore
            raise EntityNotFoundError(entity_type, str(entity_id))

    async def _validate_entities_exist(
        self,
        validations: list[tuple[IEntityExistenceChecker | None, str, ID]],
    ) -> None:
        """验证多个相关实体存在."""
        for checker, entity_type, entity_id in validations:
            await self._validate_entity_exists(checker, entity_type, entity_id)
