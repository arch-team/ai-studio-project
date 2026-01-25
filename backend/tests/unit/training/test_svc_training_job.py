"""Training Job Service Unit Tests - TDD Red-Green-Refactor."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.training.domain.entities.training_job import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
    TrainingJob,
)
from src.modules.training.domain.exceptions import TrainingJobNotFoundError
from src.shared.domain.exceptions import (
    DuplicateEntityError,
    InvalidStateTransitionError,
)

# === Fixtures ===


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock training job repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_name = AsyncMock(return_value=None)
    repo.exists_by_name = AsyncMock(return_value=False)
    repo.list_jobs = AsyncMock(return_value=([], 0))
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_hyperpod_client() -> AsyncMock:
    """Mock HyperPod SDK client."""
    client = AsyncMock()
    client.submit_training_job = AsyncMock(
        return_value={
            "job_name": "test-job",
            "status": "submitted",
            "cluster_name": "test-cluster",
        }
    )
    client.get_training_job_status = AsyncMock(
        return_value={
            "job_name": "test-job",
            "status": "running",
            "start_time": datetime.utcnow(),
        }
    )
    client.stop_training_job = AsyncMock(return_value={"job_name": "test-job", "status": "stopped"})
    return client


@pytest.fixture
def sample_job() -> TrainingJob:
    """Sample training job entity."""
    return TrainingJob(
        id=1,
        job_name="test-job-001",
        owner_id=100,
        image_uri="123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
        instance_type="ml.p4d.24xlarge",
        entrypoint_command=["torchrun", "--nproc_per_node=8", "train.py"],
        display_name="Test Training Job",
        node_count=2,
        tasks_per_node=8,
        distribution_strategy=DistributionStrategy.DDP,
        priority=JobPriority.MEDIUM,
        status=JobStatus.SUBMITTED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def running_job(sample_job: TrainingJob) -> TrainingJob:
    """Running training job."""
    sample_job.status = JobStatus.RUNNING
    sample_job.started_at = datetime.utcnow()
    return sample_job


@pytest.fixture
def paused_job(sample_job: TrainingJob) -> TrainingJob:
    """Paused training job."""
    sample_job.status = JobStatus.PAUSED
    return sample_job


@pytest.fixture
def completed_job(sample_job: TrainingJob) -> TrainingJob:
    """Completed training job."""
    sample_job.status = JobStatus.COMPLETED
    sample_job.completed_at = datetime.utcnow()
    return sample_job


@pytest.fixture
def create_job_data() -> dict:
    """Data for creating a training job."""
    return {
        "job_name": "new-training-job",
        "image_uri": "123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
        "instance_type": "ml.p4d.24xlarge",
        "node_count": 2,
        "tasks_per_node": 8,
        "entrypoint_command": ["torchrun", "--nproc_per_node=8", "train.py"],
        "distribution_strategy": "DDP",
        "priority": "MEDIUM",
    }


# === Import service after defining fixtures ===
# The service import is deferred to allow tests to run even before implementation


def get_service(mock_repository: AsyncMock, mock_hyperpod_client: AsyncMock):
    """Create TrainingJobService with mocked dependencies."""
    from src.modules.training.application.services.training_job_service import TrainingJobService

    return TrainingJobService(
        repository=mock_repository,
        hyperpod_client=mock_hyperpod_client,
    )


# === Test Classes ===


class TestCreateTrainingJob:
    """Tests for create_job method."""

    @pytest.mark.asyncio
    async def test_create_job_success(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        create_job_data: dict,
        sample_job: TrainingJob,
    ):
        """Test successful job creation."""
        # Arrange
        mock_repository.exists_by_name.return_value = False
        mock_repository.create.return_value = sample_job
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        result = await service.create_job(owner_id=100, data=create_job_data)

        # Assert
        assert result is not None
        assert result.job_name == sample_job.job_name
        mock_repository.exists_by_name.assert_called_once_with(create_job_data["job_name"])
        mock_repository.create.assert_called_once()
        mock_hyperpod_client.submit_training_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_job_name_already_exists(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        create_job_data: dict,
    ):
        """Test create fails when job name already exists."""
        # Arrange
        mock_repository.exists_by_name.return_value = True
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act & Assert
        with pytest.raises(DuplicateEntityError) as exc_info:
            await service.create_job(owner_id=100, data=create_job_data)

        assert "already exists" in str(exc_info.value)
        mock_repository.create.assert_not_called()
        mock_hyperpod_client.submit_training_job.assert_not_called()


class TestGetTrainingJob:
    """Tests for get_job method."""

    @pytest.mark.asyncio
    async def test_get_job_success(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        sample_job: TrainingJob,
    ):
        """Test get job by ID."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_job
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        result = await service.get_job(job_id=1)

        # Assert
        assert result is not None
        assert result.id == sample_job.id
        mock_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_job_not_found(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ):
        """Test get job raises error when not found."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act & Assert
        with pytest.raises(TrainingJobNotFoundError) as exc_info:
            await service.get_job(job_id=999)

        assert "not found" in str(exc_info.value)


class TestListTrainingJobs:
    """Tests for list_jobs method."""

    @pytest.mark.asyncio
    async def test_list_jobs_with_pagination(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        sample_job: TrainingJob,
    ):
        """Test list jobs with pagination."""
        # Arrange
        mock_repository.list_jobs.return_value = ([sample_job], 1)
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        jobs, total = await service.list_jobs(page=1, page_size=20)

        # Assert
        assert len(jobs) == 1
        assert total == 1
        mock_repository.list_jobs.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_jobs_filter_by_owner(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        sample_job: TrainingJob,
    ):
        """Test list jobs filtered by owner ID."""
        # Arrange
        mock_repository.list_jobs.return_value = ([sample_job], 1)
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        jobs, total = await service.list_jobs(owner_id=100)

        # Assert
        mock_repository.list_jobs.assert_called_once()
        call_kwargs = mock_repository.list_jobs.call_args.kwargs
        assert call_kwargs.get("owner_id") == 100


class TestPauseJob:
    """Tests for pause_job method."""

    @pytest.mark.asyncio
    async def test_pause_running_job_success(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        running_job: TrainingJob,
    ):
        """Test pause running job."""
        # Arrange
        mock_repository.get_by_id.return_value = running_job
        paused_result = TrainingJob(**vars(running_job))
        paused_result.status = JobStatus.PAUSED
        mock_repository.update.return_value = paused_result
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        result = await service.pause_job(job_id=1)

        # Assert
        assert result.status == JobStatus.PAUSED
        mock_hyperpod_client.stop_training_job.assert_called_once()
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_non_running_job_fails(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        sample_job: TrainingJob,
    ):
        """Test pause fails when job is not running."""
        # Arrange - job is in SUBMITTED status
        mock_repository.get_by_id.return_value = sample_job
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.pause_job(job_id=1)

        mock_hyperpod_client.stop_training_job.assert_not_called()


class TestResumeJob:
    """Tests for resume_job method."""

    @pytest.mark.asyncio
    async def test_resume_paused_job_success(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        paused_job: TrainingJob,
    ):
        """Test resume paused job."""
        # Arrange
        mock_repository.get_by_id.return_value = paused_job
        resumed_result = TrainingJob(**vars(paused_job))
        resumed_result.status = JobStatus.RUNNING
        mock_repository.update.return_value = resumed_result
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        result = await service.resume_job(job_id=1)

        # Assert
        assert result.status == JobStatus.RUNNING
        mock_hyperpod_client.submit_training_job.assert_called_once()
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_running_job_fails(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        running_job: TrainingJob,
    ):
        """Test resume fails when job is already running."""
        # Arrange
        mock_repository.get_by_id.return_value = running_job
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.resume_job(job_id=1)


class TestCancelJob:
    """Tests for cancel_job method."""

    @pytest.mark.asyncio
    async def test_cancel_running_job_success(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        running_job: TrainingJob,
    ):
        """Test cancel running job."""
        # Arrange
        mock_repository.get_by_id.return_value = running_job
        cancelled_result = TrainingJob(**vars(running_job))
        cancelled_result.status = JobStatus.FAILED
        cancelled_result.failure_reason = "CANCELLED_BY_USER"
        mock_repository.update.return_value = cancelled_result
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        result = await service.cancel_job(job_id=1)

        # Assert
        assert result.status == JobStatus.FAILED
        assert result.failure_reason == "CANCELLED_BY_USER"
        mock_hyperpod_client.stop_training_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_completed_job_fails(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        completed_job: TrainingJob,
    ):
        """Test cancel fails when job is already completed."""
        # Arrange
        mock_repository.get_by_id.return_value = completed_job
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.cancel_job(job_id=1)


class TestDeleteJob:
    """Tests for delete_job method."""

    @pytest.mark.asyncio
    async def test_delete_job_success(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        sample_job: TrainingJob,
    ):
        """Test soft delete job."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_job
        mock_repository.soft_delete.return_value = True
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        await service.delete_job(job_id=1)

        # Assert
        mock_repository.soft_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_running_job_cancels_first(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
        running_job: TrainingJob,
    ):
        """Test deleting running job cancels it first."""
        # Arrange
        mock_repository.get_by_id.return_value = running_job
        cancelled_job = TrainingJob(**vars(running_job))
        cancelled_job.status = JobStatus.FAILED
        mock_repository.update.return_value = cancelled_job
        mock_repository.soft_delete.return_value = True
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act
        await service.delete_job(job_id=1)

        # Assert
        mock_hyperpod_client.stop_training_job.assert_called_once()
        mock_repository.soft_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_job_not_found(
        self,
        mock_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ):
        """Test delete non-existent job raises error."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        service = get_service(mock_repository, mock_hyperpod_client)

        # Act & Assert
        with pytest.raises(TrainingJobNotFoundError):
            await service.delete_job(job_id=999)
