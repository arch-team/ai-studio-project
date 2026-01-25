"""Shared Domain - Core domain abstractions and exceptions."""

from .base_entity import BaseEntity, EntityT
from .base_repository import IRepository, T
from .events import DomainEvent, EventBus, EventT, event_bus, event_handler
from .exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    ValidationError,
)
from .interfaces import IEntityExistenceChecker, IQuotaChecker
from .problem import Problem, problem

__all__ = [
    # Base classes
    "BaseEntity",
    "EntityT",
    "IRepository",
    "T",
    # Events
    "DomainEvent",
    "EventBus",
    "EventT",
    "event_bus",
    "event_handler",
    # Exceptions (new Problem-based)
    "Problem",
    "problem",
    # Exceptions (legacy - will be removed after migration)
    "DomainError",
    "EntityNotFoundError",
    "ValidationError",
    "DuplicateEntityError",
    "InvalidStateTransitionError",
    "ResourceQuotaExceededError",
    # Cross-module interfaces
    "IEntityExistenceChecker",
    "IQuotaChecker",
]
