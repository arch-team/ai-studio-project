"""HyperPod Client Tests - Unit tests for HyperPod SDK client implementation.

Tests follow TDD Red-Green-Refactor cycle.
"""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.training.application.interfaces import IHyperPodClient
from src.modules.training.domain.exceptions import (
    HyperPodOperationError,
    HyperPodPodNotFoundError,
)

if TYPE_CHECKING:
    from src.modules.training.infrastructure.hyperpod.client import HyperPodClient


class TestHyperPodClient:
    """Test suite for HyperPodClient implementation."""

    @pytest.fixture
    def mock_sagemaker_client(self) -> MagicMock:
        """Mock aioboto3 SageMaker client (async methods)."""
        mock_client = MagicMock()
        # 设置所有方法返回 AsyncMock
        mock_client.create_cluster = AsyncMock()
        mock_client.describe_cluster = AsyncMock()
        mock_client.list_clusters = AsyncMock()
        mock_client.delete_cluster = AsyncMock()
        mock_client.update_cluster = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_s3_client(self) -> MagicMock:
        """Mock aioboto3 S3 client (async methods)."""
        mock_client = MagicMock()
        mock_client.head_object = AsyncMock()
        mock_client.list_objects_v2 = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_aioboto3_session(self, mock_sagemaker_client: MagicMock, mock_s3_client: MagicMock) -> MagicMock:
        """Mock aioboto3.Session with async context manager support."""
        mock_session = MagicMock()

        @asynccontextmanager
        async def mock_client(service_name: str, **kwargs):
            """Return appropriate mock client based on service name."""
            if service_name == "sagemaker":
                yield mock_sagemaker_client
            elif service_name == "s3":
                yield mock_s3_client
            else:
                yield MagicMock()

        mock_session.client = mock_client
        return mock_session

    @pytest.fixture
    def mock_hyperpod_pytorch_job(self) -> MagicMock:
        """Mock HyperPodPytorchJob class."""
        with patch("src.modules.training.infrastructure.hyperpod.client.HyperPodPytorchJob") as mock:
            yield mock

    @pytest.fixture
    def hyperpod_client(
        self,
        mock_aioboto3_session: MagicMock,
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> "HyperPodClient":
        """Create HyperPodClient instance with mocked dependencies."""
        from src.modules.training.infrastructure.hyperpod.client import HyperPodClient

        client = HyperPodClient(region="us-west-2")
        # Replace the internal aioboto3 session with the mock
        client._session = mock_aioboto3_session
        return client

    # ==================== Cluster Operations ====================

    @pytest.mark.asyncio
    async def test_create_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_sagemaker_client: MagicMock,
    ) -> None:
        """Test successful cluster creation."""
        mock_sagemaker_client.create_cluster.return_value = {
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
        mock_sagemaker_client.create_cluster.assert_called_once()

    @pytest.mark.asyncio
    async def test_describe_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_sagemaker_client: MagicMock,
    ) -> None:
        """Test successful cluster description."""
        mock_sagemaker_client.describe_cluster.return_value = {
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
        mock_sagemaker_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")

    @pytest.mark.asyncio
    async def test_list_clusters_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_sagemaker_client: MagicMock,
    ) -> None:
        """Test successful cluster listing."""
        mock_sagemaker_client.list_clusters.return_value = {
            "ClusterSummaries": [
                {"ClusterName": "cluster-1", "ClusterStatus": "InService"},
                {"ClusterName": "cluster-2", "ClusterStatus": "Creating"},
            ],
            "NextToken": None,
        }

        result = await hyperpod_client.list_clusters(max_results=10)

        assert len(result["ClusterSummaries"]) == 2
        assert result["ClusterSummaries"][0]["ClusterName"] == "cluster-1"
        mock_sagemaker_client.list_clusters.assert_called_once_with(MaxResults=10)

    @pytest.mark.asyncio
    async def test_delete_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_sagemaker_client: MagicMock,
    ) -> None:
        """Test successful cluster deletion."""
        mock_sagemaker_client.delete_cluster.return_value = {
            "ClusterArn": "arn:aws:sagemaker:us-west-2:123456:cluster/test-cluster"
        }

        result = await hyperpod_client.delete_cluster(cluster_name="test-cluster")

        assert "ClusterArn" in result
        mock_sagemaker_client.delete_cluster.assert_called_once_with(ClusterName="test-cluster")

    @pytest.mark.asyncio
    async def test_update_cluster_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_sagemaker_client: MagicMock,
    ) -> None:
        """Test successful cluster update."""
        mock_sagemaker_client.update_cluster.return_value = {
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
        mock_sagemaker_client.update_cluster.assert_called_once()

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
        # 创建符合新 SDK 结构的 mock
        mock_condition = MagicMock()
        mock_condition.type = "Running"
        mock_condition.status = "True"

        mock_status = MagicMock()
        mock_status.conditions = [mock_condition]
        mock_status.startTime = "2026-01-15T10:00:00Z"
        mock_status.completionTime = None

        mock_metadata = MagicMock()
        mock_metadata.name = "test-training-job"

        mock_job = MagicMock()
        mock_job.metadata = mock_metadata
        mock_job.status = mock_status
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(
            cluster_name="test-cluster", job_name="test-training-job"
        )

        assert result["job_name"] == "test-training-job"
        assert result["status"] == "running"  # Mapped from "Running"
        assert result["start_time"] == "2026-01-15T10:00:00Z"
        mock_hyperpod_pytorch_job.get.assert_called_once_with(name="test-training-job", namespace="default")

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

        result = await hyperpod_client.stop_training_job(cluster_name="test-cluster", job_name="test-training-job")

        assert result["job_name"] == "test-training-job"
        assert result["status"] == "stopped"
        mock_job.delete.assert_called_once()

    # ==================== Status Mapping ====================

    def _create_mock_job_with_status(
        self,
        job_name: str,
        status_type: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> MagicMock:
        """Helper to create mock job with new SDK structure."""
        mock_condition = MagicMock()
        mock_condition.type = status_type
        mock_condition.status = "True"

        mock_status = MagicMock()
        mock_status.conditions = [mock_condition]
        mock_status.startTime = start_time
        mock_status.completionTime = end_time

        mock_metadata = MagicMock()
        mock_metadata.name = job_name

        mock_job = MagicMock()
        mock_job.metadata = mock_metadata
        mock_job.status = mock_status
        return mock_job

    @pytest.mark.asyncio
    async def test_status_mapping_pending_to_submitted(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that HyperPod 'Pending' maps to platform 'submitted'."""
        mock_job = self._create_mock_job_with_status("test-job", "Pending")
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(cluster_name="test-cluster", job_name="test-job")

        assert result["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_status_mapping_succeeded_to_completed(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that HyperPod 'Succeeded' maps to platform 'completed'."""
        mock_job = self._create_mock_job_with_status(
            "test-job", "Succeeded", "2026-01-15T10:00:00Z", "2026-01-15T12:00:00Z"
        )
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(cluster_name="test-cluster", job_name="test-job")

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_status_mapping_failed_to_failed(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that HyperPod 'Failed' maps to platform 'failed'."""
        mock_job = self._create_mock_job_with_status(
            "test-job", "Failed", "2026-01-15T10:00:00Z", "2026-01-15T10:30:00Z"
        )
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_training_job_status(cluster_name="test-cluster", job_name="test-job")

        assert result["status"] == "failed"

    # ==================== Error Handling ====================

    @pytest.mark.asyncio
    async def test_client_handles_cluster_not_found(
        self,
        hyperpod_client: "HyperPodClient",
        mock_sagemaker_client: MagicMock,
    ) -> None:
        """Test error handling when cluster is not found."""
        from botocore.exceptions import ClientError

        mock_sagemaker_client.describe_cluster.side_effect = ClientError(
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
            await hyperpod_client.get_training_job_status(cluster_name="test-cluster", job_name="non-existent")

        assert "Job not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_handles_api_throttling(
        self,
        hyperpod_client: "HyperPodClient",
        mock_sagemaker_client: MagicMock,
    ) -> None:
        """Test error handling for API throttling."""
        from botocore.exceptions import ClientError

        mock_sagemaker_client.list_clusters.side_effect = ClientError(
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
            # E2E 测试支持方法
            "cancel_training_job",
            "get_job_pods",
            "get_pod_status",
            "verify_checkpoint_exists",
            "list_checkpoints",
            "resume_training_job",
            "trigger_preemption",
        ]

        for method_name in interface_methods:
            assert hasattr(hyperpod_client, method_name)
            assert callable(getattr(hyperpod_client, method_name))

    # ==================== E2E 测试支持方法 ====================

    @pytest.mark.asyncio
    async def test_cancel_training_job_delegates_to_stop(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test cancel_training_job delegates to stop_training_job."""
        mock_job = MagicMock()
        mock_job.name = "test-job"
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.cancel_training_job(job_id="test-job")

        assert result["job_name"] == "test-job"
        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_get_job_pods_delegates_to_list_pods(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test get_job_pods delegates to list_training_job_pods."""
        mock_job = MagicMock()
        mock_job.list_pods.return_value = [
            {"name": "pod-1", "phase": "Running"},
            {"name": "pod-2", "phase": "Running"},
        ]
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_job_pods(job_id="test-job")

        assert len(result) == 2
        assert result[0]["name"] == "pod-1"

    @pytest.mark.asyncio
    async def test_get_pod_status_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test successful pod status query."""
        mock_job = MagicMock()
        mock_job.list_pods.return_value = [
            {"name": "pod-1", "phase": "Running", "status": {"ready": True}},
            {"name": "pod-2", "phase": "Pending", "status": {"ready": False}},
        ]
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        result = await hyperpod_client.get_pod_status(
            cluster_name="test-cluster",
            job_name="test-job",
            pod_name="pod-1",
        )

        assert result["name"] == "pod-1"
        assert result["phase"] == "Running"
        assert result["status"]["ready"] is True

    @pytest.mark.asyncio
    async def test_get_pod_status_not_found(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test error when pod is not found."""
        mock_job = MagicMock()
        mock_job.list_pods.return_value = [
            {"name": "pod-1", "phase": "Running"},
        ]
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        with pytest.raises(HyperPodPodNotFoundError) as exc_info:
            await hyperpod_client.get_pod_status(
                cluster_name="test-cluster",
                job_name="test-job",
                pod_name="non-existent-pod",
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_checkpoint_exists_returns_true(
        self,
        hyperpod_client: "HyperPodClient",
        mock_s3_client: MagicMock,
    ) -> None:
        """Test verify_checkpoint_exists returns True when file exists."""
        mock_s3_client.head_object.return_value = {"ContentLength": 1024}

        result = await hyperpod_client.verify_checkpoint_exists(s3_path="s3://my-bucket/checkpoints/job-123/model.pt")

        assert result is True
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="my-bucket",
            Key="checkpoints/job-123/model.pt",
        )

    @pytest.mark.asyncio
    async def test_verify_checkpoint_exists_returns_false(
        self,
        hyperpod_client: "HyperPodClient",
        mock_s3_client: MagicMock,
    ) -> None:
        """Test verify_checkpoint_exists returns False when file does not exist."""
        from botocore.exceptions import ClientError

        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )

        result = await hyperpod_client.verify_checkpoint_exists(s3_path="s3://my-bucket/checkpoints/job-123/model.pt")

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_checkpoint_exists_invalid_path(
        self,
        hyperpod_client: "HyperPodClient",
    ) -> None:
        """Test verify_checkpoint_exists raises error for invalid path."""
        with pytest.raises(HyperPodOperationError) as exc_info:
            await hyperpod_client.verify_checkpoint_exists(s3_path="invalid-path")

        assert "Invalid S3 path" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_checkpoints_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_s3_client: MagicMock,
    ) -> None:
        """Test successful checkpoint listing."""
        from datetime import datetime

        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "checkpoints/job-123/epoch_1.pt",
                    "Size": 1024,
                    "LastModified": datetime(2026, 1, 15, 10, 0, 0),
                    "ETag": '"abc123"',
                },
                {
                    "Key": "checkpoints/job-123/epoch_2.pt",
                    "Size": 2048,
                    "LastModified": datetime(2026, 1, 15, 12, 0, 0),
                    "ETag": '"def456"',
                },
            ]
        }

        result = await hyperpod_client.list_checkpoints(
            job_id="job-123",
            checkpoint_base_path="s3://my-bucket/checkpoints",
        )

        assert len(result) == 2
        assert result[0]["key"] == "checkpoints/job-123/epoch_1.pt"
        assert result[0]["size"] == 1024
        assert result[1]["key"] == "checkpoints/job-123/epoch_2.pt"

    @pytest.mark.asyncio
    async def test_list_checkpoints_empty(
        self,
        hyperpod_client: "HyperPodClient",
        mock_s3_client: MagicMock,
    ) -> None:
        """Test list_checkpoints returns empty list when no checkpoints."""
        mock_s3_client.list_objects_v2.return_value = {}

        result = await hyperpod_client.list_checkpoints(
            job_id="job-123",
            checkpoint_base_path="s3://my-bucket/checkpoints",
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_list_checkpoints_invalid_path(
        self,
        hyperpod_client: "HyperPodClient",
    ) -> None:
        """Test list_checkpoints returns empty list for invalid path."""
        result = await hyperpod_client.list_checkpoints(
            job_id="job-123",
            checkpoint_base_path="invalid-path",
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_resume_training_job_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test successful training job resume."""
        mock_job = MagicMock()
        mock_job.status = MagicMock(phase="Pending")
        mock_hyperpod_pytorch_job.return_value = mock_job

        result = await hyperpod_client.resume_training_job(
            cluster_name="test-cluster",
            job_name="resumed-job",
            checkpoint_path="s3://bucket/checkpoints/job-123/model.pt",
            job_config={
                "image_uri": "123456.dkr.ecr.us-east-1.amazonaws.com/pytorch:2.1",
                "instance_type": "ml.p4d.24xlarge",
                "node_count": 4,
                "command": ["torchrun", "train.py"],
            },
        )

        assert result["job_name"] == "resumed-job"
        assert result["status"] == "submitted"
        assert result["resumed"] is True
        assert result["checkpoint_path"] == "s3://bucket/checkpoints/job-123/model.pt"
        mock_job.create.assert_called_once()

        # 验证使用新 SDK API 调用 (metadata, replica_specs, run_policy)
        call_kwargs = mock_hyperpod_pytorch_job.call_args[1]
        assert "metadata" in call_kwargs
        assert "replica_specs" in call_kwargs
        assert "run_policy" in call_kwargs

    @pytest.mark.asyncio
    async def test_resume_training_job_without_config_raises_error(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test resume_training_job raises error when job_config is None."""
        with pytest.raises(HyperPodOperationError) as exc_info:
            await hyperpod_client.resume_training_job(
                cluster_name="test-cluster",
                job_name="resumed-job",
                checkpoint_path="s3://bucket/checkpoints/model.pt",
                job_config=None,
            )

        assert "job_config is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_trigger_preemption_success(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test successful preemption trigger."""
        # Mock 目标任务
        mock_target_job = MagicMock()
        mock_target_job.status = "Running"

        # Mock 高优先级任务
        mock_preemption_job = MagicMock()
        mock_preemption_job.status = MagicMock(phase="Pending")

        # 设置 get 和构造函数返回不同对象
        mock_hyperpod_pytorch_job.get.return_value = mock_target_job
        mock_hyperpod_pytorch_job.return_value = mock_preemption_job

        result = await hyperpod_client.trigger_preemption(
            cluster_name="test-cluster",
            target_job_name="low-priority-job",
            preemption_job_config={
                "image_uri": "123456.dkr.ecr.us-east-1.amazonaws.com/pytorch:2.1",
                "instance_type": "ml.p4d.24xlarge",
                "node_count": 4,
                "command": ["torchrun", "train.py"],
            },
        )

        assert result["target_job_name"] == "low-priority-job"
        assert "preempt-low-priority-job" in result["preemption_job_name"]
        assert result["preemption_job_status"] == "submitted"
        assert result["mechanism"] == "high_priority_task"
        mock_preemption_job.create.assert_called_once()

        # 验证使用新 SDK API 调用 (metadata, replica_specs, run_policy)
        call_kwargs = mock_hyperpod_pytorch_job.call_args[1]
        assert "metadata" in call_kwargs
        assert "replica_specs" in call_kwargs
        assert "run_policy" in call_kwargs

    @pytest.mark.asyncio
    async def test_trigger_preemption_target_not_running(
        self,
        hyperpod_client: "HyperPodClient",
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test trigger_preemption raises error when target job is not running."""
        mock_target_job = MagicMock()
        mock_target_job.status = "Pending"  # 不是 Running
        mock_hyperpod_pytorch_job.get.return_value = mock_target_job

        with pytest.raises(HyperPodOperationError) as exc_info:
            await hyperpod_client.trigger_preemption(
                cluster_name="test-cluster",
                target_job_name="pending-job",
                preemption_job_config={
                    "image_uri": "test",
                    "instance_type": "ml.p4d.24xlarge",
                },
            )

        assert "is not running" in str(exc_info.value)

    # ==================== Default Region ====================

    def test_default_region_is_us_east_1(self) -> None:
        """Test that default region is us-east-1."""
        with patch("boto3.client"):
            from src.modules.training.infrastructure.hyperpod.client import (
                HyperPodClient,
            )

            client = HyperPodClient()
            assert client._region == "us-east-1"

    # ==================== Cluster Context ====================

    def test_client_accepts_default_cluster_name(self) -> None:
        """Test that HyperPodClient accepts default_cluster_name parameter."""
        from src.modules.training.infrastructure.hyperpod.client import HyperPodClient

        client = HyperPodClient(default_cluster_name="my-cluster")
        assert client._default_cluster_name == "my-cluster"

    @pytest.mark.asyncio
    async def test_ensure_cluster_context_called_on_submit(
        self,
        mock_aioboto3_session: MagicMock,
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that _ensure_cluster_context is called when submitting job."""
        with patch("src.modules.training.infrastructure.hyperpod.client.set_cluster_context") as mock_set_context:
            from src.modules.training.infrastructure.hyperpod.client import (
                HyperPodClient,
            )

            # 清理类级别缓存，确保 set_cluster_context 会被调用
            HyperPodClient._cluster_contexts.clear()

            client = HyperPodClient()
            client._session = mock_aioboto3_session

            # Setup mock job
            mock_job = MagicMock()
            mock_job.status = None
            mock_hyperpod_pytorch_job.return_value = mock_job

            await client.submit_training_job(
                cluster_name="test-cluster",
                job_name="test-job",
                job_config={"image_uri": "test-image"},
            )

            mock_set_context.assert_called_once_with("test-cluster")

    @pytest.mark.asyncio
    async def test_ensure_cluster_context_called_on_get_status(
        self,
        mock_aioboto3_session: MagicMock,
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that _ensure_cluster_context is called when getting job status."""
        with patch("src.modules.training.infrastructure.hyperpod.client.set_cluster_context") as mock_set_context:
            from src.modules.training.infrastructure.hyperpod.client import (
                HyperPodClient,
            )

            # 清理类级别缓存，确保 set_cluster_context 会被调用
            HyperPodClient._cluster_contexts.clear()

            client = HyperPodClient()
            client._session = mock_aioboto3_session

            # Setup mock job with proper structure
            mock_job = self._create_mock_job_with_status("test-job", "Running")
            mock_hyperpod_pytorch_job.get.return_value = mock_job

            await client.get_training_job_status(
                cluster_name="test-cluster",
                job_name="test-job",
            )

            mock_set_context.assert_called_once_with("test-cluster")

    @pytest.mark.asyncio
    async def test_cluster_context_cached_across_calls(
        self,
        mock_aioboto3_session: MagicMock,
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that cluster context is only set once per cluster."""
        with patch("src.modules.training.infrastructure.hyperpod.client.set_cluster_context") as mock_set_context:
            from src.modules.training.infrastructure.hyperpod.client import (
                HyperPodClient,
            )

            # 清理类级别缓存
            HyperPodClient._cluster_contexts.clear()

            client = HyperPodClient()
            client._session = mock_aioboto3_session

            # Setup mock job
            mock_job = self._create_mock_job_with_status("test-job", "Running")
            mock_hyperpod_pytorch_job.get.return_value = mock_job

            # 多次调用，但同一集群
            await client.get_training_job_status("test-cluster", "job-1")
            await client.get_training_job_status("test-cluster", "job-2")
            await client.get_training_job_status("test-cluster", "job-3")

            # set_cluster_context 应该只被调用一次
            mock_set_context.assert_called_once_with("test-cluster")

    @pytest.mark.asyncio
    async def test_cluster_context_set_for_each_cluster(
        self,
        mock_aioboto3_session: MagicMock,
        mock_hyperpod_pytorch_job: MagicMock,
    ) -> None:
        """Test that cluster context is set separately for different clusters."""
        with patch("src.modules.training.infrastructure.hyperpod.client.set_cluster_context") as mock_set_context:
            from src.modules.training.infrastructure.hyperpod.client import (
                HyperPodClient,
            )

            # 清理类级别缓存
            HyperPodClient._cluster_contexts.clear()

            client = HyperPodClient()
            client._session = mock_aioboto3_session

            # Setup mock job
            mock_job = self._create_mock_job_with_status("test-job", "Running")
            mock_hyperpod_pytorch_job.get.return_value = mock_job

            # 调用不同集群
            await client.get_training_job_status("cluster-a", "job-1")
            await client.get_training_job_status("cluster-b", "job-2")

            # set_cluster_context 应该被调用两次
            assert mock_set_context.call_count == 2

    def test_ensure_cluster_context_uses_default_if_no_cluster_provided(self) -> None:
        """Test that default cluster is used if no cluster_name provided."""
        with patch("src.modules.training.infrastructure.hyperpod.client.set_cluster_context") as mock_set_context:
            from src.modules.training.infrastructure.hyperpod.client import (
                HyperPodClient,
            )

            # 清理类级别缓存
            HyperPodClient._cluster_contexts.clear()

            client = HyperPodClient(default_cluster_name="default-cluster")

            # 不传入 cluster_name
            client._ensure_cluster_context(None)

            mock_set_context.assert_called_once_with("default-cluster")
