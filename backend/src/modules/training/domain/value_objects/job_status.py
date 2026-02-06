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


class JobStateTransition:
    """任务状态转换策略辅助类。"""

    TERMINAL_STATES = {JobStatus.COMPLETED, JobStatus.FAILED}
    RUNNING_STATES = {JobStatus.RUNNING, JobStatus.SUBMITTED}

    @classmethod
    def can_transition(cls, from_status: JobStatus, to_status: JobStatus) -> bool:
        """检查状态转换是否有效。

        Args:
            from_status: 当前状态
            to_status: 目标状态

        Returns:
            bool: 转换是否有效
        """
        return to_status in TRAINING_JOB_STATE_TRANSITIONS.get(from_status, set())

    @classmethod
    def is_terminal(cls, status: JobStatus) -> bool:
        """检查是否为终止状态。

        Args:
            status: 任务状态

        Returns:
            bool: 是否为终止状态
        """
        return status in cls.TERMINAL_STATES

    @classmethod
    def is_running(cls, status: JobStatus) -> bool:
        """检查是否为运行相关状态。

        Args:
            status: 任务状态

        Returns:
            bool: 是否为运行中或已提交状态
        """
        return status in cls.RUNNING_STATES

    @classmethod
    def get_valid_transitions(cls, status: JobStatus) -> set[JobStatus]:
        """获取某状态的所有有效转换。

        Args:
            status: 当前状态

        Returns:
            set[JobStatus]: 可转换到的状态集合
        """
        return TRAINING_JOB_STATE_TRANSITIONS.get(status, set())
