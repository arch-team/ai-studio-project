"""Unit tests for Space domain entity.

Tests cover:
- Space creation with defaults
- State machine transitions
- Business rules (can_start, can_stop, can_delete)
- Resource requirement validation
"""

import pytest

from src.modules.spaces.domain.entities.space import Space
from src.modules.spaces.domain.value_objects import (
    SPACE_STATE_TRANSITIONS,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


class TestSpaceStatusEnum:
    """Tests for SpaceStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all required statuses are defined."""
        expected_statuses = {"PENDING", "RUNNING", "STOPPED", "FAILED", "DELETED"}
        actual_statuses = {s.name for s in SpaceStatus}
        assert actual_statuses == expected_statuses


class TestSpaceTypeEnum:
    """Tests for SpaceType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all required types are defined."""
        expected_types = {"JUPYTER", "VSCODE", "RSTUDIO"}
        actual_types = {t.name for t in SpaceType}
        assert actual_types == expected_types


class TestSpaceInstanceTypeEnum:
    """Tests for SpaceInstanceType enum."""

    def test_common_instance_types_defined(self) -> None:
        """Verify common instance types are defined."""
        # Check some common instance types exist
        assert hasattr(SpaceInstanceType, "ML_G5_XLARGE")
        assert hasattr(SpaceInstanceType, "ML_G5_2XLARGE")


class TestSpaceCreation:
    """Tests for Space entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating space with only required fields."""
        space = Space(
            id="uuid-123",
            space_name="my-space",
            owner_id=1,
        )
        assert space.id == "uuid-123"
        assert space.space_name == "my-space"
        assert space.owner_id == 1

    def test_default_status_is_pending(self) -> None:
        """Test default status is PENDING."""
        space = Space(id="uuid", space_name="test", owner_id=1)
        assert space.status == SpaceStatus.PENDING

    def test_default_space_type_is_jupyter(self) -> None:
        """Test default space_type is JUPYTER."""
        space = Space(id="uuid", space_name="test", owner_id=1)
        assert space.space_type == SpaceType.JUPYTER

    def test_default_storage_size(self) -> None:
        """Test default storage_size_gb is 20."""
        space = Space(id="uuid", space_name="test", owner_id=1)
        assert space.storage_size_gb == 20

    def test_create_with_all_fields(self) -> None:
        """Test creating space with all fields."""
        space = Space(
            id="uuid-456",
            space_name="dev-space",
            owner_id=42,
            instance_type=SpaceInstanceType.ML_G5_2XLARGE,
            space_type=SpaceType.VSCODE,
            storage_size_gb=100,
            lifecycle_config_arn="arn:aws:sagemaker:...",
            sagemaker_space_arn="arn:aws:sagemaker:...:space/...",
        )
        assert space.instance_type == SpaceInstanceType.ML_G5_2XLARGE
        assert space.space_type == SpaceType.VSCODE
        assert space.storage_size_gb == 100


class TestSpaceStateTransitions:
    """Tests for Space state machine transitions."""

    @pytest.fixture
    def space(self) -> Space:
        """Create a basic space for testing."""
        return Space(id="uuid", space_name="test", owner_id=1)

    def test_pending_to_running_valid(self, space: Space) -> None:
        """Test valid transition: PENDING -> RUNNING."""
        assert space.status == SpaceStatus.PENDING
        assert space.can_transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.RUNNING)
        assert space.status == SpaceStatus.RUNNING

    def test_running_to_stopped_valid(self, space: Space) -> None:
        """Test valid transition: RUNNING -> STOPPED."""
        space.transition_to(SpaceStatus.RUNNING)
        assert space.can_transition_to(SpaceStatus.STOPPED)
        space.transition_to(SpaceStatus.STOPPED)
        assert space.status == SpaceStatus.STOPPED

    def test_stopped_to_running_valid(self, space: Space) -> None:
        """Test valid transition: STOPPED -> RUNNING (restart)."""
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        assert space.can_transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.RUNNING)
        assert space.status == SpaceStatus.RUNNING

    def test_stopped_to_deleted_valid(self, space: Space) -> None:
        """Test valid transition: STOPPED -> DELETED."""
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        assert space.can_transition_to(SpaceStatus.DELETED)
        space.transition_to(SpaceStatus.DELETED)
        assert space.status == SpaceStatus.DELETED

    def test_failed_to_deleted_valid(self, space: Space) -> None:
        """Test valid transition: FAILED -> DELETED."""
        space.transition_to(SpaceStatus.FAILED)
        assert space.can_transition_to(SpaceStatus.DELETED)
        space.transition_to(SpaceStatus.DELETED)
        assert space.status == SpaceStatus.DELETED

    def test_deleted_is_terminal(self, space: Space) -> None:
        """Test that DELETED is a terminal state."""
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        space.transition_to(SpaceStatus.DELETED)
        assert not space.can_transition_to(SpaceStatus.RUNNING)
        assert not space.can_transition_to(SpaceStatus.STOPPED)

    def test_invalid_transition_raises_exception(self, space: Space) -> None:
        """Test invalid transition raises InvalidStateTransitionError."""
        # PENDING -> DELETED is invalid
        assert not space.can_transition_to(SpaceStatus.DELETED)
        with pytest.raises(InvalidStateTransitionError):
            space.transition_to(SpaceStatus.DELETED)

    def test_transition_updates_timestamp(self, space: Space) -> None:
        """Test transition updates updated_at timestamp."""
        original_updated = space.updated_at
        space.transition_to(SpaceStatus.RUNNING)
        assert space.updated_at >= original_updated

    def test_delete_transition_sets_deleted_at(self, space: Space) -> None:
        """Test DELETED transition sets deleted_at."""
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        assert space.deleted_at is None
        space.transition_to(SpaceStatus.DELETED)
        assert space.deleted_at is not None


class TestSpaceBusinessRules:
    """Tests for Space business rule methods."""

    @pytest.fixture
    def space(self) -> Space:
        """Create a basic space for testing."""
        return Space(id="uuid", space_name="test", owner_id=1)

    def test_can_start_when_pending(self, space: Space) -> None:
        """Test can_start returns True when PENDING."""
        assert space.can_start()

    def test_can_start_when_stopped(self, space: Space) -> None:
        """Test can_start returns True when STOPPED."""
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        assert space.can_start()

    def test_cannot_start_when_running(self, space: Space) -> None:
        """Test can_start returns False when already RUNNING."""
        space.transition_to(SpaceStatus.RUNNING)
        assert not space.can_start()

    def test_can_stop_when_running(self, space: Space) -> None:
        """Test can_stop returns True when RUNNING."""
        space.transition_to(SpaceStatus.RUNNING)
        assert space.can_stop()

    def test_cannot_stop_when_stopped(self, space: Space) -> None:
        """Test can_stop returns False when already STOPPED."""
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        assert not space.can_stop()

    def test_can_delete_when_stopped(self, space: Space) -> None:
        """Test can_delete returns True when STOPPED."""
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        assert space.can_delete()

    def test_can_delete_when_failed(self, space: Space) -> None:
        """Test can_delete returns True when FAILED."""
        space.transition_to(SpaceStatus.FAILED)
        assert space.can_delete()

    def test_cannot_delete_when_running(self, space: Space) -> None:
        """Test can_delete returns False when RUNNING."""
        space.transition_to(SpaceStatus.RUNNING)
        assert not space.can_delete()

    def test_start_method(self, space: Space) -> None:
        """Test start() method transitions to RUNNING."""
        space.start()
        assert space.status == SpaceStatus.RUNNING

    def test_stop_method(self, space: Space) -> None:
        """Test stop() method transitions to STOPPED."""
        space.start()
        space.stop()
        assert space.status == SpaceStatus.STOPPED

    def test_delete_method(self, space: Space) -> None:
        """Test delete() method transitions to DELETED."""
        space.start()
        space.stop()
        space.delete()
        assert space.status == SpaceStatus.DELETED

    def test_mark_failed_method(self, space: Space) -> None:
        """Test mark_failed() method transitions to FAILED."""
        space.mark_failed()
        assert space.status == SpaceStatus.FAILED

    def test_is_active_when_running(self, space: Space) -> None:
        """Test is_active returns True when RUNNING."""
        space.start()
        assert space.is_active()

    def test_is_active_when_deleted(self, space: Space) -> None:
        """Test is_active returns False when DELETED."""
        space.start()
        space.stop()
        space.delete()
        assert not space.is_active()

    def test_is_running(self, space: Space) -> None:
        """Test is_running method."""
        assert not space.is_running()
        space.start()
        assert space.is_running()
        space.stop()
        assert not space.is_running()


class TestSpaceResourceValidation:
    """Tests for Space resource validation methods."""

    def test_get_resource_requirements(self) -> None:
        """Test get_resource_requirements returns correct values."""
        space = Space(
            id="uuid",
            space_name="test",
            owner_id=1,
            instance_type=SpaceInstanceType.ML_G5_XLARGE,
        )
        requirements = space.get_resource_requirements()
        assert "cpu_cores" in requirements
        assert "memory_gb" in requirements
        assert "gpu_count" in requirements

    def test_validate_quota_success(self) -> None:
        """Test validate_quota returns True when quota sufficient."""
        space = Space(id="uuid", space_name="test", owner_id=1)
        requirements = space.get_resource_requirements()

        is_valid, error = space.validate_quota(
            available_cpu=requirements["cpu_cores"] + 10,
            available_memory_gb=requirements["memory_gb"] + 10,
            available_gpu=requirements["gpu_count"] + 1,
        )
        assert is_valid is True
        assert error is None

    def test_validate_quota_insufficient_cpu(self) -> None:
        """Test validate_quota fails when CPU insufficient."""
        space = Space(id="uuid", space_name="test", owner_id=1)

        is_valid, error = space.validate_quota(
            available_cpu=0,
            available_memory_gb=1000,
            available_gpu=10,
        )
        assert is_valid is False
        assert "CPU" in error

    def test_validate_quota_insufficient_memory(self) -> None:
        """Test validate_quota fails when memory insufficient."""
        space = Space(id="uuid", space_name="test", owner_id=1)

        is_valid, error = space.validate_quota(
            available_cpu=1000,
            available_memory_gb=0,
            available_gpu=10,
        )
        assert is_valid is False
        assert "memory" in error

    def test_validate_quota_insufficient_gpu(self) -> None:
        """Test validate_quota fails when GPU insufficient."""
        space = Space(id="uuid", space_name="test", owner_id=1)

        is_valid, error = space.validate_quota(
            available_cpu=1000,
            available_memory_gb=1000,
            available_gpu=0,
        )
        assert is_valid is False
        assert "GPU" in error


class TestStateTransitionMatrix:
    """Tests for the state transition matrix constant."""

    def test_all_statuses_have_transitions(self) -> None:
        """Verify all statuses are keys in the transition matrix."""
        for status in SpaceStatus:
            assert status in SPACE_STATE_TRANSITIONS

    def test_deleted_has_no_transitions(self) -> None:
        """Verify DELETED state has empty transition set."""
        assert SPACE_STATE_TRANSITIONS[SpaceStatus.DELETED] == set()

    def test_pending_transitions(self) -> None:
        """Verify PENDING state transitions."""
        valid = SPACE_STATE_TRANSITIONS[SpaceStatus.PENDING]
        assert SpaceStatus.RUNNING in valid
        assert SpaceStatus.FAILED in valid


class TestSpaceRestartTransitions:
    """重启语义: 真实 App 启动需要时间，STOPPED 先进入 PENDING（启动中）."""

    @pytest.fixture
    def stopped_space(self) -> Space:
        space = Space(id="uuid", space_name="test", owner_id=1)
        space.transition_to(SpaceStatus.RUNNING)
        space.transition_to(SpaceStatus.STOPPED)
        return space

    def test_stopped_to_pending_valid(self, stopped_space: Space) -> None:
        """STOPPED -> PENDING 是合法转换（重启拉起 App）."""
        assert stopped_space.can_transition_to(SpaceStatus.PENDING)
        stopped_space.transition_to(SpaceStatus.PENDING)
        assert stopped_space.status == SpaceStatus.PENDING

    def test_mark_starting_from_stopped(self, stopped_space: Space) -> None:
        """mark_starting 将 STOPPED 置为 PENDING."""
        stopped_space.mark_starting()
        assert stopped_space.status == SpaceStatus.PENDING

    def test_mark_starting_when_pending_is_noop(self) -> None:
        """已处于 PENDING（App 启动中）时 mark_starting 幂等."""
        space = Space(id="uuid", space_name="test", owner_id=1)
        space.mark_starting()
        assert space.status == SpaceStatus.PENDING

    def test_mark_starting_when_running_raises(self) -> None:
        """RUNNING 状态不能再次启动."""
        space = Space(id="uuid", space_name="test", owner_id=1)
        space.transition_to(SpaceStatus.RUNNING)
        with pytest.raises(InvalidStateTransitionError):
            space.mark_starting()
