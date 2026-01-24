"""Training domain exceptions."""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class TrainingError(DomainError):
    """Base exception for training-related errors."""


class TrainingJobNotFoundError(EntityNotFoundError):
    """Raised when a training job is not found."""

    def __init__(self, identifier: str):
        super().__init__("TrainingJob", identifier)
        self.identifier = identifier


class CheckpointNotFoundError(EntityNotFoundError):
    """Raised when a checkpoint is not found."""

    def __init__(self, identifier: str):
        super().__init__("Checkpoint", identifier)
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


class CheckpointStorageError(TrainingError):
    """Raised when checkpoint storage operation fails."""

    def __init__(self, message: str, job_id: int | None = None):
        super().__init__(message)
        self.job_id = job_id


class CheckpointMigrationError(TrainingError):
    """Raised when checkpoint migration fails."""

    def __init__(self, checkpoint_id: int, source_tier: str, target_tier: str, reason: str):
        super().__init__(
            f"Failed to migrate checkpoint {checkpoint_id} from {source_tier} to {target_tier}: {reason}"
        )
        self.checkpoint_id = checkpoint_id
        self.source_tier = source_tier
        self.target_tier = target_tier
        self.reason = reason


class JobTemplateNotFoundError(EntityNotFoundError):
    """Raised when a job template is not found."""

    def __init__(self, identifier: int):
        super().__init__("JobTemplate", str(identifier))
        self.identifier = identifier


class JobTemplatePermissionDeniedError(TrainingError):
    """Raised when user doesn't have permission for the template operation."""

    def __init__(self, operation: str, template_id: int):
        super().__init__(
            f"Permission denied: cannot {operation} template {template_id}"
        )
        self.operation = operation
        self.template_id = template_id
