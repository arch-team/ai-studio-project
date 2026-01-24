"""Unit tests for ResourceLimitConfig domain entity.

Tests cover:
- ResourceLimitConfig creation with defaults
- Global vs project-specific config
- Job resource validation
- Default config factory method
"""

import pytest

from src.modules.quotas.domain.entities.resource_limit_config import ResourceLimitConfig
from src.modules.quotas.domain.value_objects import LimitRole, PriorityDefault


class TestLimitRoleEnum:
    """Tests for LimitRole enum."""

    def test_all_roles_defined(self) -> None:
        """Verify all required roles are defined."""
        expected_roles = {"ADMIN", "PROJECT_MANAGER", "ENGINEER", "VIEWER"}
        actual_roles = {r.name for r in LimitRole}
        assert actual_roles == expected_roles


class TestPriorityDefaultEnum:
    """Tests for PriorityDefault enum."""

    def test_all_priorities_defined(self) -> None:
        """Verify all required priorities are defined."""
        expected_priorities = {"HIGH", "MEDIUM", "LOW"}
        actual_priorities = {p.name for p in PriorityDefault}
        assert actual_priorities == expected_priorities


class TestResourceLimitConfigCreation:
    """Tests for ResourceLimitConfig entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating config with only required fields."""
        config = ResourceLimitConfig(
            id=1,
            config_name="engineer-config",
            role=LimitRole.ENGINEER,
        )
        assert config.id == 1
        assert config.config_name == "engineer-config"
        assert config.role == LimitRole.ENGINEER

    def test_default_project_id_is_none(self) -> None:
        """Test default project_id is None (global config)."""
        config = ResourceLimitConfig(
            id=1,
            config_name="global-config",
            role=LimitRole.ENGINEER,
        )
        assert config.project_id is None

    def test_default_resource_limits(self) -> None:
        """Test default resource limits."""
        config = ResourceLimitConfig(
            id=1,
            config_name="default-config",
            role=LimitRole.ENGINEER,
        )
        assert config.max_gpu_per_job == 8
        assert config.max_cpu_per_job == 96
        assert config.max_memory_gb_per_job == 768
        assert config.max_storage_gb_per_job == 1000
        assert config.max_nodes_per_job == 8

    def test_default_priority_is_medium(self) -> None:
        """Test default priority is MEDIUM."""
        config = ResourceLimitConfig(
            id=1,
            config_name="default-config",
            role=LimitRole.ENGINEER,
        )
        assert config.priority_default == PriorityDefault.MEDIUM

    def test_create_with_all_fields(self) -> None:
        """Test creating config with all fields."""
        config = ResourceLimitConfig(
            id=1,
            config_name="admin-config",
            role=LimitRole.ADMIN,
            project_id=100,
            max_gpu_per_job=64,
            max_cpu_per_job=768,
            max_memory_gb_per_job=6144,
            max_storage_gb_per_job=10000,
            max_nodes_per_job=64,
            priority_default=PriorityDefault.HIGH,
        )
        assert config.project_id == 100
        assert config.max_gpu_per_job == 64
        assert config.priority_default == PriorityDefault.HIGH


class TestResourceLimitConfigMethods:
    """Tests for ResourceLimitConfig methods."""

    def test_is_global_config_when_no_project(self) -> None:
        """Test is_global_config returns True when project_id is None."""
        config = ResourceLimitConfig(
            id=1,
            config_name="global-config",
            role=LimitRole.ENGINEER,
        )
        assert config.is_global_config()

    def test_is_global_config_when_has_project(self) -> None:
        """Test is_global_config returns False when project_id is set."""
        config = ResourceLimitConfig(
            id=1,
            config_name="project-config",
            role=LimitRole.ENGINEER,
            project_id=100,
        )
        assert not config.is_global_config()


class TestResourceLimitConfigValidation:
    """Tests for ResourceLimitConfig job resource validation."""

    @pytest.fixture
    def config(self) -> ResourceLimitConfig:
        """Create a config for validation testing."""
        return ResourceLimitConfig(
            id=1,
            config_name="test-config",
            role=LimitRole.ENGINEER,
            max_gpu_per_job=8,
            max_cpu_per_job=96,
            max_memory_gb_per_job=768,
            max_storage_gb_per_job=1000,
            max_nodes_per_job=8,
        )

    def test_validate_job_resources_success(
        self, config: ResourceLimitConfig
    ) -> None:
        """Test validate_job_resources returns True for valid resources."""
        is_valid, error = config.validate_job_resources(
            gpu_count=4,
            cpu_cores=48,
            memory_gb=384,
            storage_gb=500,
            node_count=4,
        )
        assert is_valid is True
        assert error is None

    def test_validate_job_resources_at_limits(
        self, config: ResourceLimitConfig
    ) -> None:
        """Test validate_job_resources passes at exact limits."""
        is_valid, error = config.validate_job_resources(
            gpu_count=8,
            cpu_cores=96,
            memory_gb=768,
            storage_gb=1000,
            node_count=8,
        )
        assert is_valid is True
        assert error is None

    def test_validate_job_resources_gpu_exceeded(
        self, config: ResourceLimitConfig
    ) -> None:
        """Test validate_job_resources fails when GPU exceeds limit."""
        is_valid, error = config.validate_job_resources(
            gpu_count=16,
            cpu_cores=48,
            memory_gb=384,
            storage_gb=500,
            node_count=4,
        )
        assert is_valid is False
        assert "GPU count" in error
        assert "16" in error
        assert "8" in error

    def test_validate_job_resources_cpu_exceeded(
        self, config: ResourceLimitConfig
    ) -> None:
        """Test validate_job_resources fails when CPU exceeds limit."""
        is_valid, error = config.validate_job_resources(
            gpu_count=4,
            cpu_cores=128,
            memory_gb=384,
            storage_gb=500,
            node_count=4,
        )
        assert is_valid is False
        assert "CPU cores" in error

    def test_validate_job_resources_memory_exceeded(
        self, config: ResourceLimitConfig
    ) -> None:
        """Test validate_job_resources fails when memory exceeds limit."""
        is_valid, error = config.validate_job_resources(
            gpu_count=4,
            cpu_cores=48,
            memory_gb=1024,
            storage_gb=500,
            node_count=4,
        )
        assert is_valid is False
        assert "Memory" in error

    def test_validate_job_resources_storage_exceeded(
        self, config: ResourceLimitConfig
    ) -> None:
        """Test validate_job_resources fails when storage exceeds limit."""
        is_valid, error = config.validate_job_resources(
            gpu_count=4,
            cpu_cores=48,
            memory_gb=384,
            storage_gb=2000,
            node_count=4,
        )
        assert is_valid is False
        assert "Storage" in error

    def test_validate_job_resources_nodes_exceeded(
        self, config: ResourceLimitConfig
    ) -> None:
        """Test validate_job_resources fails when node count exceeds limit."""
        is_valid, error = config.validate_job_resources(
            gpu_count=4,
            cpu_cores=48,
            memory_gb=384,
            storage_gb=500,
            node_count=16,
        )
        assert is_valid is False
        assert "Node count" in error


class TestResourceLimitConfigDefaults:
    """Tests for ResourceLimitConfig default factory method."""

    def test_get_default_for_admin(self) -> None:
        """Test get_default_for_role returns correct config for ADMIN."""
        config = ResourceLimitConfig.get_default_for_role(LimitRole.ADMIN)
        assert config.role == LimitRole.ADMIN
        assert config.max_gpu_per_job == 64
        assert config.max_cpu_per_job == 768
        assert config.max_nodes_per_job == 64
        assert config.priority_default == PriorityDefault.HIGH

    def test_get_default_for_project_manager(self) -> None:
        """Test get_default_for_role returns correct config for PROJECT_MANAGER."""
        config = ResourceLimitConfig.get_default_for_role(LimitRole.PROJECT_MANAGER)
        assert config.role == LimitRole.PROJECT_MANAGER
        assert config.max_gpu_per_job == 32
        assert config.max_cpu_per_job == 384
        assert config.max_nodes_per_job == 32
        assert config.priority_default == PriorityDefault.MEDIUM

    def test_get_default_for_engineer(self) -> None:
        """Test get_default_for_role returns correct config for ENGINEER."""
        config = ResourceLimitConfig.get_default_for_role(LimitRole.ENGINEER)
        assert config.role == LimitRole.ENGINEER
        assert config.max_gpu_per_job == 8
        assert config.max_cpu_per_job == 96
        assert config.max_nodes_per_job == 8
        assert config.priority_default == PriorityDefault.MEDIUM

    def test_get_default_for_viewer(self) -> None:
        """Test get_default_for_role returns correct config for VIEWER."""
        config = ResourceLimitConfig.get_default_for_role(LimitRole.VIEWER)
        assert config.role == LimitRole.VIEWER
        assert config.max_gpu_per_job == 0
        assert config.max_cpu_per_job == 0
        assert config.max_nodes_per_job == 0
        assert config.priority_default == PriorityDefault.LOW

    def test_get_default_config_is_global(self) -> None:
        """Test get_default_for_role returns global config (no project_id)."""
        config = ResourceLimitConfig.get_default_for_role(LimitRole.ENGINEER)
        assert config.is_global_config()
        assert config.project_id is None

    def test_get_default_config_has_placeholder_id(self) -> None:
        """Test get_default_for_role returns config with id=0."""
        config = ResourceLimitConfig.get_default_for_role(LimitRole.ENGINEER)
        assert config.id == 0

    def test_get_default_config_name_contains_role(self) -> None:
        """Test get_default_for_role generates name with role."""
        config = ResourceLimitConfig.get_default_for_role(LimitRole.ENGINEER)
        assert "engineer" in config.config_name.lower()
