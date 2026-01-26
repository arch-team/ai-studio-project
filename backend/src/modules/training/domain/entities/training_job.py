"""TrainingJob domain entity for distributed training task management."""

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.shared.domain import PydanticEntity
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.utils import utc_now

from ..value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
)
from ..value_objects.job_status import TRAINING_JOB_STATE_TRANSITIONS


class TrainingJob(PydanticEntity):
    """Training job domain entity for distributed training tasks."""

    # === Required fields ===
    job_name: str = Field(min_length=1, max_length=255)
    owner_id: int
    image_uri: str
    instance_type: str
    entrypoint_command: list[str]

    # === Optional identification ===
    display_name: str | None = None
    description: str | None = None

    # === Compute configuration ===
    node_count: int = 1
    tasks_per_node: int = 1

    # === Training parameters ===
    hyperparameters: dict | None = None
    max_epochs: int | None = None
    batch_size: int | None = None
    learning_rate: float | None = None
    environment_variables: dict | None = None

    # === Distribution configuration ===
    distribution_strategy: DistributionStrategy = DistributionStrategy.DDP
    mixed_precision: bool = False

    # === Spot instance configuration ===
    use_spot_instances: bool = False
    spot_interruption_behavior: SpotInterruptionBehavior | None = None

    # === Scheduling configuration ===
    priority: JobPriority = JobPriority.MEDIUM
    status: JobStatus = JobStatus.SUBMITTED

    # === Data mounting ===
    dataset_id: int | None = None
    data_mount_path: str | None = None
    checkpoint_mount_path: str | None = None
    checkpoint_interval: int | None = None

    # === Auto-recovery configuration (HyperPod Elastic Agent) ===
    auto_resume_checkpoint_id: int | None = None

    # === HyperPod/Kueue status ===
    hyperpod_job_arn: str | None = None  # ARN of the HyperPod training job
    hyperpod_status: str | None = None
    kueue_workload_name: str | None = None
    kueue_status: str | None = None

    # === Pod statistics ===
    total_pods: int | None = None
    running_pods: int = 0
    failed_pods: int = 0
    preemption_count: int = 0

    # === Training metrics ===
    current_epoch: int | None = None
    current_step: int | None = None
    latest_loss: Decimal | None = None
    latest_accuracy: Decimal | None = None

    # === Time statistics ===
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None

    # === Cost statistics ===
    total_gpu_hours: Decimal | None = None
    estimated_cost_usd: Decimal | None = None

    # === Error information ===
    error_message: str | None = None
    failure_reason: str | None = None

    # ========== 状态转换方法 ==========

    def can_transition_to(self, new_status: JobStatus) -> bool:
        """Check if transition to new_status is valid."""
        valid_transitions = TRAINING_JOB_STATE_TRANSITIONS.get(self.status, set())
        return new_status in valid_transitions

    def transition_to(self, new_status: JobStatus) -> None:
        """Transition to new status if valid.

        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError("TrainingJob", self.status.value, new_status.value)

        # Track preemption count
        if new_status == JobStatus.PREEMPTED:
            self.preemption_count += 1

        self.status = new_status
        self.touch()

        # Set timestamps based on status
        if new_status == JobStatus.RUNNING and self.started_at is None:
            self.started_at = utc_now()
        elif new_status in (JobStatus.COMPLETED, JobStatus.FAILED):
            self.completed_at = utc_now()

    # ========== 状态查询方法 ==========

    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == JobStatus.RUNNING

    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    def can_pause(self) -> bool:
        """Check if job can be paused."""
        return self.status == JobStatus.RUNNING

    def can_resume(self) -> bool:
        """Check if job can be resumed."""
        return self.status in (JobStatus.PAUSED, JobStatus.PREEMPTED)

    # ========== 状态操作方法 ==========

    def pause(self) -> None:
        """Pause the training job."""
        if not self.can_pause():
            raise InvalidStateTransitionError("TrainingJob", self.status.value, JobStatus.PAUSED.value)
        self.transition_to(JobStatus.PAUSED)

    def resume(self) -> None:
        """Resume a paused or preempted job."""
        if not self.can_resume():
            raise InvalidStateTransitionError("TrainingJob", self.status.value, JobStatus.RUNNING.value)
        self.transition_to(JobStatus.RUNNING)

    def complete(self) -> None:
        """Mark job as completed."""
        self.transition_to(JobStatus.COMPLETED)

    def fail(self, error_message: str | None = None, failure_reason: str | None = None) -> None:
        """Mark job as failed with optional error details."""
        self.error_message = error_message
        self.failure_reason = failure_reason
        self.transition_to(JobStatus.FAILED)
