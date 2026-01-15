"""Domain Exceptions - Business rule violation errors.

Domain exceptions represent violations of business rules:
- EntityNotFoundError: Requested entity does not exist
- ValidationError: Business validation failed
- DuplicateEntityError: Entity already exists
- InvalidStateTransitionError: Invalid state change attempted
- ResourceQuotaExceededError: Resource limits exceeded
"""


class DomainError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(DomainError):
    """Raised when a requested entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(f"{entity_type} with id '{entity_id}' not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class ValidationError(DomainError):
    """Raised when business validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class DuplicateEntityError(DomainError):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, identifier: str):
        super().__init__(f"{entity_type} with identifier '{identifier}' already exists")
        self.entity_type = entity_type
        self.identifier = identifier


class InvalidStateTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, entity_type: str, current_state: str, target_state: str):
        super().__init__(
            f"Cannot transition {entity_type} from '{current_state}' to '{target_state}'"
        )
        self.entity_type = entity_type
        self.current_state = current_state
        self.target_state = target_state


class ResourceQuotaExceededError(DomainError):
    """Raised when resource quota is exceeded."""

    def __init__(self, resource_type: str, limit: int, requested: int):
        super().__init__(
            f"{resource_type} quota exceeded: limit={limit}, requested={requested}"
        )
        self.resource_type = resource_type
        self.limit = limit
        self.requested = requested
