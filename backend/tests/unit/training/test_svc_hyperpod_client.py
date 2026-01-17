"""HyperPod Client Tests - Unit tests for HyperPod SDK client implementation.

Tests follow TDD Red-Green-Refactor cycle.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.training.application.interfaces import IHyperPodClient


class TestHyperPodClient:
    """Test suite for HyperPodClient implementation."""

    @pytest.fixture
    def mock_boto3_client(self) -> MagicMock:
        """Mock boto3 SageMaker client."""
        mock_client = MagicMock()
        with patch("boto3.client", return_value=mock_client):
            yield mock_client

    @pytest.fixture
    def mock_hyperpod_pytorch_job(self) -> MagicMock:
        """Mock HyperPodPytorchJob class."""
        with patch(
            "src.modules.training.infrastructure.hyperpod.client.HyperPodPytorchJob"
        ) as mock:
            yield mock

    @pytest.fixture
    def hyperpod_client(
        self,
        mock_boto3_client: MagicMock,
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> "HyperPodClient":
        """Create HyperPodClient instance with mocked dependencies."""
        from src.modules.training.infrastructure.hyperpod.client import HyperPodClient

        client = HyperPodClient(region="us-west-2")
        # Replace the internal boto3 client with the mock
        client._sagemaker_client = mock_boto3_client
        return client

    # ==================== Cluster Operations ====================

    @pytest.mark.asyncio
    async def test_create_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful cluster creation."""
        mock_boto3_client.create_cluster.return_value = {
            "ClusterArn": "arn:aws:sagemaker:us-west-2:123456:cluster/test-cluster",
            "ClusterStatus": "Creating",
        }

        result = await hyperpod_client.create_cluster(
            cluster_name="test-cluster",
            instance_groups=[
                {
                    "InstanceGroupName": "workers",
                    "InstanceType": "ml.p4d.24xlarge",
                    "InstanceCount": 4,
                }
            ],
            vpc_config={
                "VpcId": "vpc-123",
                "Subnets": ["subnet-abc"],
                "SecurityGroupIds": ["sg-xyz"],
            },
        )

        assert "ClusterArn" in result
        assert result["ClusterStatus"] == "Creating"
        mock_boto3_client.create_cluster.assert_called_once()

    @pytest.mark.asyncio
    async def test_describe_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful cluster description."""
        mock_boto3_client.describe_cluster.return_value = {
            "ClusterName": "test-cluster",
            "ClusterArn": "arn:aws:sagemaker:us-west-2:123456:cluster/test-cluster",
            "ClusterStatus": "InService",
            "InstanceGroups": [
                {
                    "InstanceGroupName": "workers",
                    "InstanceType": "ml.p4d.24xlarge",
                    "InstanceCount": 4,
                }
            ],
        }

        result = await hyperpod_client.describe_cluster(cluster_name="test-cluster")

        assert result["ClusterName"] == "test-cluster"
        assert result["ClusterStatus"] == "InService"
        mock_boto3_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")

    @pytest.mark.asyncio
    async def test_list_clusters_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful cluster listing."""
        mock_boto3_client.list_clusters.return_value = {
            "ClusterSummaries": [
                {"ClusterName": "cluster-1", "ClusterStatus": "InService"},
                {"ClusterName": "cluster-2", "ClusterStatus": "Creating"},
            ],
            "NextToken": None,
        }

        result = await hyperpod_client.list_clusters(max_results=10)

        assert len(result["ClusterSummaries"]) == 2
        assert result["ClusterSummaries"][0]["ClusterName"] == "cluster-1"
        mock_boto3_client.list_clusters.assert_called_once_with(MaxResults=10)

    @pytest.mark.asyncio
    async def test_delete_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful cluster deletion."""
        mock_boto3_client.delete_cluster.return_value = {
            "ClusterArn": "arn:aws:sagemaker:us-west-2:123456:cluster/test-cluster"
        }

        result = await hyperpod_client.delete_cluster(cluster_name="test-cluster")

        assert "ClusterArn" in result
        mock_boto3_client.delete_cluster.assert_called_once_with(
            ClusterName="test-cluster"
        )

    @pytest.mark.asyncio
    async def test_update_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test successful cluster update."""
        mock_boto3_client.update_cluster.return_value = {
            "ClusterArn": "arn:aws:sagemaker:us-west-2:123456:cluster/test-cluster",
            "ClusterStatus": "Updating",
        }

        result = await hyperpod_client.update_cluster(
            cluster_name="test-cluster",
            instance_groups=[
                {
                    "InstanceGroupName": "workers",
                    "InstanceType": "ml.p4d.24xlarge",
                    "InstanceCount": 8,
                }
            ],
        )

        assert result["ClusterStatus"] == "Updating"
        mock_boto3_client.update_cluster.assert_called_once()

    # ==================== Training Job Operations ====================

    @pytest.mark.asyncio
    async def test_submit_training_job_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test successful training job submission."""
        mock_job = MagicMock()
        mock_job.name = "test-training-job"
        mock_job.status = "Pending"
        # Mock the constructor to return mock_job instance
        mock_hyperpod_pytorch_job.return_value = mock_job

        result = await hyperpod_client.submit_training_job(
            cluster_name="test-cluster",
            job_name="test-training-job",
            job_config={
                "image_uri": "123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
                "instance_type": "ml.p4d.24xlarge",
                "node_count": 4,
                "tasks_per_node": 8,
                "command": ["torchrun", "--nproc_per_node=8", "train.py"],
            },
        )

        assert result["job_name"] == "test-training-job"
        assert result["status"] == "submitted"  # Mapped from "Pending"
        # Verify constructor was called and create() was called on the instance
        mock_hyperpod_pytorch_job.assert_called_once()
        mock_job.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_training_job_status_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test successful training job status query."""
        mock_job = MagicMock()
        mock_job.name = "test-training-job"
        mock_job.status = "Running"
        mock_job.start_time = "2026-01-15T10:00:00Z"
        mock_job.end_time = None
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(
            cluster_name="test-cluster", job_name="test-training-job"
        )

        assert result["job_name"] == "test-training-job"
        assert result["status"] == "running"  # Mapped from "Running"
        assert result["start_time"] == "2026-01-15T10:00:00Z"
        mock_hyperpod_pytorch_job.get.assert_called_once_with(name="test-training-job")

    @pytest.mark.asyncio
    async def test_stop_training_job_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test successful training job stop."""
        mock_job = MagicMock()
        mock_job.name = "test-training-job"
        mock_job.delete.return_value = None
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.stop_training_job(
            cluster_name="test-cluster", job_name="test-training-job"
        )

        assert result["job_name"] == "test-training-job"
        assert result["status"] == "stopped"
        mock_job.delete.assert_called_once()

    # ==================== Status Mapping ====================

    @pytest.mark.asyncio
    async def test_status_mapping_pending_to_submitted(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that HyperPod 'Pending' maps to platform 'submitted'."""
        mock_job = MagicMock()
        mock_job.name = "test-job"
        mock_job.status = "Pending"
        mock_job.start_time = None
        mock_job.end_time = None
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(
            cluster_name="test-cluster", job_name="test-job"
        )

        assert result["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_status_mapping_succeeded_to_completed(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that HyperPod 'Succeeded' maps to platform 'completed'."""
        mock_job = MagicMock()
        mock_job.name = "test-job"
        mock_job.status = "Succeeded"
        mock_job.start_time = "2026-01-15T10:00:00Z"
        mock_job.end_time = "2026-01-15T12:00:00Z"
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(
            cluster_name="test-cluster", job_name="test-job"
        )

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_status_mapping_failed_to_failed(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that HyperPod 'Failed' maps to platform 'failed'."""
        mock_job = MagicMock()
        mock_job.name = "test-job"
        mock_job.status = "Failed"
        mock_job.start_time = "2026-01-15T10:00:00Z"
        mock_job.end_time = "2026-01-15T10:30:00Z"
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(
            cluster_name="test-cluster", job_name="test-job"
        )

        assert result["status"] == "failed"

    # ==================== Error Handling ====================

    @pytest.mark.asyncio
    async def test_client_handles_cluster_not_found(
        self,
        hyperpod_client: "HyperPodClient",
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test error handling when cluster is not found."""
        from botocore.exceptions import ClientError

        mock_boto3_client.describe_cluster.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFound", "Message": "Cluster not found"}},
            "DescribeCluster",
        )

        with pytest.raises(ClientError):
            await hyperpod_client.describe_cluster(cluster_name="non-existent")

    @pytest.mark.asyncio
    async def test_client_handles_job_not_found(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test error handling when training job is not found."""
        mock_hyperpod_pytorch_job.get.side_effect = Exception("Job not found")

        with pytest.raises(Exception) as exc_info:
            await hyperpod_client.get_training_job_status(
                cluster_name="test-cluster", job_name="non-existent"
            )

        assert "Job not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_handles_api_throttling(
        self,
        hyperpod_client: "HyperPodClient",
        mock_boto3_client: MagicMock,
    ) -> None:
        """Test error handling for API throttling."""
        from botocore.exceptions import ClientError

        mock_boto3_client.list_clusters.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "ListClusters",
        )

        with pytest.raises(ClientError) as exc_info:
            await hyperpod_client.list_clusters()

        assert exc_info.value.response["Error"]["Code"] == "ThrottlingException"

    # ==================== Interface Compliance ====================

    def test_implements_ihyperpod_client_interface(
        self,
        hyperpod_client: "HyperPodClient",
    ) -> None:
        """Test that HyperPodClient implements IHyperPodClient interface."""
        assert isinstance(hyperpod_client, IHyperPodClient)

    def test_all_interface_methods_implemented(
        self,
        hyperpod_client: "HyperPodClient",
    ) -> None:
        """Test that all interface methods are implemented."""
        interface_methods = [
            "create_cluster",
            "describe_cluster",
            "list_clusters",
            "delete_cluster",
            "update_cluster",
            "submit_training_job",
            "get_training_job_status",
            "stop_training_job",
        ]

        for method_name in interface_methods:
            assert hasattr(hyperpod_client, method_name)
            assert callable(getattr(hyperpod_client, method_name))
