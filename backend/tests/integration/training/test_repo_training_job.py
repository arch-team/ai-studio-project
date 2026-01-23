"""TrainingJob Repository Integration Tests - Database CRUD operations.

Tests the repository implementation using mocked database sessions.
These tests verify ORM mapping logic, query building, and data transformations.

Note: Full database integration tests require a running MySQL instance.
These tests use mocked sessions to test repository logic in isolation.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.training.domain.entities import TrainingJob
from src.modules.training.domain.value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
)
from src.modules.training.infrastructure.repositories import TrainingJobRepository
from src.shared.domain.exceptions import EntityNotFoundError


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session: AsyncMock) -> TrainingJobRepository:
    """Create repository instance with mock session."""
    return TrainingJobRepository(mock_session)


@pytest.fixture
def sample_training_job() -> TrainingJob:
    """Sample training job entity for testing."""
    return TrainingJob(
        id=1,
        job_name="test-bert-training",
        owner_id=1,
        image_uri="123456789.dkr.ecr.us-east-1.amazonaws.com/training:latest",
        instance_type="ml.g5.xlarge",
        entrypoint_command=["python", "train.py"],
        display_name="BERT Training Job",
        description="Test training job for BERT model",
        node_count=2,
        tasks_per_node=1,
        hyperparameters={"learning_rate": "1e-4", "batch_size": "32"},
        max_epochs=10,
        batch_size=32,
        learning_rate=Decimal("0.0001"),
        distribution_strategy=DistributionStrategy.DDP,
        mixed_precision=True,
        use_spot_instances=False,
        priority=JobPriority.MEDIUM,
        status=JobStatus.SUBMITTED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_training_job_model() -> MagicMock:
    """Create a mock ORM model for testing."""
    model = MagicMock()
    model.id = 1
    model.job_name = "test-bert-training"
    model.owner_id = 1
    model.image_uri = "123456789.dkr.ecr.us-east-1.amazonaws.com/training:latest"
    model.instance_type = "ml.g5.xlarge"
    model.entrypoint_command = ["python", "train.py"]
    model.display_name = "BERT Training Job"
    model.description = "Test training job for BERT model"
    model.node_count = 2
    model.tasks_per_node = 1
    model.hyperparameters = {"learning_rate": "1e-4", "batch_size": "32"}
    model.max_epochs = 10
    model.batch_size = 32
    model.learning_rate = Decimal("0.0001")
    model.environment_variables = None
    model.dataset_id = None
    model.data_mount_path = None
    model.checkpoint_mount_path = None
    model.checkpoint_interval = None
    model.auto_resume_checkpoint_id = None
    model.hyperpod_status = None
    model.kueue_workload_name = None
    model.kueue_status = None
    model.total_pods = None
    model.running_pods = 0
    model.failed_pods = 0
    model.preemption_count = 0
    model.current_epoch = None
    model.current_step = None
    model.latest_loss = None
    model.latest_accuracy = None
    model.submitted_at = None
    model.started_at = None
    model.completed_at = None
    model.duration_seconds = None
    model.total_gpu_hours = None
    model.estimated_cost_usd = None
    model.error_message = None
    model.failure_reason = None
    model.created_at = datetime.utcnow()
    model.updated_at = datetime.utcnow()

    # Mock enum values
    model.distribution_strategy = MagicMock()
    model.distribution_strategy.value = "DDP"
    model.priority = MagicMock()
    model.priority.value = "MEDIUM"
    model.status = MagicMock()
    model.status.value = "SUBMITTED"
    model.spot_interruption_behavior = None

    return model


# =============================================================================
# Get By ID Tests
# =============================================================================


class TestTrainingJobRepositoryGetById:
    """Tests for get_by_id operation."""

    async def test_get_by_id_returns_entity_when_found(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
        mock_training_job_model: MagicMock,
    ):
        """Test get_by_id returns entity when job exists."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_training_job_model
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.job_name == "test-bert-training"
        assert result.status == JobStatus.SUBMITTED
        mock_session.execute.assert_called_once()

    async def test_get_by_id_returns_none_when_not_found(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
    ):
        """Test get_by_id returns None when job doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_id(99999)

        # Assert
        assert result is None


# =============================================================================
# Get By Name Tests
# =============================================================================


class TestTrainingJobRepositoryGetByName:
    """Tests for get_by_name operation."""

    async def test_get_by_name_returns_entity_when_found(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
        mock_training_job_model: MagicMock,
    ):
        """Test get_by_name returns entity when job exists."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_training_job_model
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_name("test-bert-training")

        # Assert
        assert result is not None
        assert result.job_name == "test-bert-training"

    async def test_get_by_name_returns_none_when_not_found(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
    ):
        """Test get_by_name returns None when job doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_name("nonexistent-job")

        # Assert
        assert result is None


# =============================================================================
# Exists By Name Tests
# =============================================================================


class TestTrainingJobRepositoryExistsByName:
    """Tests for exists_by_name operation."""

    async def test_exists_by_name_returns_true_when_exists(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
    ):
        """Test exists_by_name returns True when job exists."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.exists_by_name("test-bert-training")

        # Assert
        assert result is True

    async def test_exists_by_name_returns_false_when_not_exists(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
    ):
        """Test exists_by_name returns False when job doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.exists_by_name("nonexistent-job")

        # Assert
        assert result is False


# =============================================================================
# List Jobs Tests
# =============================================================================


class TestTrainingJobRepositoryListJobs:
    """Tests for list_jobs operation."""

    async def test_list_jobs_returns_empty_list_when_no_jobs(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
    ):
        """Test list_jobs returns empty list when no jobs exist."""
        # Arrange
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # Act
        jobs, total = await repository.list_jobs()

        # Assert
        assert jobs == []
        assert total == 0

    async def test_list_jobs_returns_jobs_with_count(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
        mock_training_job_model: MagicMock,
    ):
        """Test list_jobs returns jobs and total count."""
        # Arrange
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [mock_training_job_model]

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # Act
        jobs, total = await repository.list_jobs()

        # Assert
        assert len(jobs) == 1
        assert total == 1
        assert jobs[0].job_name == "test-bert-training"

    async def test_list_jobs_applies_pagination(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
    ):
        """Test list_jobs applies pagination parameters."""
        # Arrange
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # Act
        jobs, total = await repository.list_jobs(page=2, page_size=10)

        # Assert
        assert total == 100
        # Verify execute was called (pagination is applied internally)
        assert mock_session.execute.call_count == 2


# =============================================================================
# Create Tests
# =============================================================================


class TestTrainingJobRepositoryCreate:
    """Tests for create operation."""

    async def test_create_adds_model_to_session(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
        sample_training_job: TrainingJob,
        mock_training_job_model: MagicMock,
    ):
        """Test create adds model to session and flushes."""
        # Arrange - mock the refresh to update the model with DB values
        async def mock_refresh(model):
            model.id = 1
            model.created_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()

        mock_session.refresh = mock_refresh

        # Act
        with patch(
            "src.modules.training.infrastructure.repositories.training_job_repository_impl.TrainingJobModel"
        ) as MockModel:
            MockModel.return_value = mock_training_job_model
            result = await repository.create(sample_training_job)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.job_name == "test-bert-training"


# =============================================================================
# Update Tests
# =============================================================================


class TestTrainingJobRepositoryUpdate:
    """Tests for update operation."""

    async def test_update_modifies_existing_job(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
        sample_training_job: TrainingJob,
        mock_training_job_model: MagicMock,
    ):
        """Test update modifies existing job."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_training_job_model
        mock_session.execute.return_value = mock_result

        # Modify the job
        sample_training_job.status = JobStatus.RUNNING
        sample_training_job.started_at = datetime.utcnow()

        # Act
        result = await repository.update(sample_training_job)

        # Assert
        mock_session.flush.assert_called_once()
        assert mock_training_job_model.status == JobStatus.RUNNING

    async def test_update_raises_error_when_not_found(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
        sample_training_job: TrainingJob,
    ):
        """Test update raises EntityNotFoundError when job doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        sample_training_job.id = 99999

        # Act & Assert
        with pytest.raises(EntityNotFoundError):
            await repository.update(sample_training_job)


# =============================================================================
# Soft Delete Tests
# =============================================================================


class TestTrainingJobRepositorySoftDelete:
    """Tests for soft_delete operation."""

    async def test_soft_delete_returns_true_when_deleted(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
        mock_training_job_model: MagicMock,
    ):
        """Test soft_delete returns True when job is deleted."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_training_job_model
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.soft_delete(1)

        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(mock_training_job_model)
        mock_session.flush.assert_called_once()

    async def test_soft_delete_returns_false_when_not_found(
        self,
        repository: TrainingJobRepository,
        mock_session: AsyncMock,
    ):
        """Test soft_delete returns False when job doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.soft_delete(99999)

        # Assert
        assert result is False
        mock_session.delete.assert_not_called()


# =============================================================================
# Entity Conversion Tests
# =============================================================================


class TestTrainingJobRepositoryEntityConversion:
    """Tests for entity conversion logic."""

    def test_to_entity_converts_all_fields(
        self,
        repository: TrainingJobRepository,
        mock_training_job_model: MagicMock,
    ):
        """Test _to_entity converts all fields correctly."""
        # Act
        entity = repository._to_entity(mock_training_job_model)

        # Assert
        assert entity.id == 1
        assert entity.job_name == "test-bert-training"
        assert entity.owner_id == 1
        assert entity.image_uri == "123456789.dkr.ecr.us-east-1.amazonaws.com/training:latest"
        assert entity.instance_type == "ml.g5.xlarge"
        assert entity.node_count == 2
        assert entity.distribution_strategy == DistributionStrategy.DDP
        assert entity.priority == JobPriority.MEDIUM
        assert entity.status == JobStatus.SUBMITTED

    def test_to_entity_handles_nullable_fields(
        self,
        repository: TrainingJobRepository,
        mock_training_job_model: MagicMock,
    ):
        """Test _to_entity handles nullable fields correctly."""
        # Arrange
        mock_training_job_model.description = None
        mock_training_job_model.hyperparameters = None
        mock_training_job_model.started_at = None

        # Act
        entity = repository._to_entity(mock_training_job_model)

        # Assert
        assert entity.description is None
        assert entity.hyperparameters is None
        assert entity.started_at is None
