"""Training job status and related enums."""

from enum import Enum


class JobStatus(Enum):
    """Training job status (matches database jobstatus enum)."""

    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    PREEMPTED = "PREEMPTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DistributionStrategy(Enum):
    """Distributed training strategy."""

    DDP = "DDP"
    FSDP = "FSDP"
    DEEPSPEED = "DEEPSPEED"
    HOROVOD = "HOROVOD"


class JobPriority(Enum):
    """Job priority for Kueue preemptive scheduling."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SpotInterruptionBehavior(Enum):
    """Spot instance interruption behavior."""

    STOP = "STOP"
    TERMINATE = "TERMINATE"
    HIBERNATE = "HIBERNATE"


# Valid state transitions based on spec.md Training Job State Model
TRAINING_JOB_STATE_TRANSITIONS = {
    JobStatus.SUBMITTED: {JobStatus.RUNNING, JobStatus.FAILED},
    JobStatus.RUNNING: {
        JobStatus.PAUSED,
        JobStatus.PREEMPTED,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    },
    JobStatus.PAUSED: {JobStatus.RUNNING, JobStatus.FAILED},
    JobStatus.PREEMPTED: {JobStatus.RUNNING, JobStatus.FAILED},
    JobStatus.COMPLETED: set(),  # Terminal state
    JobStatus.FAILED: set(),  # Terminal state
}
