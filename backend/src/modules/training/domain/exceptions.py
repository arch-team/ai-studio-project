"""Training domain exceptions."""

from src.shared.domain.exceptions import DomainError


class TrainingError(DomainError):
    """Base exception for training-related errors."""


class TrainingJobNotFoundError(TrainingError):
    """Raised when a training job is not found."""

    def __init__(self, identifier: str):
        super().__init__(f"Training job not found: {identifier}")
        self.identifier = identifier


class CheckpointNotFoundError(TrainingError):
    """Raised when a checkpoint is not found."""

    def __init__(self, identifier: str):
        super().__init__(f"Checkpoint not found: {identifier}")
        self.identifier = identifier


class DuplicateJobNameError(TrainingError):
    """Raised when a job with the same name already exists."""

    def __init__(self, job_name: str):
        super().__init__(f"Training job with name '{job_name}' already exists")
        self.job_name = job_name


class InvalidJobStateError(TrainingError):
    """Raised when job is in an invalid state for the requested operation."""

    def __init__(self, job_id: int, current_state: str, operation: str):
        super().__init__(
            f"Cannot {operation} job {job_id} in state {current_state}"
        )
        self.job_id = job_id
        self.current_state = current_state
        self.operation = operation
