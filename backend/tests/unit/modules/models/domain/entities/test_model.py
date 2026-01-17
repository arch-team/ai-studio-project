"""Unit tests for Model domain entity.

Tests cover:
- Enum types validation
- State machine transitions
- Version management
- Business rules
- Entity creation
"""

from datetime import datetime

import pytest

from src.modules.models.domain.entities.model import (
    MODEL_STATE_TRANSITIONS,
    Model,
    ModelFramework,
    ModelStatus,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


class TestModelFrameworkEnum:
    """Tests for ModelFramework enum."""

    def test_all_frameworks_defined(self) -> None:
        """Verify all required frameworks are defined."""
        expected_frameworks = {"PYTORCH", "TENSORFLOW", "JAX", "OTHER"}
        actual_frameworks = {f.name for f in ModelFramework}
        assert actual_frameworks == expected_frameworks

    def test_framework_values_match_database(self) -> None:
        """Verify enum values match database enum values."""
        assert ModelFramework.PYTORCH.value == "PYTORCH"
        assert ModelFramework.TENSORFLOW.value == "TENSORFLOW"
        assert ModelFramework.JAX.value == "JAX"
        assert ModelFramework.OTHER.value == "OTHER"


class TestModelStatusEnum:
    """Tests for ModelStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all required statuses are defined."""
        expected_statuses = {"TRAINING", "REGISTERED", "DEPLOYED", "ARCHIVED", "FAILED"}
        actual_statuses = {s.name for s in ModelStatus}
        assert actual_statuses == expected_statuses

    def test_status_values_match_database(self) -> None:
        """Verify enum values match database enum values."""
        assert ModelStatus.TRAINING.value == "TRAINING"
        assert ModelStatus.REGISTERED.value == "REGISTERED"
        assert ModelStatus.DEPLOYED.value == "DEPLOYED"
        assert ModelStatus.ARCHIVED.value == "ARCHIVED"
        assert ModelStatus.FAILED.value == "FAILED"


class TestModelStateTransitions:
    """Tests for Model state machine transitions."""

    @pytest.fixture
    def model(self) -> Model:
        """Create a basic model for testing."""
        return Model(
            id=1,
            model_name="my-llm-model",
            owner_id=1,
        )

    def test_training_to_registered_valid(self, model: Model) -> None:
        """Test valid transition: TRAINING -> REGISTERED."""
        assert model.status == ModelStatus.TRAINING
        assert model.can_transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.REGISTERED)
        assert model.status == ModelStatus.REGISTERED

    def test_training_to_failed_valid(self, model: Model) -> None:
        """Test valid transition: TRAINING -> FAILED."""
        assert model.can_transition_to(ModelStatus.FAILED)
        model.transition_to(ModelStatus.FAILED)
        assert model.status == ModelStatus.FAILED

    def test_registered_to_deployed_valid(self, model: Model) -> None:
        """Test valid transition: REGISTERED -> DEPLOYED."""
        model.transition_to(ModelStatus.REGISTERED)
        assert model.can_transition_to(ModelStatus.DEPLOYED)
        model.transition_to(ModelStatus.DEPLOYED)
        assert model.status == ModelStatus.DEPLOYED

    def test_registered_to_archived_valid(self, model: Model) -> None:
        """Test valid transition: REGISTERED -> ARCHIVED."""
        model.transition_to(ModelStatus.REGISTERED)
        assert model.can_transition_to(ModelStatus.ARCHIVED)
        model.transition_to(ModelStatus.ARCHIVED)
        assert model.status == ModelStatus.ARCHIVED

    def test_deployed_to_registered_valid(self, model: Model) -> None:
        """Test valid transition: DEPLOYED -> REGISTERED (undeploy)."""
        model.transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.DEPLOYED)
        assert model.can_transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.REGISTERED)
        assert model.status == ModelStatus.REGISTERED

    def test_deployed_to_archived_valid(self, model: Model) -> None:
        """Test valid transition: DEPLOYED -> ARCHIVED."""
        model.transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.DEPLOYED)
        assert model.can_transition_to(ModelStatus.ARCHIVED)
        model.transition_to(ModelStatus.ARCHIVED)
        assert model.status == ModelStatus.ARCHIVED

    def test_archived_to_registered_valid(self, model: Model) -> None:
        """Test valid transition: ARCHIVED -> REGISTERED (restore)."""
        model.transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.ARCHIVED)
        assert model.can_transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.REGISTERED)
        assert model.status == ModelStatus.REGISTERED

    def test_failed_is_terminal(self, model: Model) -> None:
        """Test that FAILED is a terminal state."""
        model.transition_to(ModelStatus.FAILED)
        assert model.is_terminal()
        assert not model.can_transition_to(ModelStatus.TRAINING)
        assert not model.can_transition_to(ModelStatus.REGISTERED)

    def test_invalid_transition_training_to_deployed(self, model: Model) -> None:
        """Test invalid transition: TRAINING -> DEPLOYED (must register first)."""
        assert not model.can_transition_to(ModelStatus.DEPLOYED)
        with pytest.raises(InvalidStateTransitionError):
            model.transition_to(ModelStatus.DEPLOYED)

    def test_invalid_transition_training_to_archived(self, model: Model) -> None:
        """Test invalid transition: TRAINING -> ARCHIVED (must register first)."""
        assert not model.can_transition_to(ModelStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            model.transition_to(ModelStatus.ARCHIVED)

    def test_invalid_transition_raises_domain_exception(self, model: Model) -> None:
        """Test that invalid transitions raise InvalidStateTransitionError."""
        model.transition_to(ModelStatus.FAILED)
        with pytest.raises(InvalidStateTransitionError):
            model.transition_to(ModelStatus.REGISTERED)


class TestModelStateTransitionMatrix:
    """Tests for the state transition matrix constant."""

    def test_all_statuses_have_transitions(self) -> None:
        """Verify all statuses are keys in the transition matrix."""
        for status in ModelStatus:
            assert status in MODEL_STATE_TRANSITIONS

    def test_failed_is_terminal(self) -> None:
        """Verify FAILED is a terminal state."""
        assert MODEL_STATE_TRANSITIONS[ModelStatus.FAILED] == set()

    def test_training_transitions(self) -> None:
        """Verify TRAINING state transitions."""
        expected = {ModelStatus.REGISTERED, ModelStatus.FAILED}
        assert MODEL_STATE_TRANSITIONS[ModelStatus.TRAINING] == expected

    def test_registered_transitions(self) -> None:
        """Verify REGISTERED state transitions."""
        expected = {ModelStatus.DEPLOYED, ModelStatus.ARCHIVED}
        assert MODEL_STATE_TRANSITIONS[ModelStatus.REGISTERED] == expected

    def test_deployed_transitions(self) -> None:
        """Verify DEPLOYED state transitions."""
        expected = {ModelStatus.REGISTERED, ModelStatus.ARCHIVED}
        assert MODEL_STATE_TRANSITIONS[ModelStatus.DEPLOYED] == expected

    def test_archived_transitions(self) -> None:
        """Verify ARCHIVED state transitions (can restore)."""
        expected = {ModelStatus.REGISTERED}
        assert MODEL_STATE_TRANSITIONS[ModelStatus.ARCHIVED] == expected


class TestModelVersioning:
    """Tests for model versioning."""

    def test_parse_version_v1(self) -> None:
        """Test parsing version v1."""
        assert Model.parse_version("v1") == 1

    def test_parse_version_v10(self) -> None:
        """Test parsing version v10."""
        assert Model.parse_version("v10") == 10

    def test_parse_version_v123(self) -> None:
        """Test parsing version v123."""
        assert Model.parse_version("v123") == 123

    def test_increment_version_from_v1(self) -> None:
        """Test incrementing version from v1."""
        assert Model.increment_version("v1") == "v2"

    def test_increment_version_from_v10(self) -> None:
        """Test incrementing version from v10."""
        assert Model.increment_version("v10") == "v11"

    def test_increment_version_from_v99(self) -> None:
        """Test incrementing version from v99."""
        assert Model.increment_version("v99") == "v100"

    def test_compare_version_same(self) -> None:
        """Test comparing same versions."""
        model1 = Model(id=1, model_name="test", owner_id=1, version="v5")
        model2 = Model(id=2, model_name="test", owner_id=1, version="v5")
        assert model1.compare_version(model2) == 0

    def test_compare_version_greater(self) -> None:
        """Test comparing when self is greater."""
        model1 = Model(id=1, model_name="test", owner_id=1, version="v10")
        model2 = Model(id=2, model_name="test", owner_id=1, version="v5")
        assert model1.compare_version(model2) == 1

    def test_compare_version_lesser(self) -> None:
        """Test comparing when self is lesser."""
        model1 = Model(id=1, model_name="test", owner_id=1, version="v3")
        model2 = Model(id=2, model_name="test", owner_id=1, version="v7")
        assert model1.compare_version(model2) == -1


class TestModelBusinessRules:
    """Tests for Model business rules."""

    @pytest.fixture
    def model(self) -> Model:
        """Create a basic model for testing."""
        return Model(
            id=1,
            model_name="my-llm-model",
            owner_id=1,
        )

    def test_is_training(self, model: Model) -> None:
        """Test is_training() method."""
        assert model.is_training()
        model.transition_to(ModelStatus.REGISTERED)
        assert not model.is_training()

    def test_is_registered(self, model: Model) -> None:
        """Test is_registered() method."""
        assert not model.is_registered()
        model.transition_to(ModelStatus.REGISTERED)
        assert model.is_registered()

    def test_is_deployed(self, model: Model) -> None:
        """Test is_deployed() method."""
        assert not model.is_deployed()
        model.transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.DEPLOYED)
        assert model.is_deployed()

    def test_is_archived(self, model: Model) -> None:
        """Test is_archived() method."""
        assert not model.is_archived()
        model.transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.ARCHIVED)
        assert model.is_archived()

    def test_is_terminal_failed(self, model: Model) -> None:
        """Test is_terminal() for FAILED status."""
        assert not model.is_terminal()
        model.transition_to(ModelStatus.FAILED)
        assert model.is_terminal()

    def test_can_deploy_when_registered(self, model: Model) -> None:
        """Test can_deploy() returns True when REGISTERED."""
        model.transition_to(ModelStatus.REGISTERED)
        assert model.can_deploy()

    def test_cannot_deploy_when_training(self, model: Model) -> None:
        """Test can_deploy() returns False when TRAINING."""
        assert not model.can_deploy()

    def test_cannot_deploy_when_archived(self, model: Model) -> None:
        """Test can_deploy() returns False when ARCHIVED."""
        model.transition_to(ModelStatus.REGISTERED)
        model.transition_to(ModelStatus.ARCHIVED)
        assert not model.can_deploy()

    def test_register_from_training(self, model: Model) -> None:
        """Test register() method."""
        assert model.registered_at is None
        model.register()
        assert model.status == ModelStatus.REGISTERED
        assert model.registered_at is not None

    def test_register_when_not_training_raises_error(self, model: Model) -> None:
        """Test register() raises error when not TRAINING."""
        model.transition_to(ModelStatus.FAILED)
        with pytest.raises(InvalidStateTransitionError):
            model.register()

    def test_deploy(self, model: Model) -> None:
        """Test deploy() method."""
        model.register()
        model.deploy()
        assert model.status == ModelStatus.DEPLOYED

    def test_deploy_when_not_registered_raises_error(self, model: Model) -> None:
        """Test deploy() raises error when not REGISTERED."""
        with pytest.raises(InvalidStateTransitionError):
            model.deploy()

    def test_archive(self, model: Model) -> None:
        """Test archive() method."""
        model.register()
        assert model.archived_at is None
        model.archive()
        assert model.status == ModelStatus.ARCHIVED
        assert model.archived_at is not None

    def test_archive_when_not_deployable_state_raises_error(self, model: Model) -> None:
        """Test archive() raises error when in invalid state."""
        with pytest.raises(InvalidStateTransitionError):
            model.archive()

    def test_fail_sets_status(self, model: Model) -> None:
        """Test fail() method sets status to FAILED."""
        model.fail()
        assert model.status == ModelStatus.FAILED


class TestModelCreation:
    """Tests for Model entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating model with only required fields."""
        model = Model(
            id=1,
            model_name="my-model",
            owner_id=1,
        )
        assert model.id == 1
        assert model.model_name == "my-model"
        assert model.owner_id == 1

    def test_default_version_is_v1(self) -> None:
        """Test default version is v1."""
        model = Model(
            id=1,
            model_name="my-model",
            owner_id=1,
        )
        assert model.version == "v1"

    def test_default_framework_is_pytorch(self) -> None:
        """Test default framework is PYTORCH."""
        model = Model(
            id=1,
            model_name="my-model",
            owner_id=1,
        )
        assert model.framework == ModelFramework.PYTORCH

    def test_default_status_is_training(self) -> None:
        """Test default status is TRAINING."""
        model = Model(
            id=1,
            model_name="my-model",
            owner_id=1,
        )
        assert model.status == ModelStatus.TRAINING

    def test_create_with_all_optional_fields(self) -> None:
        """Test creating model with all fields."""
        model = Model(
            id=1,
            model_name="my-model",
            owner_id=1,
            version="v5",
            display_name="My Custom Model",
            description="A fine-tuned LLM",
            training_job_id=10,
            checkpoint_id=100,
            model_uri="s3://bucket/models/my-model/v5",
            registry_arn="arn:aws:sagemaker:us-east-1:123456789012:model-package/my-model",
            registry_status="APPROVED",
            metrics={"accuracy": 0.95, "loss": 0.05},
            hyperparameters={"learning_rate": 0.001, "epochs": 100},
            framework=ModelFramework.TENSORFLOW,
            framework_version="2.15.0",
            status=ModelStatus.REGISTERED,
            size_bytes=1073741824,
            model_format="safetensors",
            tags=["production", "llm", "fine-tuned"],
        )
        assert model.version == "v5"
        assert model.display_name == "My Custom Model"
        assert model.training_job_id == 10
        assert model.checkpoint_id == 100
        assert model.framework == ModelFramework.TENSORFLOW
        assert model.status == ModelStatus.REGISTERED
        assert model.tags == ["production", "llm", "fine-tuned"]

    def test_created_at_set_on_creation(self) -> None:
        """Test created_at is set automatically."""
        model = Model(
            id=1,
            model_name="my-model",
            owner_id=1,
        )
        assert model.created_at is not None
        assert isinstance(model.created_at, datetime)

    def test_updated_at_set_on_creation(self) -> None:
        """Test updated_at is set automatically."""
        model = Model(
            id=1,
            model_name="my-model",
            owner_id=1,
        )
        assert model.updated_at is not None
        assert isinstance(model.updated_at, datetime)
