"""PodStatistics value object - Pod health and status metrics."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class PodStatistics:
    """Value object representing pod statistics for a training job.

    Immutable object that encapsulates pod health information.
    """

    total_pods: int | None = None
    running_pods: int = 0
    failed_pods: int = 0
    preemption_count: int = 0

    def healthy_ratio(self) -> float:
        """Calculate the ratio of running pods to total pods."""
        if self.total_pods is None or self.total_pods == 0:
            return 0.0
        return self.running_pods / self.total_pods

    def has_failures(self) -> bool:
        """Check if there are any failed pods."""
        return self.failed_pods > 0

    def was_preempted(self) -> bool:
        """Check if job has been preempted."""
        return self.preemption_count > 0

    def increment_preemption(self) -> "PodStatistics":
        """Return new instance with incremented preemption count."""
        return replace(self, preemption_count=self.preemption_count + 1)
