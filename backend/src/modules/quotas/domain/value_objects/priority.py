"""Priority value object."""

from enum import Enum


class PriorityDefault(Enum):
    """Default priority levels for training jobs."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def to_kueue_priority(self) -> int:
        """Convert to Kueue priority class value."""
        mapping = {
            PriorityDefault.HIGH: 1000,
            PriorityDefault.MEDIUM: 500,
            PriorityDefault.LOW: 100,
        }
        return mapping[self]
