"""Training Job Repository Interface - Data access contract for training jobs."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.training_job import JobPriority, JobStatus, TrainingJob


class ITrainingJobRepository(ABC):
    """Abstract repository interface for TrainingJob entity."""

    @abstractmethod
    async def get_by_id(self, job_id: int) -> TrainingJob | None:
        """Get training job by ID."""

    @abstractmethod
    async def get_by_name(self, job_name: str) -> TrainingJob | None:
        """Get training job by unique name."""

    @abstractmethod
    async def list_jobs(
        self,
        owner_id: int | None = None,
        status: JobStatus | None = None,
        priority: JobPriority | None = None,
        submitted_after: datetime | None = None,
        submitted_before: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[TrainingJob], int]:
        """List training jobs with pagination and filters.

        Returns:
            tuple of (list of training jobs, total count)
        """

    @abstractmethod
    async def create(self, job: TrainingJob) -> TrainingJob:
        """Create a new training job."""

    @abstractmethod
    async def update(self, job: TrainingJob) -> TrainingJob:
        """Update an existing training job."""

    @abstractmethod
    async def soft_delete(self, job_id: int) -> bool:
        """Soft delete a training job.

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def exists_by_name(self, job_name: str) -> bool:
        """Check if a job with the given name exists."""
