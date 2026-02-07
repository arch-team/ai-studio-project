"""Query builder utility for common repository operations."""

from enum import Enum
from typing import Any, Generic, TypeVar

import structlog
from sqlalchemy import Select, asc, desc, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ModelT = TypeVar("ModelT")


class QueryBuilder(Generic[ModelT]):
    """Builder for common query operations: pagination, sorting, soft delete filter."""

    def __init__(self, query: Select[tuple[ModelT]], model_class: type[ModelT]):
        self._query: Select[tuple[ModelT]] = query
        self._model_class = model_class
        self._filters: list[Any] = []

    def _convert_enum_value(self, column_name: str, value: Any) -> Any:
        """Convert value to enum if column is an enum type.

        Handles string-to-enum conversion automatically by detecting the column's
        enum class from SQLAlchemy mapper metadata.
        """
        if isinstance(value, Enum):
            return value

        enum_class = self._get_column_enum_class(column_name)
        if not enum_class or not isinstance(value, str):
            return value

        return self._string_to_enum(value, enum_class)

    def _get_column_enum_class(self, column_name: str) -> type[Enum] | None:
        """获取列的枚举类型。"""
        try:
            mapper = inspect(self._model_class)
            if not hasattr(mapper, "columns"):
                return None

            columns = getattr(mapper, "columns", None)
            if not columns:
                return None

            column = columns.get(column_name)
            if not column:
                return None

            # Check if column type has enum_class (SQLAlchemy Enum type)
            column_type = column.type
            if hasattr(column_type, "enum_class") and column_type.enum_class:
                return column_type.enum_class
        except (AttributeError, KeyError) as e:
            logger.debug("enum_class_not_found", column_name=column_name, error=str(e))

        return None

    def _string_to_enum(self, value: str, enum_class: type[Enum]) -> Any:
        """将字符串转换为枚举值。"""
        upper_value = value.upper()

        # Try by name first (case-insensitive)
        try:
            return enum_class[upper_value]
        except KeyError:
            pass

        # Then try by value
        for member in enum_class:
            if member.value.upper() == upper_value:
                return member

        # 转换失败，返回原始值
        logger.debug("enum_conversion_failed", value=value, enum_class=enum_class.__name__)
        return value

    def with_soft_delete_filter(self) -> "QueryBuilder[ModelT]":
        """Filter out soft-deleted records (deleted_at IS NULL)."""
        if hasattr(self._model_class, "deleted_at"):
            filter_clause = getattr(self._model_class, "deleted_at").is_(None)
            self._query = self._query.where(filter_clause)
            self._filters.append(filter_clause)
        return self

    def with_filter(self, column_name: str, value: Any) -> "QueryBuilder[ModelT]":
        """Add equality filter if value is not None.

        Automatically converts string values to enum if the column is an enum type.
        """
        if value is not None and hasattr(self._model_class, column_name):
            converted_value = self._convert_enum_value(column_name, value)
            filter_clause = getattr(self._model_class, column_name) == converted_value
            self._query = self._query.where(filter_clause)
            self._filters.append(filter_clause)
        return self

    def with_order_by(self, sort_by: str = "created_at", sort_order: str = "desc") -> "QueryBuilder[ModelT]":
        """Add ordering clause."""
        if hasattr(self._model_class, sort_by):
            column = getattr(self._model_class, sort_by)
            order_func = desc if sort_order.lower() == "desc" else asc
            self._query = self._query.order_by(order_func(column))
        return self

    def with_pagination(self, page: int = 1, page_size: int = 20) -> "QueryBuilder[ModelT]":
        """Add pagination (offset + limit)."""
        offset = (page - 1) * page_size
        self._query = self._query.offset(offset).limit(page_size)
        return self

    def build(self) -> Select[tuple[ModelT]]:
        """Return the built query."""
        return self._query

    async def count(self, session: AsyncSession) -> int:
        """Execute count query using stored filters."""
        pk_column = getattr(self._model_class, "id", None)
        if pk_column is None:
            return 0
        count_query = select(func.count(pk_column))
        for f in self._filters:
            count_query = count_query.where(f)
        result = await session.execute(count_query)
        return result.scalar() or 0

    async def execute(self, session: AsyncSession) -> list[ModelT]:
        """Execute and return results."""
        result = await session.execute(self._query)
        return list(result.scalars().all())

    async def execute_with_count(self, session: AsyncSession) -> tuple[list[ModelT], int]:
        """Execute query and return results with total count."""
        total = await self.count(session)
        items = await self.execute(session)
        return items, total
