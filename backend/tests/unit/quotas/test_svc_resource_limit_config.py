"""ResourceLimitConfig Service Unit Tests - TDD Red-Green-Refactor.

Tests for T012c-f (resource limit config CRUD operations).
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.modules.quotas.domain.entities.resource_limit_config import (
    LimitRole,
    PriorityDefault,
    ResourceLimitConfig,
)
from src.modules.quotas.domain.exceptions import DuplicateConfigError, QuotaNotFoundError

# === Fixtures ===


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock resource limit config repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_role_and_project = AsyncMock(return_value=None)
    repo.list_configs = AsyncMock(return_value=([], 0))
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock(return_value=True)
    repo.exists_by_role_and_project = AsyncMock(return_value=False)
    return repo


@pytest.fixture
def sample_config() -> ResourceLimitConfig:
    """Sample resource limit config entity."""
    return ResourceLimitConfig(
        id=1,
        config_name="engineer-global-limits",
        role=LimitRole.ENGINEER,
        project_id=None,
        max_gpu_per_job=8,
        max_cpu_per_job=64,
        max_memory_gb_per_job=512,
        max_storage_gb_per_job=1000,
        max_nodes_per_job=4,
        priority_default=PriorityDefault.MEDIUM,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def project_config(sample_config: ResourceLimitConfig) -> ResourceLimitConfig:
    """Project-specific config."""
    config = ResourceLimitConfig(
        id=2,
        config_name="engineer-project-1-limits",
        role=LimitRole.ENGINEER,
        project_id=100,
        max_gpu_per_job=16,
        max_cpu_per_job=128,
        max_memory_gb_per_job=1024,
        max_storage_gb_per_job=2000,
        max_nodes_per_job=8,
        priority_default=PriorityDefault.HIGH,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return config


@pytest.fixture
def create_config_data() -> dict[str, Any]:
    """Data for creating a config."""
    return {
        "config_name": "new-engineer-config",
        "role": "engineer",
        "project_id": None,
        "max_gpu_per_job": 8,
        "max_cpu_per_job": 64,
        "max_memory_gb_per_job": 512,
        "max_storage_gb_per_job": 1000,
        "max_nodes_per_job": 4,
        "priority_default": "medium",
    }


# === Service Factory ===


def get_service(mock_repository: AsyncMock):
    """Create ResourceLimitConfigService with mocked dependencies."""
    from src.modules.quotas.application.services.resource_limit_config_service import (
        ResourceLimitConfigService,
    )

    return ResourceLimitConfigService(repository=mock_repository)


# === Test Classes ===


class TestCreateConfig:
    """Tests for create_config method (T012d)."""

    @pytest.mark.asyncio
    async def test_create_config_success(
        self,
        mock_repository: AsyncMock,
        create_config_data: dict[str, Any],
        sample_config: ResourceLimitConfig,
    ):
        """Test successful config creation."""
        # Arrange
        mock_repository.exists_by_role_and_project.return_value = False
        mock_repository.create.return_value = sample_config
        service = get_service(mock_repository)

        # Act
        result = await service.create_config(create_config_data)

        # Assert
        assert result is not None
        assert result.config_name == sample_config.config_name
        mock_repository.exists_by_role_and_project.assert_called_once()
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_config_duplicate_raises_error(
        self,
        mock_repository: AsyncMock,
        create_config_data: dict[str, Any],
    ):
        """Test create fails when (role, project_id) combination exists."""
        # Arrange
        mock_repository.exists_by_role_and_project.return_value = True
        service = get_service(mock_repository)

        # Act & Assert
        with pytest.raises(DuplicateConfigError) as exc_info:
            await service.create_config(create_config_data)

        assert "already exists" in str(exc_info.value)
        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_config_with_project_id(
        self,
        mock_repository: AsyncMock,
        project_config: ResourceLimitConfig,
    ):
        """Test creating project-specific config."""
        # Arrange
        mock_repository.exists_by_role_and_project.return_value = False
        mock_repository.create.return_value = project_config
        service = get_service(mock_repository)

        data = {
            "config_name": "engineer-project-1-limits",
            "role": "engineer",
            "project_id": 100,
            "max_gpu_per_job": 16,
        }

        # Act
        result = await service.create_config(data)

        # Assert
        assert result.project_id == 100
        mock_repository.exists_by_role_and_project.assert_called_once_with(LimitRole.ENGINEER, 100)

    @pytest.mark.asyncio
    async def test_create_config_uses_defaults(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test create uses default values for optional fields."""
        # Arrange
        mock_repository.exists_by_role_and_project.return_value = False
        mock_repository.create.return_value = sample_config
        service = get_service(mock_repository)

        minimal_data = {
            "config_name": "minimal-config",
            "role": "engineer",
        }

        # Act
        await service.create_config(minimal_data)

        # Assert
        mock_repository.create.assert_called_once()
        created_config = mock_repository.create.call_args[0][0]
        assert created_config.max_gpu_per_job == 8  # default
        assert created_config.priority_default == PriorityDefault.MEDIUM  # default


class TestGetConfig:
    """Tests for get_config method."""

    @pytest.mark.asyncio
    async def test_get_config_success(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test get config by ID."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_config
        service = get_service(mock_repository)

        # Act
        result = await service.get_config(config_id=1)

        # Assert
        assert result is not None
        assert result.id == sample_config.id
        mock_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_config_not_found(
        self,
        mock_repository: AsyncMock,
    ):
        """Test get config raises error when not found."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        service = get_service(mock_repository)

        # Act & Assert
        with pytest.raises(QuotaNotFoundError) as exc_info:
            await service.get_config(config_id=999)

        assert "not found" in str(exc_info.value).lower()


class TestGetConfigForRole:
    """Tests for get_config_for_role method."""

    @pytest.mark.asyncio
    async def test_get_config_for_role_returns_project_specific(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
        project_config: ResourceLimitConfig,
    ):
        """Test returns project-specific config when available."""
        # Arrange
        mock_repository.get_by_role_and_project.return_value = project_config
        service = get_service(mock_repository)

        # Act
        result = await service.get_config_for_role(LimitRole.ENGINEER, project_id=100)

        # Assert
        assert result is not None
        assert result.project_id == 100
        mock_repository.get_by_role_and_project.assert_called_once_with(LimitRole.ENGINEER, 100)

    @pytest.mark.asyncio
    async def test_get_config_for_role_falls_back_to_global(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test falls back to global config when project-specific not found."""
        # Arrange
        # First call (project-specific) returns None, second call (global) returns config
        mock_repository.get_by_role_and_project.side_effect = [None, sample_config]
        service = get_service(mock_repository)

        # Act
        result = await service.get_config_for_role(LimitRole.ENGINEER, project_id=100)

        # Assert
        assert result is not None
        assert result.project_id is None  # global config
        assert mock_repository.get_by_role_and_project.call_count == 2

    @pytest.mark.asyncio
    async def test_get_config_for_role_returns_none_when_no_config(
        self,
        mock_repository: AsyncMock,
    ):
        """Test returns None when no config found."""
        # Arrange
        mock_repository.get_by_role_and_project.return_value = None
        service = get_service(mock_repository)

        # Act
        result = await service.get_config_for_role(LimitRole.VIEWER)

        # Assert
        assert result is None


class TestListConfigs:
    """Tests for list_configs method (T012c)."""

    @pytest.mark.asyncio
    async def test_list_configs_with_pagination(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test list configs with pagination."""
        # Arrange
        mock_repository.list_configs.return_value = ([sample_config], 1)
        service = get_service(mock_repository)

        # Act
        configs, total = await service.list_configs(page=1, page_size=20)

        # Assert
        assert len(configs) == 1
        assert total == 1
        mock_repository.list_configs.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_configs_filter_by_role(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test list configs filtered by role."""
        # Arrange
        mock_repository.list_configs.return_value = ([sample_config], 1)
        service = get_service(mock_repository)

        # Act
        configs, total = await service.list_configs(role=LimitRole.ENGINEER)

        # Assert
        call_kwargs = mock_repository.list_configs.call_args.kwargs
        assert call_kwargs.get("role") == LimitRole.ENGINEER

    @pytest.mark.asyncio
    async def test_list_configs_filter_by_project(
        self,
        mock_repository: AsyncMock,
        project_config: ResourceLimitConfig,
    ):
        """Test list configs filtered by project_id."""
        # Arrange
        mock_repository.list_configs.return_value = ([project_config], 1)
        service = get_service(mock_repository)

        # Act
        configs, total = await service.list_configs(project_id=100)

        # Assert
        call_kwargs = mock_repository.list_configs.call_args.kwargs
        assert call_kwargs.get("project_id") == 100


class TestUpdateConfig:
    """Tests for update_config method (T012e)."""

    @pytest.mark.asyncio
    async def test_update_config_success(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test successful config update."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_config
        updated_config = ResourceLimitConfig(
            id=sample_config.id,
            config_name="updated-name",
            role=sample_config.role,
            project_id=sample_config.project_id,
            max_gpu_per_job=16,
            max_cpu_per_job=sample_config.max_cpu_per_job,
            max_memory_gb_per_job=sample_config.max_memory_gb_per_job,
            max_storage_gb_per_job=sample_config.max_storage_gb_per_job,
            max_nodes_per_job=sample_config.max_nodes_per_job,
            priority_default=sample_config.priority_default,
            created_at=sample_config.created_at,
            updated_at=datetime.utcnow(),
        )
        mock_repository.update.return_value = updated_config
        service = get_service(mock_repository)

        # Act
        result = await service.update_config(
            config_id=1,
            data={"config_name": "updated-name", "max_gpu_per_job": 16},
        )

        # Assert
        assert result.config_name == "updated-name"
        assert result.max_gpu_per_job == 16
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_config_not_found(
        self,
        mock_repository: AsyncMock,
    ):
        """Test update raises error when config not found."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        service = get_service(mock_repository)

        # Act & Assert
        with pytest.raises(QuotaNotFoundError):
            await service.update_config(config_id=999, data={"config_name": "new"})

    @pytest.mark.asyncio
    async def test_update_config_duplicate_role_project(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
        project_config: ResourceLimitConfig,
    ):
        """Test update fails when new (role, project_id) already exists."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_config
        mock_repository.get_by_role_and_project.return_value = project_config
        service = get_service(mock_repository)

        # Act & Assert
        with pytest.raises(DuplicateConfigError):
            await service.update_config(
                config_id=1,
                data={"role": "engineer", "project_id": 100},
            )

        mock_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_config_partial_update(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test partial update only changes specified fields."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_config
        mock_repository.update.return_value = sample_config
        service = get_service(mock_repository)

        # Act
        await service.update_config(
            config_id=1,
            data={"max_gpu_per_job": 32},
        )

        # Assert
        mock_repository.update.assert_called_once()
        updated = mock_repository.update.call_args[0][0]
        assert updated.max_gpu_per_job == 32
        # Other fields unchanged
        assert updated.max_cpu_per_job == sample_config.max_cpu_per_job


class TestDeleteConfig:
    """Tests for delete_config method (T012f)."""

    @pytest.mark.asyncio
    async def test_delete_config_success(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test successful config deletion."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_config
        mock_repository.soft_delete.return_value = True
        service = get_service(mock_repository)

        # Act
        await service.delete_config(config_id=1)

        # Assert
        mock_repository.soft_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_config_not_found(
        self,
        mock_repository: AsyncMock,
    ):
        """Test delete raises error when config not found."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        service = get_service(mock_repository)

        # Act & Assert
        with pytest.raises(QuotaNotFoundError):
            await service.delete_config(config_id=999)


class TestValidateJobLimits:
    """Tests for validate_job_limits method."""

    @pytest.mark.asyncio
    async def test_validate_limits_within_bounds(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test validation passes when within limits."""
        # Arrange
        mock_repository.get_by_role_and_project.return_value = sample_config
        service = get_service(mock_repository)

        # Act
        is_valid, error = await service.validate_job_limits(
            role=LimitRole.ENGINEER,
            project_id=None,
            requested_gpu=4,
            requested_cpu=32,
            requested_memory_gb=256,
            requested_storage_gb=500,
            requested_nodes=2,
        )

        # Assert
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_limits_exceeds_gpu(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test validation fails when GPU limit exceeded."""
        # Arrange
        mock_repository.get_by_role_and_project.return_value = sample_config
        service = get_service(mock_repository)

        # Act
        is_valid, error = await service.validate_job_limits(
            role=LimitRole.ENGINEER,
            project_id=None,
            requested_gpu=16,  # Exceeds limit of 8
            requested_cpu=32,
            requested_memory_gb=256,
            requested_storage_gb=500,
            requested_nodes=2,
        )

        # Assert
        assert is_valid is False
        assert "GPU" in error
        assert "exceeds limit" in error

    @pytest.mark.asyncio
    async def test_validate_limits_multiple_exceeded(
        self,
        mock_repository: AsyncMock,
        sample_config: ResourceLimitConfig,
    ):
        """Test validation reports multiple limit violations."""
        # Arrange
        mock_repository.get_by_role_and_project.return_value = sample_config
        service = get_service(mock_repository)

        # Act
        is_valid, error = await service.validate_job_limits(
            role=LimitRole.ENGINEER,
            project_id=None,
            requested_gpu=16,  # Exceeds
            requested_cpu=128,  # Exceeds
            requested_memory_gb=256,
            requested_storage_gb=500,
            requested_nodes=2,
        )

        # Assert
        assert is_valid is False
        assert "GPU" in error
        assert "CPU" in error

    @pytest.mark.asyncio
    async def test_validate_limits_no_config_allows_all(
        self,
        mock_repository: AsyncMock,
    ):
        """Test validation passes when no config exists."""
        # Arrange
        mock_repository.get_by_role_and_project.return_value = None
        service = get_service(mock_repository)

        # Act
        is_valid, error = await service.validate_job_limits(
            role=LimitRole.VIEWER,
            project_id=None,
            requested_gpu=1000,  # Any value
            requested_cpu=1000,
            requested_memory_gb=10000,
            requested_storage_gb=100000,
            requested_nodes=100,
        )

        # Assert
        assert is_valid is True
        assert error is None
