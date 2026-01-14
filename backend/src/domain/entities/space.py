"""Space domain entity - SageMaker Spaces for online development environments."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SpaceInstanceType(Enum):
    """Space instance type options."""

    ML_T3_MEDIUM = "ml.t3.medium"
    ML_T3_LARGE = "ml.t3.large"
    ML_G4DN_XLARGE = "ml.g4dn.xlarge"
    ML_G5_XLARGE = "ml.g5.xlarge"
    ML_G5_2XLARGE = "ml.g5.2xlarge"


class SpaceType(Enum):
    """Space IDE type."""

    JUPYTER = "jupyter"
    VSCODE = "vscode"
    RSTUDIO = "rstudio"


class SpaceStatus(Enum):
    """Space lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETED = "deleted"


# Valid state transitions
SPACE_STATE_TRANSITIONS = {
    SpaceStatus.PENDING: {SpaceStatus.RUNNING, SpaceStatus.FAILED},
    SpaceStatus.RUNNING: {SpaceStatus.STOPPED, SpaceStatus.FAILED},
    SpaceStatus.STOPPED: {SpaceStatus.RUNNING, SpaceStatus.FAILED, SpaceStatus.DELETED},
    SpaceStatus.FAILED: {SpaceStatus.PENDING, SpaceStatus.DELETED},
    SpaceStatus.DELETED: set(),  # Terminal state
}


@dataclass
class Space:
    """Development space domain entity for online IDE environments.

    Represents a SageMaker Space for JupyterLab/VS Code development.
    """

    id: str  # UUID
    space_name: str
    owner_id: int

    # Configuration
    instance_type: SpaceInstanceType = SpaceInstanceType.ML_G5_XLARGE
    space_type: SpaceType = SpaceType.JUPYTER
    storage_size_gb: int = 20

    # Status
    status: SpaceStatus = SpaceStatus.PENDING

    # SageMaker integration
    lifecycle_config_arn: Optional[str] = None
    sagemaker_space_arn: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    def can_transition_to(self, new_status: SpaceStatus) -> bool:
        """Check if transition to new_status is valid."""
        valid_transitions = SPACE_STATE_TRANSITIONS.get(self.status, set())
        return new_status in valid_transitions

    def transition_to(self, new_status: SpaceStatus) -> None:
        """Transition to new status if valid.

        Raises:
            ValueError: If transition is not allowed
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Invalid state transition: {self.status.value} -> {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

        if new_status == SpaceStatus.DELETED:
            self.deleted_at = datetime.utcnow()

    def can_start(self) -> bool:
        """Check if space can be started."""
        return self.status in (SpaceStatus.PENDING, SpaceStatus.STOPPED)

    def can_stop(self) -> bool:
        """Check if space can be stopped."""
        return self.status == SpaceStatus.RUNNING

    def can_delete(self) -> bool:
        """Check if space can be deleted."""
        return self.status in (SpaceStatus.STOPPED, SpaceStatus.FAILED)

    def start(self) -> None:
        """Start the space."""
        if not self.can_start():
            raise ValueError(f"Cannot start space in {self.status.value} status")
        self.transition_to(SpaceStatus.RUNNING)

    def stop(self) -> None:
        """Stop the space."""
        if not self.can_stop():
            raise ValueError(f"Cannot stop space in {self.status.value} status")
        self.transition_to(SpaceStatus.STOPPED)

    def delete(self) -> None:
        """Mark space as deleted (soft delete)."""
        if not self.can_delete():
            raise ValueError(f"Cannot delete space in {self.status.value} status")
        self.transition_to(SpaceStatus.DELETED)

    def mark_failed(self) -> None:
        """Mark space as failed."""
        self.transition_to(SpaceStatus.FAILED)

    def is_active(self) -> bool:
        """Check if space is in an active (non-deleted) state."""
        return self.status != SpaceStatus.DELETED and self.deleted_at is None

    def is_running(self) -> bool:
        """Check if space is currently running."""
        return self.status == SpaceStatus.RUNNING

    def get_resource_requirements(self) -> dict[str, int]:
        """Get resource requirements based on instance type.

        Returns dict with cpu_cores, memory_gb, gpu_count.
        """
        resource_map = {
            SpaceInstanceType.ML_T3_MEDIUM: {"cpu_cores": 2, "memory_gb": 4, "gpu_count": 0},
            SpaceInstanceType.ML_T3_LARGE: {"cpu_cores": 2, "memory_gb": 8, "gpu_count": 0},
            SpaceInstanceType.ML_G4DN_XLARGE: {"cpu_cores": 4, "memory_gb": 16, "gpu_count": 1},
            SpaceInstanceType.ML_G5_XLARGE: {"cpu_cores": 4, "memory_gb": 16, "gpu_count": 1},
            SpaceInstanceType.ML_G5_2XLARGE: {"cpu_cores": 8, "memory_gb": 32, "gpu_count": 1},
        }
        return resource_map.get(
            self.instance_type,
            {"cpu_cores": 4, "memory_gb": 16, "gpu_count": 1},
        )

    def validate_quota(
        self,
        available_cpu: int,
        available_memory_gb: int,
        available_gpu: int,
    ) -> tuple[bool, Optional[str]]:
        """Validate space resource requirements against available quota.

        Returns:
            Tuple of (is_valid, error_message)
        """
        requirements = self.get_resource_requirements()

        if requirements["cpu_cores"] > available_cpu:
            return False, f"Insufficient CPU: need {requirements['cpu_cores']}, have {available_cpu}"

        if requirements["memory_gb"] > available_memory_gb:
            return False, f"Insufficient memory: need {requirements['memory_gb']}GB, have {available_memory_gb}GB"

        if requirements["gpu_count"] > available_gpu:
            return False, f"Insufficient GPU: need {requirements['gpu_count']}, have {available_gpu}"

        return True, None
