"""Training module test fixtures."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.modules.training.domain.entities.training_job import TrainingJob
from src.modules.training.domain.value_objects import JobStatus, DistributionStrategy


@pytest.fixture
def sample_training_job() -> TrainingJob:
    """Create a sample TrainingJob entity for testing."""
    return TrainingJob(
        id=1,
        name="test-training-job",
        owner_id=1,
        status=JobStatus.SUBMITTED,
        distribution_strategy=DistributionStrategy.DDP,
        gpu_count=4,
        instance_type="ml.p4d.24xlarge",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def running_training_job(sample_training_job: TrainingJob) -> TrainingJob:
    """Create a running TrainingJob entity for testing."""
    job = sample_training_job
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(UTC)
    return job


@pytest.fixture
def mock_training_job_repository() -> AsyncMock:
    """Mock ITrainingJobRepository for testing training services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_owner = AsyncMock(return_value=[])
    repo.get_by_status = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_checkpoint_repository() -> AsyncMock:
    """Mock ICheckpointRepository for testing checkpoint services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_job_id = AsyncMock(return_value=[])
    repo.get_latest_by_job_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_hyperpod_client() -> AsyncMock:
    """Mock HyperPodClient for testing training services."""
    client = AsyncMock()
    client.submit_job = AsyncMock()
    client.get_job_status = AsyncMock()
    client.cancel_job = AsyncMock()
    client.list_jobs = AsyncMock(return_value=[])
    return client
