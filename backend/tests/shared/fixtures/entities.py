"""Shared entity fixtures for testing."""

from datetime import UTC, datetime
from typing import Any

import pytest

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.value_objects import Role, UserStatus
from src.modules.models.domain.entities import Model
from src.modules.models.domain.value_objects import ModelFramework, ModelStatus
from src.modules.training.domain.entities import Checkpoint, TrainingJob
from src.modules.training.domain.value_objects import (
    CheckpointStatus,
    DistributionStrategy,
    JobPriority,
    JobStatus,
)

# ========== User Fixtures ==========


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "display_name": "Test User",
        "role": Role.ENGINEER,
        "status": UserStatus.ACTIVE,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


@pytest.fixture
def sample_user(sample_user_data: dict[str, Any]) -> User:
    """Create a sample User entity."""
    return User(**sample_user_data)


@pytest.fixture
def admin_user() -> User:
    """Create an admin User entity."""
    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        display_name="Admin User",
        role=Role.ADMIN,
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ========== TrainingJob Fixtures ==========


@pytest.fixture
def sample_training_job_data() -> dict[str, Any]:
    """Sample training job data for testing."""
    return {
        "id": 1,
        "job_name": "test-job-001",
        "owner_id": 1,
        "image_uri": "123456789012.dkr.ecr.us-west-2.amazonaws.com/ml-training:latest",
        "instance_type": "ml.p4d.24xlarge",
        "entrypoint_command": "python train.py",
        "display_name": "Test Training Job",
        "description": "Test job for unit testing",
        "node_count": 2,
        "tasks_per_node": 8,
        "hyperparameters": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
        },
        "max_epochs": 100,
        "batch_size": 32,
        "learning_rate": 0.001,
        "environment_variables": {"PYTHONPATH": "/opt/ml/code"},
        "distribution_strategy": DistributionStrategy.DDP,
        "mixed_precision": True,
        "use_spot_instances": False,
        "priority": JobPriority.MEDIUM,
        "status": JobStatus.SUBMITTED,
        "dataset_id": 1,
        "data_mount_path": "/data",
        "checkpoint_mount_path": "/checkpoints",
        "checkpoint_interval": 10,
        "submitted_at": datetime.now(UTC),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


@pytest.fixture
def sample_training_job(sample_training_job_data: dict[str, Any]) -> TrainingJob:
    """Create a sample TrainingJob entity."""
    return TrainingJob(**sample_training_job_data)


@pytest.fixture
def running_training_job(sample_training_job: TrainingJob) -> TrainingJob:
    """Create a running TrainingJob entity."""
    job = sample_training_job
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(UTC)
    job.running_pods = job.total_pods
    return job


@pytest.fixture
def completed_training_job(sample_training_job: TrainingJob) -> TrainingJob:
    """Create a completed TrainingJob entity."""
    job = sample_training_job
    job.status = JobStatus.COMPLETED
    job.started_at = datetime.now(UTC)
    job.completed_at = datetime.now(UTC)
    job.duration_seconds = 3600
    job.current_epoch = job.max_epochs
    job.latest_loss = 0.01
    job.latest_accuracy = 0.99
    return job


# ========== Checkpoint Fixtures ==========


@pytest.fixture
def sample_checkpoint_data() -> dict[str, Any]:
    """Sample checkpoint data for testing."""
    return {
        "id": 1,
        "job_id": 1,
        "checkpoint_number": 1,
        "epoch": 10,
        "step": 1000,
        "s3_uri": "s3://ai-training-platform/checkpoints/job-001/checkpoint-001",
        "size_bytes": 1024 * 1024 * 100,  # 100 MB
        "metrics": {
            "loss": 0.5,
            "accuracy": 0.85,
            "val_loss": 0.6,
            "val_accuracy": 0.83,
        },
        "status": CheckpointStatus.READY,
        "is_best": False,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


@pytest.fixture
def sample_checkpoint(sample_checkpoint_data: dict[str, Any]) -> Checkpoint:
    """Create a sample Checkpoint entity."""
    return Checkpoint(**sample_checkpoint_data)


# ========== Model Fixtures ==========


@pytest.fixture
def sample_model_data() -> dict[str, Any]:
    """Sample model data for testing."""
    return {
        "id": 1,
        "model_name": "test-model",
        "owner_id": 1,
        "version": "v1",
        "display_name": "Test Model",
        "description": "Test model for unit testing",
        "training_job_id": 1,
        "checkpoint_id": 1,
        "model_uri": "s3://ai-training-platform/models/test-model/v1",
        "framework": ModelFramework.PYTORCH,
        "framework_version": "2.0.1",
        "metrics": {
            "accuracy": 0.95,
            "f1_score": 0.93,
            "precision": 0.94,
            "recall": 0.92,
        },
        "hyperparameters": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
        },
        "status": ModelStatus.REGISTERED,
        "size_bytes": 1024 * 1024 * 500,  # 500 MB
        "model_format": "pt",
        "tags": ["production", "v1"],
        "registered_at": datetime.now(UTC),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


@pytest.fixture
def sample_model(sample_model_data: dict[str, Any]) -> Model:
    """Create a sample Model entity."""
    return Model(**sample_model_data)


# ========== Batch Fixtures ==========


@pytest.fixture
def batch_training_jobs() -> list[TrainingJob]:
    """Create multiple TrainingJob entities for batch testing."""
    jobs = []
    for i in range(5):
        job = TrainingJob(
            id=i + 1,
            job_name=f"test-job-{i+1:03d}",
            owner_id=1,
            image_uri="123456789012.dkr.ecr.us-west-2.amazonaws.com/ml-training:latest",
            instance_type="ml.p4d.24xlarge",
            entrypoint_command="python train.py",
            node_count=1,
            tasks_per_node=8,
            status=JobStatus.SUBMITTED if i < 3 else JobStatus.RUNNING,
            priority=JobPriority.MEDIUM,
            distribution_strategy=DistributionStrategy.DDP,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        jobs.append(job)
    return jobs


@pytest.fixture
def batch_users() -> list[User]:
    """Create multiple User entities for batch testing."""
    users = []
    roles = [Role.VIEWER, Role.ENGINEER, Role.ADMIN]
    for i in range(3):
        user = User(
            id=i + 1,
            username=f"user{i+1}",
            email=f"user{i+1}@example.com",
            display_name=f"User {i+1}",
            role=roles[i],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        users.append(user)
    return users
