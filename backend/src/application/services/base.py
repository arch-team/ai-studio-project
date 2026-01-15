"""Base Service - Common service functionality and patterns."""

from typing import Any, Generic, Protocol, TypeVar

from src.domain.exceptions import EntityNotFoundError

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class HasGetById(Protocol[T_co]):
    """Protocol for repositories with get_by_id method."""

    async def get_by_id(self, entity_id: int) -> T_co | None: ...


class EntityServiceMixin(Generic[T]):
    """Mixin providing common entity retrieval patterns.

    Subclasses must set:
        _repository: Repository instance with get_by_id method
        _entity_name: Human-readable entity name for error messages

    Example:
        class TrainingJobService(EntityServiceMixin[TrainingJob]):
            _entity_name = "TrainingJob"

            async def get_job(self, job_id: int) -> TrainingJob:
                return await self._get_or_raise(job_id)
    """

    _repository: HasGetById[Any]
    _entity_name: str = "Entity"

    async def _get_or_raise(self, entity_id: int) -> T:
        """Get entity by ID or raise EntityNotFoundError.

        Args:
            entity_id: Entity ID to retrieve

        Returns:
            Entity instance

        Raises:
            EntityNotFoundError: If entity not found
        """
        entity = await self._repository.get_by_id(entity_id)
        if entity is None:
            raise EntityNotFoundError(self._entity_name, str(entity_id))
        return entity  # type: ignore[no-any-return]
