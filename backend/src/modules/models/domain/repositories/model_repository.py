"""Model Repository Interface - Data access contract for ML models."""

from abc import ABC, abstractmethod

from ..entities import Model
from ..value_objects import ModelFramework, ModelStatus


class IModelRepository(ABC):
    """Abstract repository interface for Model entity."""

    @abstractmethod
    async def get_by_id(self, model_id: int) -> Model | None:
        """Get model by ID."""

    @abstractmethod
    async def get_by_name_and_version(
        self, model_name: str, version: str
    ) -> Model | None:
        """Get model by name and version."""

    @abstractmethod
    async def get_latest_version(self, model_name: str) -> Model | None:
        """Get the latest version of a model by name."""

    @abstractmethod
    async def list_models(
        self,
        owner_id: int | None = None,
        training_job_id: int | None = None,
        status: str | ModelStatus | None = None,
        framework: str | ModelFramework | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Model], int]:
        """List models with pagination and filters.

        Returns:
            tuple of (list of models, total count)
        """

    @abstractmethod
    async def list_versions(self, model_name: str) -> list[Model]:
        """List all versions of a model by name."""

    @abstractmethod
    async def create(self, model: Model) -> Model:
        """Create a new model."""

    @abstractmethod
    async def update(self, model: Model) -> Model:
        """Update an existing model."""

    @abstractmethod
    async def soft_delete(self, model_id: int) -> bool:
        """Soft delete a model.

        Returns:
            True if deleted, False if not found
        """
