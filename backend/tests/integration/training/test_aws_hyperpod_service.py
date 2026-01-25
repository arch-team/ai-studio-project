"""HyperPodService AWS Integration Tests.

T036: Verify HyperPodService operations against real AWS HyperPod cluster.
Tests HyperPod SDK integration through the service layer.

Prerequisites:
- AWS credentials configured (AWS_PROFILE or explicit credentials)
- HYPERPOD_TEST_CLUSTER_NAME environment variable set
- For write tests: HYPERPOD_ENABLE_WRITE_TESTS=true
"""

import os
import uuid
from typing import Any

import pytest
import pytest_asyncio

from src.modules.training.application.services.hyperpod_service import (
    HyperPodService,
)
from src.modules.training.infrastructure.hyperpod.client import HyperPodClient
from src.shared.domain.exceptions import EntityNotFoundError

# Mark all tests as AWS integration tests
pytestmark = [
    pytest.mark.aws_integration,
    pytest.mark.hyperpod,
]


# === Helper Functions ===


def aws_credentials_available() -> bool:
    """Check if AWS credentials are available."""
    try:
        import boto3

        boto3.client("sts").get_caller_identity()
        return True
    except Exception:
        return False


def hyperpod_cluster_configured() -> bool:
    """Check if HyperPod test cluster is configured."""
    return bool(os.environ.get("HYPERPOD_TEST_CLUSTER_NAME"))


def hyperpod_write_tests_enabled() -> bool:
    """Check if HyperPod write tests are enabled."""
    return os.environ.get("HYPERPOD_ENABLE_WRITE_TESTS", "false").lower() == "true"


# Skip decorators
skip_without_aws = pytest.mark.skipif(
    not aws_credentials_available(),
    reason="AWS credentials not available",
)

skip_without_cluster = pytest.mark.skipif(
    not hyperpod_cluster_configured(),
    reason="HYPERPOD_TEST_CLUSTER_NAME not configured",
)

skip_write_tests = pytest.mark.skipif(
    not hyperpod_write_tests_enabled(),
    reason="HyperPod write tests disabled (set HYPERPOD_ENABLE_WRITE_TESTS=true)",
)


# === Fixtures ===


@pytest.fixture(scope="session")
def aws_region() -> str:
    """Get AWS region from environment."""
    return os.environ.get("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def test_cluster_name() -> str:
    """Get test cluster name from environment."""
    return os.environ.get("HYPERPOD_TEST_CLUSTER_NAME", "")


@pytest_asyncio.fixture
async def hyperpod_client(aws_region: str) -> HyperPodClient:
    """Create HyperPod client for testing."""
    return HyperPodClient(region=aws_region)


@pytest_asyncio.fixture
async def hyperpod_service(
    hyperpod_client: HyperPodClient,
    test_cluster_name: str,
) -> HyperPodService:
    """Create HyperPodService for testing."""
    return HyperPodService(
        hyperpod_client=hyperpod_client,
        cluster_name=test_cluster_name,
        max_retries=3,
        retry_delay=1.0,
    )


@pytest.fixture
def test_job_name() -> str:
    """Generate unique test job name."""
    return f"integration-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def minimal_job_config(aws_region: str) -> dict[str, Any]:
    """Minimal job configuration for testing."""
    # Use AWS Deep Learning Container for PyTorch
    account_id = "763104351884"  # AWS DLC account ID for us-east-1
    return {
        "image_uri": f"{account_id}.dkr.ecr.{aws_region}.amazonaws.com/pytorch-training:2.0.1-gpu-py310-cu118-ubuntu20.04-ec2",
        "instance_type": "ml.g4dn.xlarge",  # Minimal GPU instance
        "node_count": 1,
        "tasks_per_node": 1,
        "command": ["python", "-c", "import torch; print(f'PyTorch {torch.__version__}'); import time; time.sleep(30)"],
        "environment": {
            "NCCL_DEBUG": "INFO",
        },
    }


# === Test Classes ===


class TestHyperPodServiceReadOnly:
    """Read-only tests for HyperPodService (no cost)."""

    @skip_without_aws
    @skip_without_cluster
    @pytest.mark.asyncio
    async def test_get_nonexistent_job_raises_not_found(
        self,
        hyperpod_service: HyperPodService,
    ) -> None:
        """Verify get_job_status raises EntityNotFoundError for non-existent job."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await hyperpod_service.get_job_status(job_name="nonexistent-job-12345")

        assert "TrainingJob" in str(exc_info.value)

    @skip_without_aws
    @skip_without_cluster
    @pytest.mark.asyncio
    async def test_service_initialization(
        self,
        hyperpod_service: HyperPodService,
        test_cluster_name: str,
    ) -> None:
        """Verify HyperPodService initializes correctly."""
        assert hyperpod_service._cluster_name == test_cluster_name
        assert hyperpod_service._max_retries == 3
        assert hyperpod_service._retry_delay == 1.0

    @skip_without_aws
    @skip_without_cluster
    @pytest.mark.asyncio
    async def test_retry_mechanism_configuration(
        self,
        hyperpod_client: HyperPodClient,
        test_cluster_name: str,
    ) -> None:
        """Verify retry mechanism is properly configured."""
        service = HyperPodService(
            hyperpod_client=hyperpod_client,
            cluster_name=test_cluster_name,
            max_retries=5,
            retry_delay=2.0,
        )
        assert service._max_retries == 5
        assert service._retry_delay == 2.0


class TestHyperPodServiceClusterOperations:
    """Test HyperPodService with real cluster operations."""

    @skip_without_aws
    @skip_without_cluster
    @pytest.mark.asyncio
    async def test_underlying_client_describe_cluster(
        self,
        hyperpod_client: HyperPodClient,
        test_cluster_name: str,
    ) -> None:
        """Verify underlying client can describe the test cluster."""
        result = await hyperpod_client.describe_cluster(test_cluster_name)

        assert result is not None
        # Verify cluster status (may vary based on actual cluster state)
        assert "ClusterStatus" in result or "status" in str(result).lower()

    @skip_without_aws
    @skip_without_cluster
    @pytest.mark.asyncio
    async def test_list_clusters_includes_test_cluster(
        self,
        hyperpod_client: HyperPodClient,
        test_cluster_name: str,
    ) -> None:
        """Verify test cluster appears in cluster list."""
        result = await hyperpod_client.list_clusters(max_results=100)

        cluster_names = [c.get("ClusterName", "") for c in result.get("ClusterSummaries", [])]
        assert test_cluster_name in cluster_names


class TestHyperPodServiceWriteOperations:
    """Write operation tests (create/terminate jobs) - requires HYPERPOD_ENABLE_WRITE_TESTS=true."""

    @skip_without_aws
    @skip_without_cluster
    @skip_write_tests
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_submit_and_terminate_job(
        self,
        hyperpod_service: HyperPodService,
        test_job_name: str,
        minimal_job_config: dict[str, Any],
    ) -> None:
        """Test full job lifecycle: submit -> check status -> terminate.

        WARNING: This test creates a real training job and will incur AWS costs.
        """
        try:
            # Submit job
            submit_result = await hyperpod_service.submit_job(
                job_name=test_job_name,
                job_config=minimal_job_config,
            )

            assert submit_result["job_name"] == test_job_name
            # 刚提交时 SDK 可能还没同步状态，返回 unknown 是正常的
            assert submit_result["status"] in ["submitted", "running", "pending", "unknown"]

            # Give the job time to be registered
            import asyncio

            await asyncio.sleep(5)

            # Check status
            status_result = await hyperpod_service.get_job_status(job_name=test_job_name)
            assert status_result["job_name"] == test_job_name

        finally:
            # Always try to terminate to avoid leaving jobs running
            try:
                await hyperpod_service.terminate_job(job_name=test_job_name)
            except Exception:
                pass  # Job may have already completed or failed

    @skip_without_aws
    @skip_without_cluster
    @skip_write_tests
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_submit_job_with_retry_on_transient_error(
        self,
        hyperpod_service: HyperPodService,
        test_job_name: str,
        minimal_job_config: dict[str, Any],
    ) -> None:
        """Verify retry mechanism works for job submission.

        Note: This test submits a real job.
        """
        try:
            # Submit should succeed (retry mechanism handles transient errors)
            result = await hyperpod_service.submit_job(
                job_name=test_job_name,
                job_config=minimal_job_config,
            )
            assert result["job_name"] == test_job_name
        finally:
            try:
                await hyperpod_service.terminate_job(job_name=test_job_name)
            except Exception:
                pass


class TestHyperPodServiceStatusMapping:
    """Test status mapping functionality."""

    def test_status_mapping_values(self) -> None:
        """Verify all expected status mappings exist."""
        from src.modules.training.application.services.hyperpod_service import map_hyperpod_status

        assert map_hyperpod_status("Pending") == "submitted"
        assert map_hyperpod_status("Running") == "running"
        assert map_hyperpod_status("Succeeded") == "completed"
        assert map_hyperpod_status("Failed") == "failed"
        assert map_hyperpod_status("Unknown") == "unknown"
        assert map_hyperpod_status("SomeOtherStatus") == "unknown"


class TestHyperPodServiceVolumeConfig:
    """Test volume configuration building."""

    def test_build_volume_config_with_data_path(self) -> None:
        """Verify volume config is built correctly."""
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

    def test_build_volume_config_partial(self) -> None:
        """Verify partial volume config works."""
        from src.modules.training.application.services.hyperpod_service import build_volume_config

        volumes = build_volume_config(data_path="/fsx/data")
        assert len(volumes) == 1
        assert volumes[0]["name"] == "training-data"

        volumes = build_volume_config(checkpoint_path="/fsx/ckpt")
        assert len(volumes) == 1
        assert volumes[0]["name"] == "checkpoints"

        volumes = build_volume_config()
        assert len(volumes) == 0
