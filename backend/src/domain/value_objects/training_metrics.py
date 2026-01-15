"""TrainingMetrics value object - Training progress and metrics."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TrainingMetrics:
    """Value object representing training progress metrics.

    Immutable object that encapsulates training progress information.
    """

    current_epoch: int | None = None
    current_step: int | None = None
    latest_loss: Decimal | None = None
    latest_accuracy: Decimal | None = None

    def has_progress(self) -> bool:
        """Check if any training progress has been made."""
        return self.current_epoch is not None or self.current_step is not None

    def is_improving(self, previous: "TrainingMetrics") -> bool:
        """Check if metrics show improvement over previous metrics.

        Improvement is determined by lower loss value.
        """
        if self.latest_loss is None or previous.latest_loss is None:
            return False
        return self.latest_loss < previous.latest_loss
