"""Enhanced Base Repository Implementation with QueryBuilder integration."""

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


class EnhancedBaseRepository(ABC, Generic[EntityT, ModelT, IdT]):
    """Enhanced base repository with QueryBuilder integration.

    Provides:
    - Common CRUD operations (get_by_id, create, update, delete)
    - Pagination support with QueryBuilder
    - Soft delete support
    - Existence checking utilities

    Subclasses only need to implement:
    - _to_entity(): ORM model to domain entity conversion
    - _to_model(): Domain entity to ORM model conversion
    - _update_model(): Update ORM model fields from entity
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelT]):
        """Initialize repository.

        Args:
            session: SQLAlchemy async session
            model_class: ORM model class
        """
        self._session = session
        self._model_class = model_class

    @abstractmethod
    def _to_entity(self, model: ModelT) -> EntityT:
        """Convert ORM model to domain entity.

        Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def _to_model(self, entity: EntityT) -> ModelT:
        """Convert domain entity to ORM model.

        Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def _update_model(self, model: ModelT, entity: EntityT) -> None:
        """Update ORM model fields from entity.

        Must be implemented by subclasses.
        Only updates mutable fields, not ID or timestamps.
        """
        ...

    def _get_id_column(self) -> Any:
        """Get the primary key column.

        Override if your model's primary key is not 'id'.
        """
        return getattr(self._model_class, "id")

    def _get_entity_type_name(self) -> str:
        """Get entity type name for error messages.

        Override to customize error messages.
        """
        return self._model_class.__name__.replace("Model", "")

    # ========== Basic CRUD Operations ==========

    async def get_by_id(self, id: IdT) -> EntityT | None:
        """Get entity by primary key.

        Args:
            id: Primary key value

        Returns:
            Entity if found, None otherwise
        """
        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column == id))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_id_or_raise(self, id: IdT) -> EntityT:
        """Get entity by primary key or raise exception.

        Args:
            id: Primary key value

        Returns:
            Entity

        Raises:
            EntityNotFoundError: If entity not found
        """
        entity = await self.get_by_id(id)
        if entity is None:
            raise EntityNotFoundError(self._get_entity_type_name(), str(id))
        return entity

    async def create(self, entity: EntityT) -> EntityT:
        """Create a new entity.

        Args:
            entity: Domain entity to create

        Returns:
            Created entity with generated ID
        """
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: EntityT) -> EntityT:
        """Update an existing entity.

        Args:
            entity: Domain entity with updated values

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If entity not found
        """
        id_value = getattr(entity, "id")
        id_column = self._get_id_column()

        result = await self._session.execute(select(self._model_class).where(id_column == id_value))
        model = result.scalar_one_or_none()

        if model is None:
            raise EntityNotFoundError(self._get_entity_type_name(), str(id_value))

        self._update_model(model, entity)

        # Update timestamp if model has updated_at field
        if hasattr(model, "updated_at"):
            model.updated_at = utc_now()

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: IdT) -> bool:
        """Hard delete an entity.

        Args:
            id: Primary key of entity to delete

        Returns:
            True if deleted, False if not found
        """
        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column == id))
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def soft_delete(self, id: IdT) -> bool:
        """Soft delete an entity.

        Only works if model has 'deleted_at' field.

        Args:
            id: Primary key of entity to soft delete

        Returns:
            True if deleted, False if not found or no soft delete support
        """
        if not hasattr(self._model_class, "deleted_at"):
            # Fallback to hard delete if no soft delete column
            return await self.delete(id)

        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column == id))
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.deleted_at = utc_now()

        if hasattr(model, "updated_at"):
            model.updated_at = utc_now()

        await self._session.flush()
        return True

    # ========== Existence Checking ==========

    async def exists(self, id: IdT) -> bool:
        """Check if entity exists by primary key.

        Args:
            id: Primary key value

        Returns:
            True if exists, False otherwise
        """
        id_column = self._get_id_column()
        result = await self._session.execute(select(func.count(id_column)).where(id_column == id))
        count = result.scalar() or 0
        return count > 0

    async def exists_by(self, column_name: str, value: Any) -> bool:
        """Check if entity exists by arbitrary column value.

        Args:
            column_name: Column name to check
            value: Value to check for

        Returns:
            True if exists, False otherwise
        """
        column = getattr(self._model_class, column_name, None)
        if column is None:
            return False

        query = select(func.count(self._get_id_column())).where(column == value)

        # Apply soft delete filter if supported
        if hasattr(self._model_class, "deleted_at"):
            query = query.where(self._model_class.deleted_at.is_(None))

        result = await self._session.execute(query)
        count = result.scalar() or 0
        return count > 0

    # ========== Query Building Helpers ==========

    def _create_query_builder(self) -> QueryBuilder[ModelT]:
        """Create a QueryBuilder instance for this model.

        Returns:
            QueryBuilder configured for the model class
        """
        query = select(self._model_class)
        return QueryBuilder(query, self._model_class)

    async def _list_with_filters(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_soft_deleted: bool = False,
    ) -> tuple[list[EntityT], int]:
        """List entities with filters and pagination.

        Args:
            filters: Dict of column_name -> value filters
            page: Page number (1-based)
            page_size: Items per page
            sort_by: Column name to sort by
            sort_order: "asc" or "desc"
            include_soft_deleted: Whether to include soft-deleted records

        Returns:
            Tuple of (entities, total_count)
        """
        builder = self._create_query_builder()

        # Apply soft delete filter
        if not include_soft_deleted:
            builder = builder.with_soft_delete_filter()

        # Apply custom filters
        if filters:
            for column_name, value in filters.items():
                if value is not None:
                    builder = builder.with_filter(column_name, value)

        # Apply sorting
        builder = builder.with_order_by(sort_by, sort_order)

        # Get total count before pagination
        total = await builder.count(self._session)

        # Apply pagination
        builder = builder.with_pagination(page, page_size)

        # Execute query
        items = await builder.execute(self._session)

        # Convert to entities
        entities = [self._to_entity(item) for item in items]

        return entities, total

    # ========== Batch Operations ==========

    async def create_many(self, entities: list[EntityT]) -> list[EntityT]:
        """Create multiple entities in a batch.

        Args:
            entities: List of domain entities to create

        Returns:
            List of created entities with generated IDs
        """
        models = [self._to_model(entity) for entity in entities]
        self._session.add_all(models)
        await self._session.flush()

        # Refresh all models to get generated IDs
        for model in models:
            await self._session.refresh(model)

        return [self._to_entity(model) for model in models]

    async def get_by_ids(self, ids: list[IdT]) -> list[EntityT]:
        """Get multiple entities by their IDs.

        Args:
            ids: List of primary key values

        Returns:
            List of entities (may be shorter than ids if some not found)
        """
        if not ids:
            return []

        id_column = self._get_id_column()
        result = await self._session.execute(select(self._model_class).where(id_column.in_(ids)))
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]
