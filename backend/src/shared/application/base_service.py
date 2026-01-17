"""Base application service with common operations."""

from collections.abc import Callable
from typing import Generic, TypeVar

from src.shared.domain.exceptions import EntityNotFoundError

T = TypeVar("T")
ID = TypeVar("ID")


class BaseService(Generic[T, ID]):
    """Base service with common entity operations.

    Type Parameters:
        T: Entity type
        ID: Entity ID type (int, str, UUID, etc.)

    Subclasses can customize the not-found exception by setting _not_found_error_factory.
    """

    _repository: object
    _entity_type: str
    _not_found_error_factory: Callable[[str], Exception] | None = None

    def __init__(self, repository: object, entity_type: str):
        """Initialize base service.

        Args:
            repository: Repository instance with get_by_id method
            entity_type: Entity type name for error messages
        """
        self._repository = repository
        self._entity_type = entity_type

    def _create_not_found_error(self, entity_id: str) -> Exception:
        """Create not-found error. Override or set _not_found_error_factory to customize."""
        if self._not_found_error_factory is not None:
            return self._not_found_error_factory(entity_id)
        return EntityNotFoundError(self._entity_type, entity_id)

    async def _get_or_raise(self, entity_id: ID) -> T:
        """Get entity by ID or raise not-found error."""
        entity = await self._repository.get_by_id(entity_id)  # type: ignore
        if entity is None:
            raise self._create_not_found_error(str(entity_id))
        return entity  # type: ignore
