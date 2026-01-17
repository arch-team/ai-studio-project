"""Unit tests for TrainingJob domain entity.

Tests cover:
- Enum types validation
- State machine transitions
- Business rules
- Entity creation
"""


import pytest

from src.modules.training.domain.entities.training_job import (
    TRAINING_JOB_STATE_TRANSITIONS,
    DistributionStrategy,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
    TrainingJob,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


class TestJobStatusEnum:
    """Tests for JobStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all required statuses are defined."""
        expected_statuses = {
            "SUBMITTED",
            "RUNNING",
            "PAUSED",
            "PREEMPTED",
            "COMPLETED",
            "FAILED",
        }
        actual_statuses = {s.name for s in JobStatus}
        assert actual_statuses == expected_statuses

    def test_status_values_match_database(self) -> None:
        """Verify enum values match database enum values."""
        assert JobStatus.SUBMITTED.value == "SUBMITTED"
        assert JobStatus.RUNNING.value == "RUNNING"
        assert JobStatus.PAUSED.value == "PAUSED"
        assert JobStatus.PREEMPTED.value == "PREEMPTED"
        assert JobStatus.COMPLETED.value == "COMPLETED"
        assert JobStatus.FAILED.value == "FAILED"


class TestDistributionStrategyEnum:
    """Tests for DistributionStrategy enum."""

    def test_all_strategies_defined(self) -> None:
        """Verify all required strategies are defined."""
        expected = {"DDP", "FSDP", "DEEPSPEED", "HOROVOD"}
        actual = {s.name for s in DistributionStrategy}
        assert actual == expected


class TestJobPriorityEnum:
    """Tests for JobPriority enum."""

    def test_all_priorities_defined(self) -> None:
        """Verify all required priorities are defined."""
        expected = {"HIGH", "MEDIUM", "LOW"}
        actual = {p.name for p in JobPriority}
        assert actual == expected


class TestSpotInterruptionBehaviorEnum:
    """Tests for SpotInterruptionBehavior enum."""

    def test_all_behaviors_defined(self) -> None:
        """Verify all required behaviors are defined."""
        expected = {"STOP", "TERMINATE", "HIBERNATE"}
        actual = {b.name for b in SpotInterruptionBehavior}
        assert actual == expected


class TestTrainingJobStateTransitions:
    """Tests for TrainingJob state machine transitions."""

    @pytest.fixture
    def job(self) -> TrainingJob:
        """Create a basic training job for testing."""
        return TrainingJob(
            id=1,
            job_name="test-job-001",
            owner_id=1,
            image_uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/training:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )

    def test_submitted_to_running_valid(self, job: TrainingJob) -> None:
        """Test valid transition: SUBMITTED -> RUNNING."""
        assert job.status == JobStatus.SUBMITTED
        assert job.can_transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING

    def test_submitted_to_failed_valid(self, job: TrainingJob) -> None:
        """Test valid transition: SUBMITTED -> FAILED."""
        assert job.can_transition_to(JobStatus.FAILED)
        job.transition_to(JobStatus.FAILED)
        assert job.status == JobStatus.FAILED

    def test_running_to_paused_valid(self, job: TrainingJob) -> None:
        """Test valid transition: RUNNING -> PAUSED."""
        job.transition_to(JobStatus.RUNNING)
        assert job.can_transition_to(JobStatus.PAUSED)
        job.transition_to(JobStatus.PAUSED)
        assert job.status == JobStatus.PAUSED

    def test_running_to_preempted_valid(self, job: TrainingJob) -> None:
        """Test valid transition: RUNNING -> PREEMPTED."""
        job.transition_to(JobStatus.RUNNING)
        assert job.can_transition_to(JobStatus.PREEMPTED)
        job.transition_to(JobStatus.PREEMPTED)
        assert job.status == JobStatus.PREEMPTED

    def test_running_to_completed_valid(self, job: TrainingJob) -> None:
        """Test valid transition: RUNNING -> COMPLETED."""
        job.transition_to(JobStatus.RUNNING)
        assert job.can_transition_to(JobStatus.COMPLETED)
        job.transition_to(JobStatus.COMPLETED)
        assert job.status == JobStatus.COMPLETED

    def test_running_to_failed_valid(self, job: TrainingJob) -> None:
        """Test valid transition: RUNNING -> FAILED."""
        job.transition_to(JobStatus.RUNNING)
        assert job.can_transition_to(JobStatus.FAILED)
        job.transition_to(JobStatus.FAILED)
        assert job.status == JobStatus.FAILED

    def test_paused_to_running_valid(self, job: TrainingJob) -> None:
        """Test valid transition: PAUSED -> RUNNING (resume)."""
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.PAUSED)
        assert job.can_transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING

    def test_preempted_to_running_valid(self, job: TrainingJob) -> None:
        """Test valid transition: PREEMPTED -> RUNNING (auto-resume)."""
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.PREEMPTED)
        assert job.can_transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING

    def test_completed_is_terminal(self, job: TrainingJob) -> None:
        """Test that COMPLETED is a terminal state."""
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.COMPLETED)
        assert job.is_terminal()
        assert not job.can_transition_to(JobStatus.RUNNING)
        assert not job.can_transition_to(JobStatus.PAUSED)
        assert not job.can_transition_to(JobStatus.FAILED)

    def test_failed_is_terminal(self, job: TrainingJob) -> None:
        """Test that FAILED is a terminal state."""
        job.transition_to(JobStatus.FAILED)
        assert job.is_terminal()
        assert not job.can_transition_to(JobStatus.RUNNING)
        assert not job.can_transition_to(JobStatus.SUBMITTED)

    def test_invalid_transition_submitted_to_completed(self, job: TrainingJob) -> None:
        """Test invalid transition: SUBMITTED -> COMPLETED."""
        assert not job.can_transition_to(JobStatus.COMPLETED)
        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.COMPLETED)

    def test_invalid_transition_raises_domain_exception(self, job: TrainingJob) -> None:
        """Test that invalid transitions raise InvalidStateTransitionError."""
        assert not job.can_transition_to(JobStatus.PAUSED)
        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.PAUSED)


class TestTrainingJobBusinessRules:
    """Tests for TrainingJob business rules."""

    @pytest.fixture
    def job(self) -> TrainingJob:
        """Create a basic training job for testing."""
        return TrainingJob(
            id=1,
            job_name="test-job-001",
            owner_id=1,
            image_uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/training:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )

    def test_is_running(self, job: TrainingJob) -> None:
        """Test is_running() method."""
        assert not job.is_running()
        job.transition_to(JobStatus.RUNNING)
        assert job.is_running()
        job.transition_to(JobStatus.PAUSED)
        assert not job.is_running()

    def test_is_terminal_completed(self, job: TrainingJob) -> None:
        """Test is_terminal() for COMPLETED status."""
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.COMPLETED)
        assert job.is_terminal()

    def test_is_terminal_failed(self, job: TrainingJob) -> None:
        """Test is_terminal() for FAILED status."""
        job.transition_to(JobStatus.FAILED)
        assert job.is_terminal()

    def test_can_pause_when_running(self, job: TrainingJob) -> None:
        """Test can_pause() returns True when RUNNING."""
        job.transition_to(JobStatus.RUNNING)
        assert job.can_pause()

    def test_cannot_pause_when_paused(self, job: TrainingJob) -> None:
        """Test can_pause() returns False when already PAUSED."""
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.PAUSED)
        assert not job.can_pause()

    def test_cannot_pause_when_submitted(self, job: TrainingJob) -> None:
        """Test can_pause() returns False when SUBMITTED."""
        assert not job.can_pause()

    def test_can_resume_when_paused(self, job: TrainingJob) -> None:
        """Test can_resume() returns True when PAUSED."""
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.PAUSED)
        assert job.can_resume()

    def test_can_resume_when_preempted(self, job: TrainingJob) -> None:
        """Test can_resume() returns True when PREEMPTED."""
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.PREEMPTED)
        assert job.can_resume()

    def test_cannot_resume_when_running(self, job: TrainingJob) -> None:
        """Test can_resume() returns False when already RUNNING."""
        job.transition_to(JobStatus.RUNNING)
        assert not job.can_resume()

    def test_increment_preemption_count(self, job: TrainingJob) -> None:
        """Test preemption count increment on PREEMPTED transition."""
        assert job.preemption_count == 0
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.PREEMPTED)
        assert job.preemption_count == 1
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.PREEMPTED)
        assert job.preemption_count == 2


class TestTrainingJobCreation:
    """Tests for TrainingJob entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating job with only required fields."""
        job = TrainingJob(
            id=1,
            job_name="test-job",
            owner_id=1,
            image_uri="test-image:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )
        assert job.id == 1
        assert job.job_name == "test-job"
        assert job.owner_id == 1
        assert job.image_uri == "test-image:latest"
        assert job.instance_type == "ml.p4d.24xlarge"
        assert job.entrypoint_command == ["python", "train.py"]

    def test_default_status_is_submitted(self) -> None:
        """Test default status is SUBMITTED."""
        job = TrainingJob(
            id=1,
            job_name="test-job",
            owner_id=1,
            image_uri="test-image:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )
        assert job.status == JobStatus.SUBMITTED

    def test_default_priority_is_medium(self) -> None:
        """Test default priority is MEDIUM."""
        job = TrainingJob(
            id=1,
            job_name="test-job",
            owner_id=1,
            image_uri="test-image:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )
        assert job.priority == JobPriority.MEDIUM

    def test_default_distribution_strategy_is_ddp(self) -> None:
        """Test default distribution strategy is DDP."""
        job = TrainingJob(
            id=1,
            job_name="test-job",
            owner_id=1,
            image_uri="test-image:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )
        assert job.distribution_strategy == DistributionStrategy.DDP

    def test_default_node_count_is_one(self) -> None:
        """Test default node_count is 1."""
        job = TrainingJob(
            id=1,
            job_name="test-job",
            owner_id=1,
            image_uri="test-image:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )
        assert job.node_count == 1

    def test_default_preemption_count_is_zero(self) -> None:
        """Test default preemption_count is 0."""
        job = TrainingJob(
            id=1,
            job_name="test-job",
            owner_id=1,
            image_uri="test-image:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
        )
        assert job.preemption_count == 0

    def test_create_with_all_optional_fields(self) -> None:
        """Test creating job with all fields."""
        job = TrainingJob(
            id=1,
            job_name="test-job",
            owner_id=1,
            image_uri="test-image:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command=["python", "train.py"],
            display_name="Test Training Job",
            description="A test job",
            node_count=4,
            tasks_per_node=8,
            hyperparameters={"lr": 0.001, "epochs": 100},
            max_epochs=100,
            batch_size=32,
            learning_rate=0.001,
            distribution_strategy=DistributionStrategy.FSDP,
            mixed_precision=True,
            use_spot_instances=True,
            spot_interruption_behavior=SpotInterruptionBehavior.STOP,
            priority=JobPriority.HIGH,
        )
        assert job.display_name == "Test Training Job"
        assert job.node_count == 4
        assert job.distribution_strategy == DistributionStrategy.FSDP
        assert job.mixed_precision is True
        assert job.priority == JobPriority.HIGH


class TestStateTransitionMatrix:
    """Tests for the state transition matrix constant."""

    def test_all_statuses_have_transitions(self) -> None:
        """Verify all statuses are keys in the transition matrix."""
        for status in JobStatus:
            assert status in TRAINING_JOB_STATE_TRANSITIONS

    def test_terminal_states_have_no_transitions(self) -> None:
        """Verify terminal states have empty transition sets."""
        assert TRAINING_JOB_STATE_TRANSITIONS[JobStatus.COMPLETED] == set()
        assert TRAINING_JOB_STATE_TRANSITIONS[JobStatus.FAILED] == set()

    def test_submitted_transitions(self) -> None:
        """Verify SUBMITTED state transitions."""
        expected = {JobStatus.RUNNING, JobStatus.FAILED}
        assert TRAINING_JOB_STATE_TRANSITIONS[JobStatus.SUBMITTED] == expected

    def test_running_transitions(self) -> None:
        """Verify RUNNING state transitions."""
        expected = {
            JobStatus.PAUSED,
            JobStatus.PREEMPTED,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        }
        assert TRAINING_JOB_STATE_TRANSITIONS[JobStatus.RUNNING] == expected

    def test_paused_transitions(self) -> None:
        """Verify PAUSED state transitions."""
        expected = {JobStatus.RUNNING, JobStatus.FAILED}
        assert TRAINING_JOB_STATE_TRANSITIONS[JobStatus.PAUSED] == expected

    def test_preempted_transitions(self) -> None:
        """Verify PREEMPTED state transitions."""
        expected = {JobStatus.RUNNING, JobStatus.FAILED}
        assert TRAINING_JOB_STATE_TRANSITIONS[JobStatus.PREEMPTED] == expected
