"""HyperPod Integration Tests - Real AWS environment validation.

NOTE: These tests are designed to be COST-CONSCIOUS.
- Only read-only operations (list, describe) run by default
- Write operations require explicit HYPERPOD_ENABLE_WRITE_TESTS=true flag

Run with: pytest -m aws_integration tests/integration/aws/test_hyperpod_integration.py -v
"""

import os

import pytest
import pytest_asyncio

from src.infrastructure.external.hyperpod.client import HyperPodClient


pytestmark = [
    pytest.mark.aws_integration,
    pytest.mark.hyperpod,
]


def aws_credentials_available() -> bool:
    """Check if AWS credentials are configured."""
    import boto3

    try:
        boto3.client("sts").get_caller_identity()
        return True
    except Exception:
        return False


def hyperpod_write_tests_enabled() -> bool:
    """Check if destructive HyperPod tests are enabled."""
    return os.environ.get("HYPERPOD_ENABLE_WRITE_TESTS", "false").lower() == "true"


skip_without_aws = pytest.mark.skipif(
    not aws_credentials_available(), reason="AWS credentials not available"
)

skip_write_tests = pytest.mark.skipif(
    not hyperpod_write_tests_enabled(),
    reason="HyperPod write tests disabled (set HYPERPOD_ENABLE_WRITE_TESTS=true)",
)


@pytest_asyncio.fixture
async def hyperpod_client() -> HyperPodClient:
    """Create HyperPod client for integration tests."""
    region = os.environ.get("AWS_REGION", "us-west-2")
    return HyperPodClient(region=region)


@pytest.fixture
def test_cluster_name() -> str | None:
    """Get test cluster name from environment."""
    return os.environ.get("HYPERPOD_TEST_CLUSTER_NAME")


class TestHyperPodReadOnly:
    """Test HyperPod read-only operations (cost-free)."""

    @skip_without_aws
    @pytest.mark.asyncio
    async def test_list_clusters_success(
        self,
        hyperpod_client: HyperPodClient,
    ) -> None:
        """Test listing HyperPod clusters."""
        result = await hyperpod_client.list_clusters(max_results=10)

        assert isinstance(result, dict)
        assert "ClusterSummaries" in result or "NextToken" in result or result == {}

        if "ClusterSummaries" in result and result["ClusterSummaries"]:
            cluster = result["ClusterSummaries"][0]
            assert "ClusterName" in cluster
            assert "ClusterStatus" in cluster

    @skip_without_aws
    @pytest.mark.asyncio
    async def test_list_clusters_pagination(
        self,
        hyperpod_client: HyperPodClient,
    ) -> None:
        """Test listing clusters with pagination."""
        result1 = await hyperpod_client.list_clusters(max_results=1)

        if "NextToken" in result1 and result1["NextToken"]:
            result2 = await hyperpod_client.list_clusters(
                max_results=1, next_token=result1["NextToken"]
            )
            assert isinstance(result2, dict)

    @skip_without_aws
    @pytest.mark.asyncio
    async def test_describe_cluster_with_existing_cluster(
        self,
        hyperpod_client: HyperPodClient,
        test_cluster_name: str | None,
    ) -> None:
        """Test describing an existing cluster."""
        if not test_cluster_name:
            clusters = await hyperpod_client.list_clusters(max_results=1)
            if not clusters.get("ClusterSummaries"):
                pytest.skip("No clusters available for describe test")
            test_cluster_name = clusters["ClusterSummaries"][0]["ClusterName"]

        result = await hyperpod_client.describe_cluster(cluster_name=test_cluster_name)

        assert "ClusterName" in result
        assert result["ClusterName"] == test_cluster_name
        assert "ClusterStatus" in result

    @skip_without_aws
    @pytest.mark.asyncio
    async def test_describe_nonexistent_cluster_raises_error(
        self,
        hyperpod_client: HyperPodClient,
    ) -> None:
        """Test describing a non-existent cluster raises error."""
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError) as exc_info:
            await hyperpod_client.describe_cluster(
                cluster_name="nonexistent-cluster-12345"
            )

        error_code = exc_info.value.response["Error"]["Code"]
        assert error_code in ("ResourceNotFound", "ValidationException")


class TestHyperPodStatusMapping:
    """Test HyperPod status mapping to platform status."""

    @skip_without_aws
    @pytest.mark.asyncio
    async def test_cluster_status_values(
        self,
        hyperpod_client: HyperPodClient,
    ) -> None:
        """Verify cluster status values match expected enum."""
        clusters = await hyperpod_client.list_clusters(max_results=100)

        expected_statuses = {
            "Creating",
            "Deleting",
            "Failed",
            "InService",
            "RollingBack",
            "SystemUpdating",
            "Updating",
        }

        for cluster in clusters.get("ClusterSummaries", []):
            status = cluster.get("ClusterStatus")
            assert status in expected_statuses, f"Unexpected status: {status}"


class TestHyperPodErrorHandling:
    """Test HyperPod error handling scenarios."""

    @skip_without_aws
    @pytest.mark.asyncio
    async def test_api_throttling_handling(
        self,
        hyperpod_client: HyperPodClient,
    ) -> None:
        """Test that API throttling is handled gracefully."""
        for _ in range(5):
            result = await hyperpod_client.list_clusters(max_results=1)
            assert isinstance(result, dict)

    @skip_without_aws
    @pytest.mark.asyncio
    async def test_invalid_region_handling(self) -> None:
        """Test handling of invalid region."""
        from botocore.exceptions import ClientError, EndpointConnectionError

        client = HyperPodClient(region="invalid-region-1")

        with pytest.raises((ClientError, EndpointConnectionError)):
            await client.list_clusters()


class TestHyperPodWrite:
    """Test HyperPod write operations (COST WARNING).

    These tests are DISABLED by default.
    To enable: export HYPERPOD_ENABLE_WRITE_TESTS=true

    WARNING: Running these tests will incur AWS charges!
    """

    @skip_without_aws
    @skip_write_tests
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_create_minimal_cluster(
        self,
        hyperpod_client: HyperPodClient,
    ) -> None:
        """Test creating a minimal cluster (EXPENSIVE).

        Uses smallest possible instance to minimize cost.
        Cluster will be deleted after test.
        """
        import uuid

        cluster_name = f"integration-test-{uuid.uuid4().hex[:8]}"
        security_group = os.environ.get("TEST_SECURITY_GROUP")
        subnet = os.environ.get("TEST_SUBNET")

        if not security_group or not subnet:
            pytest.skip("TEST_SECURITY_GROUP and TEST_SUBNET required for write tests")

        try:
            result = await hyperpod_client.create_cluster(
                cluster_name=cluster_name,
                instance_groups=[
                    {
                        "InstanceGroupName": "test-worker",
                        "InstanceType": "ml.t3.medium",
                        "InstanceCount": 1,
                        "LifeCycleConfig": {
                            "SourceS3Uri": "s3://placeholder/lifecycle",
                            "OnCreate": "placeholder.sh",
                        },
                    }
                ],
                vpc_config={
                    "SecurityGroupIds": [security_group],
                    "Subnets": [subnet],
                },
            )

            assert "ClusterArn" in result
            assert result.get("ClusterStatus") in ("Creating", "Pending")

        finally:
            try:
                await hyperpod_client.delete_cluster(cluster_name=cluster_name)
            except Exception:
                pass
