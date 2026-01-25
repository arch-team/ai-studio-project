"""Enhanced Base Service with common business logic patterns."""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from src.shared.domain.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
)
from src.shared.domain.interfaces import IEntityExistenceChecker
from src.shared.utils import EnumMapper

T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type


class EnhancedBaseService(Generic[T, ID]):
    """Enhanced base service with common business patterns.

    Provides:
    - CRUD operations with validation
    - State transition management
    - Entity existence validation
    - Enum conversion utilities
    - Pagination support

    Subclasses benefit from:
    - Reduced boilerplate for common operations
    - Consistent error handling
    - Reusable validation patterns
    """

    _repository: object
    _entity_type: str
    _not_found_error_factory: Callable[[str], Exception] | None = None

    def __init__(self, repository: object, entity_type: str):
        """Initialize enhanced base service.

        Args:
            repository: Repository instance with standard methods
            entity_type: Entity type name for error messages
        """
        self._repository = repository
        self._entity_type = entity_type

    # ========== Error Creation ==========

    def _create_not_found_error(self, entity_id: str) -> Exception:
        """Create not-found error.

        Override _not_found_error_factory to customize.
        """
        if self._not_found_error_factory is not None:
            return self._not_found_error_factory(entity_id)
        return EntityNotFoundError(self._entity_type, entity_id)

    def _create_duplicate_error(self, field: str, value: str) -> Exception:
        """Create duplicate entity error."""
        return DuplicateEntityError(self._entity_type, f"{field}={value}")

    def _create_invalid_transition_error(self, current_state: str, target_state: str) -> Exception:
        """Create invalid state transition error."""
        return InvalidStateTransitionError(self._entity_type, current_state, target_state)

    # ========== Entity Retrieval ==========

    async def _get_or_raise(self, entity_id: ID) -> T:
        """Get entity by ID or raise not-found error.

        Args:
            entity_id: Entity ID

        Returns:
            Entity

        Raises:
            EntityNotFoundError: If entity not found
        """
        entity = await self._repository.get_by_id(entity_id)  # type: ignore
        if entity is None:
            raise self._create_not_found_error(str(entity_id))
        return entity  # type: ignore

    async def _get_by_field_or_none(self, field_name: str, field_value: Any) -> T | None:
        """Get entity by arbitrary field.

        Args:
            field_name: Field name to search by
            field_value: Field value to match

        Returns:
            Entity if found, None otherwise
        """
        method_name = f"get_by_{field_name}"
        if hasattr(self._repository, method_name):
            method = getattr(self._repository, method_name)
            return await method(field_value)  # type: ignore
        return None

    # ========== Validation Utilities ==========

    async def _validate_unique_field(self, field_name: str, field_value: Any) -> None:
        """Validate that a field value is unique.

        Args:
            field_name: Field name to check
            field_value: Field value to validate

        Raises:
            DuplicateEntityError: If value already exists
        """
        method_name = f"exists_by_{field_name}"
        if hasattr(self._repository, method_name):
            exists_method = getattr(self._repository, method_name)
            if await exists_method(field_value):
                raise self._create_duplicate_error(field_name, str(field_value))
        # Alternative: Try exists_by if available
        elif hasattr(self._repository, "exists_by"):
            if await self._repository.exists_by(field_name, field_value):
                raise self._create_duplicate_error(field_name, str(field_value))

    async def _validate_entity_exists(
        self,
        checker: IEntityExistenceChecker | None,
        entity_type: str,
        entity_id: ID,
    ) -> None:
        """Validate that a related entity exists.

        Args:
            checker: Entity existence checker
            entity_type: Type of entity to check
            entity_id: ID of entity to check

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        if checker and not await checker.exists(entity_id):  # type: ignore
            raise EntityNotFoundError(entity_type, str(entity_id))

    async def _validate_entities_exist(
        self,
        validations: list[tuple[IEntityExistenceChecker | None, str, ID]],
    ) -> None:
        """Validate multiple related entities exist.

        Args:
            validations: List of (checker, entity_type, entity_id) tuples

        Raises:
            EntityNotFoundError: If any entity doesn't exist
        """
        for checker, entity_type, entity_id in validations:
            await self._validate_entity_exists(checker, entity_type, entity_id)

    # ========== State Management ==========

    def _validate_state_transition(
        self,
        entity: Any,
        target_state: Any,
        allowed_from_states: list[Any] | None = None,
    ) -> None:
        """Validate that a state transition is allowed.

        Args:
            entity: Entity with current state
            target_state: Target state to transition to
            allowed_from_states: List of states that allow this transition

        Raises:
            InvalidStateTransitionError: If transition not allowed
        """
        current_state = getattr(entity, "status", None) or getattr(entity, "state", None)

        if current_state is None:
            return

        # Check if entity has can_transition_to method
        if hasattr(entity, "can_transition_to"):
            if not entity.can_transition_to(target_state):
                raise self._create_invalid_transition_error(str(current_state), str(target_state))
        # Otherwise check allowed_from_states
        elif allowed_from_states and current_state not in allowed_from_states:
            raise self._create_invalid_transition_error(str(current_state), str(target_state))

    # ========== CRUD Operations ==========

    async def get_by_id(self, entity_id: ID) -> T:
        """Get entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity

        Raises:
            EntityNotFoundError: If entity not found
        """
        return await self._get_or_raise(entity_id)

    async def list_entities(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[T], int]:
        """List entities with filters and pagination.

        Args:
            filters: Filter criteria
            page: Page number (1-based)
            page_size: Items per page
            sort_by: Sort column
            sort_order: Sort direction

        Returns:
            Tuple of (entities, total_count)
        """
        # Try to use repository's list method if available
        if hasattr(self._repository, "list_with_filters"):
            return await self._repository.list_with_filters(  # type: ignore
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        # Fallback to a generic list method
        elif hasattr(self._repository, "list"):
            return await self._repository.list(  # type: ignore
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        else:
            # Return empty list if no list method available
            return [], 0

    async def create_entity(
        self,
        data: dict[str, Any],
        unique_fields: list[str] | None = None,
    ) -> T:
        """Create a new entity with validation.

        Args:
            data: Entity data
            unique_fields: Fields that must be unique

        Returns:
            Created entity

        Raises:
            DuplicateEntityError: If unique constraint violated
        """
        # Validate unique fields
        if unique_fields:
            for field in unique_fields:
                if field in data:
                    await self._validate_unique_field(field, data[field])

        # Create entity (assumes repository has create method)
        return await self._repository.create(data)  # type: ignore

    async def update_entity(
        self,
        entity_id: ID,
        data: dict[str, Any],
    ) -> T:
        """Update an existing entity.

        Args:
            entity_id: Entity ID
            data: Update data

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If entity not found
        """
        entity = await self._get_or_raise(entity_id)

        # Update entity attributes
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # Save changes
        return await self._repository.update(entity)  # type: ignore

    async def delete_entity(
        self,
        entity_id: ID,
        soft_delete: bool = True,
    ) -> None:
        """Delete an entity.

        Args:
            entity_id: Entity ID
            soft_delete: Use soft delete if available

        Raises:
            EntityNotFoundError: If entity not found
        """
        await self._get_or_raise(entity_id)  # Verify exists

        if soft_delete and hasattr(self._repository, "soft_delete"):
            await self._repository.soft_delete(entity_id)
        else:
            await self._repository.delete(entity_id)

    # ========== Batch Operations ==========

    async def create_many(
        self,
        items: list[dict[str, Any]],
        unique_fields: list[str] | None = None,
    ) -> list[T]:
        """Create multiple entities.

        Args:
            items: List of entity data
            unique_fields: Fields that must be unique

        Returns:
            List of created entities

        Raises:
            DuplicateEntityError: If unique constraint violated
        """
        # Validate unique fields for all items
        if unique_fields:
            for item in items:
                for field in unique_fields:
                    if field in item:
                        await self._validate_unique_field(field, item[field])

        # Create all entities
        if hasattr(self._repository, "create_many"):
            return await self._repository.create_many(items)  # type: ignore
        else:
            # Fallback to individual creates
            results = []
            for item in items:
                result = await self._repository.create(item)  # type: ignore
                results.append(result)
            return results

    async def get_by_ids(self, entity_ids: list[ID]) -> list[T]:
        """Get multiple entities by their IDs.

        Args:
            entity_ids: List of entity IDs

        Returns:
            List of entities (may be shorter if some not found)
        """
        if hasattr(self._repository, "get_by_ids"):
            return await self._repository.get_by_ids(entity_ids)  # type: ignore
        else:
            # Fallback to individual gets
            results = []
            for entity_id in entity_ids:
                entity = await self._repository.get_by_id(entity_id)  # type: ignore
                if entity:
                    results.append(entity)
            return results

    # ========== Utility Methods ==========

    def convert_enum(
        self,
        value: str | None,
        enum_class: type,
        default: Any = None,
    ) -> Any:
        """Convert string to enum value.

        Args:
            value: String value to convert
            enum_class: Target enum class
            default: Default value if conversion fails

        Returns:
            Enum value or default
        """
        return EnumMapper.from_string(value, enum_class, default)
