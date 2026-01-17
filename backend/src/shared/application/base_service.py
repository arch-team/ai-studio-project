"""Base application service with common operations."""

from typing import Generic, TypeVar

from src.shared.domain.exceptions import EntityNotFoundError

T = TypeVar("T")
ID = TypeVar("ID")


class BaseService(Generic[T, ID]):
    """Base service with common entity operations.

    Type Parameters:
        T: Entity type
        ID: Entity ID type (int, str, UUID, etc.)
    """

    _repository: object
    _entity_type: str

    def __init__(self, repository: object, entity_type: str):
        """Initialize base service.

        Args:
            repository: Repository instance with get_by_id method
            entity_type: Entity type name for error messages
        """
        self._repository = repository
        self._entity_type = entity_type

    async def _get_or_raise(self, entity_id: ID) -> T:
        """Get entity by ID or raise EntityNotFoundError."""
        entity = await self._repository.get_by_id(entity_id)  # type: ignore
        if entity is None:
            raise EntityNotFoundError(self._entity_type, str(entity_id))
        return entity  # type: ignore
