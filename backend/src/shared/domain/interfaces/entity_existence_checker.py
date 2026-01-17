"""Entity Existence Checker Interface - Cross-module interface for entity validation.

This interface enables modules to verify entity existence in other modules
without directly depending on their repository implementations.

Usage in models module:
    from src.shared.domain.interfaces import IEntityExistenceChecker

    class ModelService:
        def __init__(self, training_job_checker: IEntityExistenceChecker):
            self._training_job_checker = training_job_checker

        async def create_model(self, data: dict) -> Model:
            if not await self._training_job_checker.exists(data["training_job_id"]):
                raise EntityNotFoundError("TrainingJob", str(data["training_job_id"]))
"""

from abc import ABC, abstractmethod


class IEntityExistenceChecker(ABC):
    """Interface for checking entity existence across modules.

    This interface decouples modules that need to validate foreign key
    references without creating direct dependencies on other modules.
    """

    @abstractmethod
    async def exists(self, entity_id: int) -> bool:
        """Check if an entity with the given ID exists.

        Args:
            entity_id: The ID of the entity to check.

        Returns:
            True if the entity exists, False otherwise.
        """
        pass

    @abstractmethod
    async def get_entity_type(self) -> str:
        """Get the type name of the entity this checker validates.

        Returns:
            Entity type name (e.g., "TrainingJob", "Checkpoint").
        """
        pass
