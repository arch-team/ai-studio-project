"""Domain Events - Event-driven communication between modules.

Domain events enable loose coupling between modules by allowing them
to communicate through events rather than direct dependencies.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, TypeVar
from uuid import UUID, uuid4

from src.shared.utils import utc_now


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=utc_now)


# Type variable for event types
EventT = TypeVar("EventT", bound=DomainEvent)

# Event handler type
EventHandler = Callable[[DomainEvent], Any]


class EventBus:
    """Simple in-process event bus for domain events."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    def subscribe(self, event_type: type[EventT], handler: Callable[[EventT], Any]) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)  # type: ignore

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribed handlers."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            handler(event)

    async def publish_async(self, event: DomainEvent) -> None:
        """Publish an event asynchronously to all subscribed handlers."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            result = handler(event)
            if hasattr(result, "__await__"):
                await result


# Global event bus instance
event_bus = EventBus()


def event_handler(event_type: type[EventT]) -> Callable[[Callable[[EventT], Any]], Callable[[EventT], Any]]:
    """Decorator to register an event handler."""

    def decorator(func: Callable[[EventT], Any]) -> Callable[[EventT], Any]:
        event_bus.subscribe(event_type, func)  # type: ignore
        return func

    return decorator
