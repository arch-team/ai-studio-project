"""Space module domain exceptions."""

from src.shared.domain.exceptions import DomainError


class SpaceError(DomainError):
    """Base exception for space-related errors."""


class SpaceNotFoundError(SpaceError):
    """Space not found exception."""

    def __init__(self, space_id: str):
        super().__init__(f"Space not found: {space_id}")
        self.space_id = space_id


class DuplicateSpaceNameError(SpaceError):
    """Space name already exists for owner exception."""

    def __init__(self, space_name: str, owner_id: int):
        super().__init__(f"Space name already exists: {space_name} for owner {owner_id}")
        self.space_name = space_name
        self.owner_id = owner_id


class InvalidSpaceStateError(SpaceError):
    """Invalid space state for operation exception."""

    def __init__(self, space_id: str, current_state: str, operation: str):
        super().__init__(
            f"Cannot {operation} space {space_id} in {current_state} state"
        )
        self.space_id = space_id
        self.current_state = current_state
        self.operation = operation


class SpaceQuotaExceededError(SpaceError):
    """Space resource quota exceeded exception."""

    def __init__(self, resource: str, required: int, available: int):
        super().__init__(
            f"Insufficient {resource}: need {required}, have {available}"
        )
        self.resource = resource
        self.required = required
        self.available = available
