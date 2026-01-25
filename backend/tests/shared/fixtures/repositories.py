"""Shared repository mock fixtures for testing."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# ========== Generic Repository Mock ==========


def create_mock_repository(
    entity_type: str = "Entity",
    default_return: Any = None,
) -> AsyncMock:
    """Create a generic mock repository with common methods.

    Args:
        entity_type: Type of entity for error messages
        default_return: Default return value for get methods

    Returns:
        Mock repository with standard methods
    """
    repo = AsyncMock()

    # Standard CRUD methods
    repo.get_by_id = AsyncMock(return_value=default_return)
    repo.create = AsyncMock(side_effect=lambda x: x)  # Return input entity
    repo.update = AsyncMock(side_effect=lambda x: x)  # Return input entity
    repo.delete = AsyncMock(return_value=True)
    repo.soft_delete = AsyncMock(return_value=True)

    # Query methods
    repo.exists = AsyncMock(return_value=False)
    repo.exists_by = AsyncMock(return_value=False)
    repo.list = AsyncMock(return_value=([], 0))
    repo.list_with_filters = AsyncMock(return_value=([], 0))

    # Batch operations
    repo.create_many = AsyncMock(side_effect=lambda x: x)  # Return input list
    repo.get_by_ids = AsyncMock(return_value=[])

    return repo


# ========== Specific Repository Mocks ==========


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Mock IUserRepository for testing auth services."""
    repo = create_mock_repository("User")

    # User-specific methods
    repo.get_by_username = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.exists_by_username = AsyncMock(return_value=False)
    repo.exists_by_email = AsyncMock(return_value=False)
    repo.get_active_users = AsyncMock(return_value=[])

    return repo


@pytest.fixture
def mock_training_job_repository() -> AsyncMock:
    """Mock ITrainingJobRepository for testing training services."""
    repo = create_mock_repository("TrainingJob")

    # TrainingJob-specific methods
    repo.get_by_name = AsyncMock(return_value=None)
    repo.exists_by_name = AsyncMock(return_value=False)
    repo.list_jobs = AsyncMock(return_value=([], 0))
    repo.get_by_owner = AsyncMock(return_value=[])
    repo.get_by_status = AsyncMock(return_value=[])
    repo.get_running_jobs = AsyncMock(return_value=[])

    return repo


@pytest.fixture
def mock_checkpoint_repository() -> AsyncMock:
    """Mock ICheckpointRepository for testing checkpoint services."""
    repo = create_mock_repository("Checkpoint")

    # Checkpoint-specific methods
    repo.get_by_job_id = AsyncMock(return_value=[])
    repo.get_latest_by_job_id = AsyncMock(return_value=None)
    repo.get_best_by_job_id = AsyncMock(return_value=None)
    repo.list_checkpoints = AsyncMock(return_value=([], 0))

    return repo


@pytest.fixture
def mock_model_repository() -> AsyncMock:
    """Mock IModelRepository for testing model services."""
    repo = create_mock_repository("Model")

    # Model-specific methods
    repo.get_by_name_and_version = AsyncMock(return_value=None)
    repo.get_latest_version = AsyncMock(return_value=None)
    repo.list_versions = AsyncMock(return_value=[])
    repo.list_models = AsyncMock(return_value=([], 0))
    repo.get_by_training_job = AsyncMock(return_value=[])

    return repo


@pytest.fixture
def mock_resource_quota_repository() -> AsyncMock:
    """Mock IResourceQuotaRepository for testing quota services."""
    repo = create_mock_repository("ResourceQuota")

    # ResourceQuota-specific methods
    repo.get_by_user_id = AsyncMock(return_value=None)
    repo.get_by_project_id = AsyncMock(return_value=None)
    repo.list_quotas = AsyncMock(return_value=([], 0))

    return repo


@pytest.fixture
def mock_space_repository() -> AsyncMock:
    """Mock ISpaceRepository for testing space services."""
    repo = create_mock_repository("Space")

    # Space-specific methods
    repo.get_by_name = AsyncMock(return_value=None)
    repo.get_by_owner = AsyncMock(return_value=[])
    repo.exists_by_name = AsyncMock(return_value=False)
    repo.list_spaces = AsyncMock(return_value=([], 0))

    return repo


# ========== Repository Factory ==========


@pytest.fixture
def mock_repository_factory() -> MagicMock:
    """Factory for creating mock repositories on demand."""

    def factory(
        entity_type: str = "Entity",
        methods: dict[str, Any] | None = None,
    ) -> AsyncMock:
        """Create a mock repository with custom methods.

        Args:
            entity_type: Type of entity
            methods: Dict of method_name -> return_value

        Returns:
            Configured mock repository
        """
        repo = create_mock_repository(entity_type)

        # Add custom methods
        if methods:
            for method_name, return_value in methods.items():
                setattr(repo, method_name, AsyncMock(return_value=return_value))

        return repo

    return MagicMock(side_effect=factory)


# ========== Repository with Behavior ==========


@pytest.fixture
def mock_repository_with_data() -> AsyncMock:
    """Mock repository that simulates real data storage."""

    class MockRepositoryWithData:
        """Mock repository with in-memory storage."""

        def __init__(self):
            self._data: dict[int, Any] = {}
            self._next_id = 1

        async def get_by_id(self, id: int) -> Any:
            """Get entity by ID."""
            return self._data.get(id)

        async def create(self, entity: Any) -> Any:
            """Create entity with auto-generated ID."""
            if not hasattr(entity, "id") or entity.id is None:
                entity.id = self._next_id
                self._next_id += 1
            self._data[entity.id] = entity
            return entity

        async def update(self, entity: Any) -> Any:
            """Update existing entity."""
            if hasattr(entity, "id") and entity.id in self._data:
                self._data[entity.id] = entity
            return entity

        async def delete(self, id: int) -> bool:
            """Delete entity by ID."""
            if id in self._data:
                del self._data[id]
                return True
            return False

        async def exists(self, id: int) -> bool:
            """Check if entity exists."""
            return id in self._data

        async def list(
            self,
            page: int = 1,
            page_size: int = 20,
            **kwargs,
        ) -> tuple[list, int]:
            """List entities with pagination."""
            items = list(self._data.values())
            total = len(items)

            # Apply pagination
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = items[start:end]

            return paginated_items, total

    return AsyncMock(wraps=MockRepositoryWithData())
