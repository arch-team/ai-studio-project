"""Model module domain exceptions."""

from src.shared.domain.exceptions import DomainError


class ModelError(DomainError):
    """Base exception for model-related errors."""


class ModelNotFoundError(ModelError):
    """Model not found exception."""

    def __init__(self, model_id: int | str):
        super().__init__(f"Model not found: {model_id}")
        self.model_id = model_id


class DuplicateModelVersionError(ModelError):
    """Model version already exists exception."""

    def __init__(self, model_name: str, version: str):
        super().__init__(f"Model version already exists: {model_name} {version}")
        self.model_name = model_name
        self.version = version


class InvalidModelStateError(ModelError):
    """Invalid model state for operation exception."""

    def __init__(self, model_id: int, current_state: str, operation: str):
        super().__init__(
            f"Cannot {operation} model {model_id} in {current_state} state"
        )
        self.model_id = model_id
        self.current_state = current_state
        self.operation = operation
