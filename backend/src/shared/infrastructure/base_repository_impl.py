"""Base Repository Implementation - Common CRUD patterns for SQLAlchemy repositories."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

EntityT = TypeVar("EntityT")
ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT", int, str)


class BaseRepositoryImpl(ABC, Generic[EntityT, ModelT, IdT]):
    """Base repository with common CRUD patterns.

    Provides reusable implementations for get_by_id, create, and exists operations.
    Subclasses must implement _to_entity and _to_model for ORM-domain mapping.

    Type Parameters:
        EntityT: Domain entity type
        ModelT: SQLAlchemy ORM model type
        IdT: Primary key type (int or str)
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelT]):
        self._session = session
        self._model_class = model_class

    @abstractmethod
    def _to_entity(self, model: ModelT) -> EntityT:
        """Convert ORM model to domain entity."""
        ...

    @abstractmethod
    def _to_model(self, entity: EntityT) -> ModelT:
        """Convert domain entity to ORM model."""
        ...

    def _get_id_column(self) -> Any:
        """Get the primary key column. Override if not 'id'."""
        return getattr(self._model_class, "id")

    async def get_by_id(self, id: IdT) -> EntityT | None:
        """Get entity by primary key."""
        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column == id))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def create(self, entity: EntityT) -> EntityT:
        """Create a new entity."""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def exists(self, id: IdT) -> bool:
        """Check if entity exists by primary key."""
        id_column = self._get_id_column()
        result = await self._session.execute(select(func.count(id_column)).where(id_column == id))
        count = result.scalar() or 0
        return count > 0

    async def exists_by(self, column_name: str, value: Any) -> bool:
        """Check if entity exists by arbitrary column value."""
        column = getattr(self._model_class, column_name, None)
        if column is None:
            return False
        result = await self._session.execute(select(func.count(self._get_id_column())).where(column == value))
        count = result.scalar() or 0
        return count > 0
