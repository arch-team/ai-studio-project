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
from .pydantic_entity import PydanticEntity

__all__ = [
    # Base classes
    "BaseEntity",
    "EntityT",
    "PydanticEntity",
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
    # Exceptions (向后兼容)
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
