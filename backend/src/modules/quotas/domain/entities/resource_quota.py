"""ResourceQuota domain entity - Resource allocation and limits for users/teams."""

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.utils import utc_now

from ..value_objects import QuotaStatus, QuotaType


@dataclass
class ResourceQuota:
    """Resource quota domain entity for managing resource allocation.

    Maps to Kueue ClusterQueue and ResourceFlavor resources.
    """

    id: int
    name: str
    quota_type: QuotaType = QuotaType.USER
    description: str | None = None

    # CPU quota (vCPU)
    max_cpu_cores: int = 0
    reserved_cpu_cores: int = 0

    # GPU quota
    max_gpu_count: int = 0
    reserved_gpu_count: int = 0
    gpu_types: list[str] = field(default_factory=list)

    # Memory quota (GB)
    max_memory_gb: int = 0
    reserved_memory_gb: int = 0

    # Storage quota (GB)
    max_storage_gb: int | None = None

    # Job limits
    max_concurrent_jobs: int = 5
    max_total_jobs: int | None = None

    # Spot instance limit
    max_spot_instances: int = 0

    # Status and validity
    status: QuotaStatus = QuotaStatus.ACTIVE
    valid_from: datetime = field(default_factory=utc_now)
    valid_until: datetime | None = None

    # Audit fields
    created_by: int | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def is_active(self) -> bool:
        """Check if quota is currently active and valid."""
        if self.status != QuotaStatus.ACTIVE:
            return False
        now = utc_now()
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True

    def is_expired(self) -> bool:
        """Check if quota has expired."""
        if self.valid_until is None:
            return False
        return utc_now() > self.valid_until

    def can_allocate_gpu(self, requested: int) -> bool:
        """Check if GPU allocation is within quota limits."""
        return requested <= self.max_gpu_count

    def can_allocate_cpu(self, requested: int) -> bool:
        """Check if CPU allocation is within quota limits."""
        return requested <= self.max_cpu_cores

    def can_allocate_memory(self, requested_gb: int) -> bool:
        """Check if memory allocation is within quota limits."""
        return requested_gb <= self.max_memory_gb

    def can_allocate_storage(self, requested_gb: int) -> bool:
        """Check if storage allocation is within quota limits."""
        if self.max_storage_gb is None:
            return True
        return requested_gb <= self.max_storage_gb

    def is_gpu_type_allowed(self, gpu_type: str) -> bool:
        """Check if GPU type is allowed by quota."""
        if not self.gpu_types:
            return True  # No restrictions
        return gpu_type in self.gpu_types

    def validate_job_submission(
        self,
        cpu_cores: int,
        gpu_count: int,
        memory_gb: int,
        current_running_jobs: int,
        gpu_type: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validate if a new job can be submitted within quota limits.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_active():
            return False, "Quota is not active"

        if not self.can_allocate_cpu(cpu_cores):
            return False, f"CPU request {cpu_cores} exceeds quota {self.max_cpu_cores}"

        if not self.can_allocate_gpu(gpu_count):
            return False, f"GPU request {gpu_count} exceeds quota {self.max_gpu_count}"

        if not self.can_allocate_memory(memory_gb):
            return (
                False,
                f"Memory request {memory_gb}GB exceeds quota {self.max_memory_gb}GB",
            )

        if gpu_type and not self.is_gpu_type_allowed(gpu_type):
            return False, f"GPU type {gpu_type} not allowed. Allowed: {self.gpu_types}"

        if current_running_jobs >= self.max_concurrent_jobs:
            return False, f"Concurrent job limit {self.max_concurrent_jobs} reached"

        return True, None

    def suspend(self) -> None:
        """Suspend quota."""
        self.status = QuotaStatus.SUSPENDED
        self.updated_at = utc_now()

    def activate(self) -> None:
        """Activate quota."""
        self.status = QuotaStatus.ACTIVE
        self.updated_at = utc_now()
