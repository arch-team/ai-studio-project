"""Quotas domain exceptions."""

from src.shared.domain.exceptions import DomainError


class QuotaError(DomainError):
    """Base exception for quota-related errors."""


class QuotaNotFoundError(QuotaError):
    """Raised when a quota is not found."""

    def __init__(self, identifier: str):
        super().__init__(f"Quota not found: {identifier}")
        self.identifier = identifier


class QuotaExceededError(QuotaError):
    """Raised when resource quota is exceeded."""

    def __init__(self, resource: str, requested: int, limit: int):
        super().__init__(
            f"{resource} quota exceeded: requested {requested}, limit {limit}"
        )
        self.resource = resource
        self.requested = requested
        self.limit = limit


class DuplicateConfigError(QuotaError):
    """Raised when config with same role+project already exists."""

    def __init__(self, role: str, scope: str):
        super().__init__(
            f"Config already exists for role={role}, scope={scope}"
        )
        self.role = role
        self.scope = scope
