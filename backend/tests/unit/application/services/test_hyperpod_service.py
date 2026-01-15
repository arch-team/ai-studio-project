"""HyperPod Service Unit Tests - TDD Red-Green-Refactor.

T036: HyperPodPytorchJob Integration Logic
- Encapsulate HyperPod SDK training job lifecycle management
- Implement submit, pause, resume, terminate operations
- Error handling and retry mechanism
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.modules.training.domain.entities.training_job import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
    TrainingJob,
)
from src.shared.domain.exceptions import (
    EntityNotFoundError,
)

# === Fixtures ===


@pytest.fixture
def mock_hyperpod_client() -> AsyncMock:
    """Mock HyperPod SDK client."""
    client = AsyncMock()
    client.submit_training_job = AsyncMock(
        return_value={
            "job_name": "test-job-001",
            "status": "submitted",
            "cluster_name": "test-cluster",
        }
    )
    client.get_training_job_status = AsyncMock(
        return_value={
            "job_name": "test-job-001",
            "status": "running",
            "start_time": datetime.utcnow(),
            "cluster_name": "test-cluster",
        }
    )
    client.stop_training_job = AsyncMock(
        return_value={
            "job_name": "test-job-001",
            "status": "stopped",
            "cluster_name": "test-cluster",
        }
    )
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
def job_config() -> dict[str, Any]:
    """Sample job configuration for HyperPod SDK."""
    return {
        "image_uri": "123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
        "instance_type": "ml.p4d.24xlarge",
        "node_count": 2,
        "tasks_per_node": 8,
        "command": ["torchrun", "--nproc_per_node=8", "train.py"],
        "environment": {
            "NCCL_DEBUG": "INFO",
            "NCCL_SOCKET_IFNAME": "eth0",
        },
        "volumes": [],
    }


# === Test Class: HyperPodService ===


class TestHyperPodServiceSubmit:
    """Test HyperPodService.submit_job method."""

    @pytest.mark.asyncio
    async def test_submit_job_success(
        self, mock_hyperpod_client: AsyncMock, job_config: dict[str, Any]
    ) -> None:
        """Submit job successfully via HyperPod SDK."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        result = await service.submit_job(
            job_name="test-job-001",
            job_config=job_config,
        )

        assert result["job_name"] == "test-job-001"
        assert result["status"] == "submitted"
        mock_hyperpod_client.submit_training_job.assert_awaited_once_with(
            cluster_name="test-cluster",
            job_name="test-job-001",
            job_config=job_config,
        )

    @pytest.mark.asyncio
    async def test_submit_job_sdk_error_with_retry(
        self, mock_hyperpod_client: AsyncMock, job_config: dict[str, Any]
    ) -> None:
        """Submit job with retry on transient SDK errors."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        # First call fails, second succeeds
        mock_hyperpod_client.submit_training_job.side_effect = [
            RuntimeError("Transient error"),
            {
                "job_name": "test-job-001",
                "status": "submitted",
                "cluster_name": "test-cluster",
            },
        ]

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
            max_retries=3,
            retry_delay=0.1,
        )

        result = await service.submit_job(
            job_name="test-job-001",
            job_config=job_config,
        )

        assert result["status"] == "submitted"
        assert mock_hyperpod_client.submit_training_job.await_count == 2

    @pytest.mark.asyncio
    async def test_submit_job_max_retries_exceeded(
        self, mock_hyperpod_client: AsyncMock, job_config: dict[str, Any]
    ) -> None:
        """Submit job fails after max retries exceeded."""
        from src.modules.training.application.services.hyperpod_service import (
            HyperPodService,
            HyperPodServiceError,
        )

        mock_hyperpod_client.submit_training_job.side_effect = RuntimeError(
            "Persistent error"
        )

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
            max_retries=2,
            retry_delay=0.1,
        )

        with pytest.raises(HyperPodServiceError) as exc_info:
            await service.submit_job(
                job_name="test-job-001",
                job_config=job_config,
            )

        assert "failed after 2 retries" in str(exc_info.value)


class TestHyperPodServiceGetStatus:
    """Test HyperPodService.get_job_status method."""

    @pytest.mark.asyncio
    async def test_get_job_status_success(
        self, mock_hyperpod_client: AsyncMock
    ) -> None:
        """Get job status successfully."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        result = await service.get_job_status(job_name="test-job-001")

        assert result["job_name"] == "test-job-001"
        assert result["status"] == "running"
        mock_hyperpod_client.get_training_job_status.assert_awaited_once_with(
            cluster_name="test-cluster",
            job_name="test-job-001",
        )

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(
        self, mock_hyperpod_client: AsyncMock
    ) -> None:
        """Get status for non-existent job."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        mock_hyperpod_client.get_training_job_status.side_effect = RuntimeError(
            "Job not found"
        )

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        with pytest.raises(EntityNotFoundError):
            await service.get_job_status(job_name="non-existent-job")


class TestHyperPodServiceTerminate:
    """Test HyperPodService.terminate_job method."""

    @pytest.mark.asyncio
    async def test_terminate_job_success(self, mock_hyperpod_client: AsyncMock) -> None:
        """Terminate running job successfully."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        result = await service.terminate_job(job_name="test-job-001")

        assert result["status"] == "stopped"
        mock_hyperpod_client.stop_training_job.assert_awaited_once_with(
            cluster_name="test-cluster",
            job_name="test-job-001",
        )

    @pytest.mark.asyncio
    async def test_terminate_job_with_retry(
        self, mock_hyperpod_client: AsyncMock
    ) -> None:
        """Terminate job with retry on transient errors."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        mock_hyperpod_client.stop_training_job.side_effect = [
            RuntimeError("Transient error"),
            {
                "job_name": "test-job-001",
                "status": "stopped",
                "cluster_name": "test-cluster",
            },
        ]

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
            max_retries=3,
            retry_delay=0.1,
        )

        result = await service.terminate_job(job_name="test-job-001")

        assert result["status"] == "stopped"
        assert mock_hyperpod_client.stop_training_job.await_count == 2


class TestHyperPodServicePause:
    """Test HyperPodService.pause_job method.

    Note: HyperPod SDK does not have native pause support.
    Pause is implemented as checkpointing + terminate.
    """

    @pytest.mark.asyncio
    async def test_pause_job_triggers_checkpoint_and_stop(
        self, mock_hyperpod_client: AsyncMock
    ) -> None:
        """Pause job triggers checkpoint signal and stops job."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        result = await service.pause_job(job_name="test-job-001")

        assert result["status"] == "paused"
        mock_hyperpod_client.stop_training_job.assert_awaited_once()


class TestHyperPodServiceResume:
    """Test HyperPodService.resume_job method.

    Note: Resume is implemented as resubmitting with checkpoint restore.
    """

    @pytest.mark.asyncio
    async def test_resume_job_resubmits_with_checkpoint(
        self, mock_hyperpod_client: AsyncMock, job_config: dict[str, Any]
    ) -> None:
        """Resume job resubmits with checkpoint configuration."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        result = await service.resume_job(
            job_name="test-job-001",
            job_config=job_config,
            checkpoint_path="/checkpoints/epoch-10.pth",
        )

        assert result["status"] == "submitted"
        mock_hyperpod_client.submit_training_job.assert_awaited_once()
        # Verify checkpoint path is included in config
        call_args = mock_hyperpod_client.submit_training_job.call_args
        submitted_config = call_args.kwargs.get("job_config") or call_args[1].get(
            "job_config"
        )
        assert submitted_config.get("checkpoint_path") == "/checkpoints/epoch-10.pth"


class TestHyperPodServiceListPods:
    """Test HyperPodService.list_job_pods method."""

    @pytest.mark.asyncio
    async def test_list_job_pods_success(self, mock_hyperpod_client: AsyncMock) -> None:
        """List pods for a training job."""
        from src.modules.training.application.services.hyperpod_service import HyperPodService

        mock_hyperpod_client.list_training_job_pods = AsyncMock(
            return_value=[
                {
                    "name": "test-job-001-worker-0",
                    "status": "Running",
                    "node_name": "node-1",
                },
                {
                    "name": "test-job-001-worker-1",
                    "status": "Running",
                    "node_name": "node-2",
                },
            ]
        )

        service = HyperPodService(
            hyperpod_client=mock_hyperpod_client,
            cluster_name="test-cluster",
        )

        pods = await service.list_job_pods(job_name="test-job-001")

        assert len(pods) == 2
        assert pods[0]["name"] == "test-job-001-worker-0"


class TestHyperPodServiceStatusMapping:
    """Test HyperPod status to platform status mapping."""

    @pytest.mark.parametrize(
        "hyperpod_status,expected_platform_status",
        [
            ("Pending", "submitted"),
            ("Running", "running"),
            ("Succeeded", "completed"),
            ("Failed", "failed"),
            ("Unknown", "unknown"),
        ],
    )
    def test_status_mapping(
        self, hyperpod_status: str, expected_platform_status: str
    ) -> None:
        """Map HyperPod status to platform status."""
        from src.modules.training.application.services.hyperpod_service import map_hyperpod_status

        assert map_hyperpod_status(hyperpod_status) == expected_platform_status


class TestHyperPodServiceVolumeConfig:
    """Test HyperPod volume configuration building."""

    def test_build_fsx_volume_config(self) -> None:
        """Build FSx for Lustre volume configuration."""
        from src.modules.training.application.services.hyperpod_service import build_volume_config

        volumes = build_volume_config(
            data_path="/fsx/training-data",
            checkpoint_path="/fsx/checkpoints",
        )

        assert len(volumes) == 2
        assert volumes[0]["name"] == "training-data"
        assert volumes[0]["mount_path"] == "/data"
        assert volumes[0]["path"] == "/fsx/training-data"
        assert volumes[1]["name"] == "checkpoints"
        assert volumes[1]["mount_path"] == "/checkpoints"


class TestHyperPodServiceJobConfig:
    """Test HyperPod job configuration building."""

    def test_build_job_config_from_entity(self, sample_job: TrainingJob) -> None:
        """Build HyperPod job config from TrainingJob entity."""
        from src.modules.training.application.services.hyperpod_service import build_job_config

        config = build_job_config(sample_job)

        assert config["image_uri"] == sample_job.image_uri
        assert config["instance_type"] == sample_job.instance_type
        assert config["node_count"] == sample_job.node_count
        assert config["tasks_per_node"] == sample_job.tasks_per_node
        assert config["command"] == sample_job.entrypoint_command
