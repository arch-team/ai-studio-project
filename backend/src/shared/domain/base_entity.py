"""Base Entity - Foundation for all domain entities."""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeVar
from uuid import UUID, uuid4

from src.shared.utils import utc_now


@dataclass
class BaseEntity(ABC):
    """Abstract base class for all domain entities.

    Provides common fields for identity and auditing.
    """

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# Type variable for entity types
EntityT = TypeVar("EntityT", bound=BaseEntity)
