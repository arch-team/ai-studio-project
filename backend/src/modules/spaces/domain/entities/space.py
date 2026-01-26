"""Space domain entity - SageMaker Spaces for online development environments."""

from datetime import datetime

from pydantic import Field

from src.shared.domain import PydanticEntity
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.utils import utc_now

from ..value_objects import (
    INSTANCE_TYPE_RESOURCES,
    SPACE_STATE_TRANSITIONS,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)


class Space(PydanticEntity):
    """Development space domain entity for online IDE environments."""

    id: str | None = None  # UUID
    space_name: str = Field(min_length=1, max_length=255)
    owner_id: int

    # Configuration
    instance_type: SpaceInstanceType = SpaceInstanceType.ML_G5_XLARGE
    space_type: SpaceType = SpaceType.JUPYTER
    storage_size_gb: int = 20

    # Status
    status: SpaceStatus = SpaceStatus.PENDING

    # SageMaker integration
    lifecycle_config_arn: str | None = None
    sagemaker_space_arn: str | None = None

    # Timestamps
    deleted_at: datetime | None = None

    # ========== 业务方法 ==========

    def can_transition_to(self, new_status: SpaceStatus) -> bool:
        """Check if transition to new_status is valid."""
        valid_transitions = SPACE_STATE_TRANSITIONS.get(self.status, set())
        return new_status in valid_transitions

    def transition_to(self, new_status: SpaceStatus) -> None:
        """Transition to new status if valid."""
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError("Space", self.status.value, new_status.value)
        self.status = new_status
        self.touch()

        if new_status == SpaceStatus.DELETED:
            self.deleted_at = utc_now()

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
            raise InvalidStateTransitionError("Space", self.status.value, SpaceStatus.RUNNING.value)
        self.transition_to(SpaceStatus.RUNNING)

    def stop(self) -> None:
        """Stop the space."""
        if not self.can_stop():
            raise InvalidStateTransitionError("Space", self.status.value, SpaceStatus.STOPPED.value)
        self.transition_to(SpaceStatus.STOPPED)

    def delete(self) -> None:
        """Mark space as deleted (soft delete)."""
        if not self.can_delete():
            raise InvalidStateTransitionError("Space", self.status.value, SpaceStatus.DELETED.value)
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
        """Get resource requirements based on instance type."""
        return INSTANCE_TYPE_RESOURCES.get(
            self.instance_type,
            {"cpu_cores": 4, "memory_gb": 16, "gpu_count": 1},
        )

    def validate_quota(
        self,
        available_cpu: int,
        available_memory_gb: int,
        available_gpu: int,
    ) -> tuple[bool, str | None]:
        """Validate space resource requirements against available quota."""
        requirements = self.get_resource_requirements()

        if requirements["cpu_cores"] > available_cpu:
            return (
                False,
                f"Insufficient CPU: need {requirements['cpu_cores']}, have {available_cpu}",
            )

        if requirements["memory_gb"] > available_memory_gb:
            return (
                False,
                f"Insufficient memory: need {requirements['memory_gb']}GB, have {available_memory_gb}GB",
            )

        if requirements["gpu_count"] > available_gpu:
            return (
                False,
                f"Insufficient GPU: need {requirements['gpu_count']}, have {available_gpu}",
            )

        return True, None
