"""Query builder utility for common repository operations."""

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class QueryBuilder(Generic[ModelT]):
    """Builder for common query operations: pagination, sorting, soft delete filter."""

    def __init__(self, query: Select[tuple[ModelT]], model_class: type[ModelT]):
        self._query: Select[tuple[ModelT]] = query
        self._model_class = model_class

    def with_soft_delete_filter(self) -> "QueryBuilder[ModelT]":
        """Filter out soft-deleted records (deleted_at IS NULL)."""
        if hasattr(self._model_class, "deleted_at"):
            self._query = self._query.where(
                getattr(self._model_class, "deleted_at").is_(None)
            )
        return self

    def with_filter(self, column_name: str, value: Any) -> "QueryBuilder[ModelT]":
        """Add equality filter if value is not None."""
        if value is not None and hasattr(self._model_class, column_name):
            self._query = self._query.where(
                getattr(self._model_class, column_name) == value
            )
        return self

    def with_order_by(
        self, sort_by: str = "created_at", sort_order: str = "desc"
    ) -> "QueryBuilder[ModelT]":
        """Add ordering clause."""
        if hasattr(self._model_class, sort_by):
            column = getattr(self._model_class, sort_by)
            order_func = desc if sort_order.lower() == "desc" else asc
            self._query = self._query.order_by(order_func(column))
        return self

    def with_pagination(
        self, page: int = 1, page_size: int = 20
    ) -> "QueryBuilder[ModelT]":
        """Add pagination (offset + limit)."""
        offset = (page - 1) * page_size
        self._query = self._query.offset(offset).limit(page_size)
        return self

    def build(self) -> Select[tuple[ModelT]]:
        """Return the built query."""
        return self._query

    async def count(self, session: AsyncSession) -> int:
        """Execute count query (without pagination)."""
        count_query = self._query.with_only_columns(func.count()).order_by(None)
        result = await session.execute(count_query)
        return result.scalar() or 0

    async def execute(self, session: AsyncSession) -> list[ModelT]:
        """Execute and return results."""
        result = await session.execute(self._query)
        return list(result.scalars().all())
