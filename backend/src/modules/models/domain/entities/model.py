"""Model domain entity for trained model management."""

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.utils import utc_now

from ..value_objects import MODEL_STATE_TRANSITIONS, ModelFramework, ModelStatus


@dataclass
class Model:
    """Model domain entity for trained models."""

    # === Required fields ===
    id: int
    model_name: str
    owner_id: int

    # === Version ===
    version: str = "v1"

    # === Optional identification ===
    display_name: str | None = None
    description: str | None = None

    # === Associated relationships ===
    training_job_id: int | None = None
    checkpoint_id: int | None = None

    # === Storage location ===
    model_uri: str | None = None  # S3 URI

    # === SageMaker Model Registry integration ===
    registry_arn: str | None = None
    registry_status: str | None = None

    # === Training metrics ===
    metrics: dict | None = None  # {accuracy, loss, f1_score}
    hyperparameters: dict | None = None

    # === Framework information ===
    framework: ModelFramework = ModelFramework.PYTORCH
    framework_version: str | None = None

    # === Status ===
    status: ModelStatus = ModelStatus.TRAINING

    # === Model metadata ===
    size_bytes: int | None = None
    model_format: str | None = None  # safetensors, pickle, onnx
    tags: list[str] | None = None

    # === Audit fields ===
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    registered_at: datetime | None = None
    archived_at: datetime | None = None

    def can_transition_to(self, new_status: ModelStatus) -> bool:
        """Check if transition to new_status is valid."""
        valid_transitions = MODEL_STATE_TRANSITIONS.get(self.status, set())
        return new_status in valid_transitions

    def transition_to(self, new_status: ModelStatus) -> None:
        """Transition to new status if valid.

        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                "Model", self.status.value, new_status.value
            )
        self.status = new_status
        self.updated_at = utc_now()

    def is_training(self) -> bool:
        """Check if model is currently training."""
        return self.status == ModelStatus.TRAINING

    def is_registered(self) -> bool:
        """Check if model is registered."""
        return self.status == ModelStatus.REGISTERED

    def is_deployed(self) -> bool:
        """Check if model is deployed."""
        return self.status == ModelStatus.DEPLOYED

    def is_archived(self) -> bool:
        """Check if model is archived."""
        return self.status == ModelStatus.ARCHIVED

    def is_terminal(self) -> bool:
        """Check if model is in a terminal state."""
        return self.status == ModelStatus.FAILED

    def can_deploy(self) -> bool:
        """Check if model can be deployed."""
        return self.status == ModelStatus.REGISTERED

    def register(self) -> None:
        """Register the model (transition from TRAINING to REGISTERED).

        Raises:
            InvalidStateTransitionError: If model cannot be registered
        """
        if self.status != ModelStatus.TRAINING:
            raise InvalidStateTransitionError(
                "Model", self.status.value, ModelStatus.REGISTERED.value
            )
        self.transition_to(ModelStatus.REGISTERED)
        self.registered_at = utc_now()

    def deploy(self) -> None:
        """Deploy the model.

        Raises:
            InvalidStateTransitionError: If model cannot be deployed
        """
        if not self.can_deploy():
            raise InvalidStateTransitionError(
                "Model", self.status.value, ModelStatus.DEPLOYED.value
            )
        self.transition_to(ModelStatus.DEPLOYED)

    def archive(self) -> None:
        """Archive the model.

        Raises:
            InvalidStateTransitionError: If model cannot be archived
        """
        if not self.can_transition_to(ModelStatus.ARCHIVED):
            raise InvalidStateTransitionError(
                "Model", self.status.value, ModelStatus.ARCHIVED.value
            )
        self.transition_to(ModelStatus.ARCHIVED)
        self.archived_at = utc_now()

    def fail(self) -> None:
        """Mark model as failed."""
        if self.can_transition_to(ModelStatus.FAILED):
            self.transition_to(ModelStatus.FAILED)
        else:
            # Force transition for TRAINING state
            self.status = ModelStatus.FAILED
            self.updated_at = utc_now()

    @staticmethod
    def parse_version(version: str) -> int:
        """Parse version string (e.g., 'v1') to integer."""
        return int(version[1:])

    @staticmethod
    def increment_version(version: str) -> str:
        """Increment version string (e.g., 'v1' -> 'v2')."""
        num = Model.parse_version(version)
        return f"v{num + 1}"

    def compare_version(self, other: "Model") -> int:
        """Compare version with another model.

        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        self_num = self.parse_version(self.version)
        other_num = self.parse_version(other.version)
        if self_num < other_num:
            return -1
        elif self_num > other_num:
            return 1
        return 0
