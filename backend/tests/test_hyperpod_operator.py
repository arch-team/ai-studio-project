"""HyperPod Operator单元测试

测试HyperPodOperator的核心功能(需要Mock K8s API)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from services.training.operators import (
    HyperPodOperator,
    JobCreationError,
    JobNotFoundError,
)
from models.training import (
    TrainingJob,
    TrainingJobConfig,
    TrainingJobStatus,
    TrainingJobType,
    FrameworkType,
)


@pytest.fixture
def mock_k8s_config():
    """Mock Kubernetes配置"""
    with patch("kubernetes.config.load_kube_config") as mock_config:
        yield mock_config


@pytest.fixture
def mock_custom_api():
    """Mock Kubernetes CustomObjectsApi"""
    with patch("kubernetes.client.CustomObjectsApi") as mock_api:
        mock_instance = MagicMock()
        mock_api.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_core_api():
    """Mock Kubernetes CoreV1Api"""
    with patch("kubernetes.client.CoreV1Api") as mock_api:
        mock_instance = MagicMock()
        mock_api.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_training_job():
    """示例训练任务"""
    job = TrainingJob(
        id=1,
        name="test-pytorch-training",
        description="测试训练任务",
        status=TrainingJobStatus.PENDING,
        job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
        framework=FrameworkType.PYTORCH,
        project_id=1,
        creator_id=1,
        k8s_namespace="ai-training-project-1",
    )
    return job


@pytest.fixture
def sample_job_config():
    """示例训练配置"""
    config = TrainingJobConfig(
        job_id=1,
        node_count=2,
        gpu_per_node=8,
        cpu_per_node=96,
        memory_per_node_gb=512,
        gpu_type="ml.p4d.24xlarge",
        docker_image="pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel",
        command=["python", "-m", "torch.distributed.launch"],
        args=["train.py", "--epochs", "100"],
        env_vars={"NCCL_DEBUG": "INFO"},
        dataset_path="/fsx/datasets/imagenet",
        output_path="/fsx/outputs/model-1",
        hyperparameters={"learning_rate": 0.001, "batch_size": 256},
        timeout_seconds=86400,
        max_retries=3,
    )
    return config


class TestHyperPodOperatorInitialization:
    """测试Operator初始化"""

    def test_init_with_kubeconfig(self, mock_k8s_config, mock_custom_api, mock_core_api):
        """测试使用kubeconfig初始化"""
        operator = HyperPodOperator(
            kubeconfig_path="/path/to/kubeconfig",
            in_cluster=False,
        )

        assert operator is not None
        assert operator.kubeconfig_path == "/path/to/kubeconfig"
        assert operator.in_cluster is False
        mock_k8s_config.assert_called_once()

    def test_init_in_cluster(self, mock_custom_api, mock_core_api):
        """测试集群内初始化"""
        with patch("kubernetes.config.load_incluster_config") as mock_incluster:
            operator = HyperPodOperator(in_cluster=True)

            assert operator is not None
            assert operator.in_cluster is True
            mock_incluster.assert_called_once()


class TestJobCreation:
    """测试Job创建"""

    @pytest.mark.asyncio
    async def test_create_pytorch_job_success(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
        sample_training_job,
        sample_job_config,
    ):
        """测试成功创建PyTorchJob"""
        # Mock成功创建
        mock_custom_api.create_namespaced_custom_object = AsyncMock(
            return_value={"metadata": {"name": "test-job-1-123456"}}
        )

        operator = HyperPodOperator()
        job_name = await operator.create_pytorch_job(
            job=sample_training_job,
            config=sample_job_config,
        )

        assert job_name is not None
        assert "test-pytorch-training" in job_name
        assert str(sample_training_job.id) in job_name

    @pytest.mark.asyncio
    async def test_create_job_api_error(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
        sample_training_job,
        sample_job_config,
    ):
        """测试API错误处理"""
        from kubernetes.client.exceptions import ApiException

        # Mock API错误
        mock_custom_api.create_namespaced_custom_object = AsyncMock(
            side_effect=ApiException(status=403, reason="Forbidden")
        )

        operator = HyperPodOperator()
        with pytest.raises(JobCreationError):
            await operator.create_pytorch_job(
                job=sample_training_job,
                config=sample_job_config,
            )


class TestJobStatus:
    """测试状态查询"""

    @pytest.mark.asyncio
    async def test_get_job_status_running(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
    ):
        """测试查询运行中的Job"""
        # Mock K8s响应
        mock_response = {
            "status": {
                "conditions": [
                    {
                        "type": "Running",
                        "status": "True",
                        "message": "Training is running",
                        "reason": "JobRunning",
                    }
                ],
                "replicaStatuses": {
                    "Master": {"active": 1},
                    "Worker": {"active": 1},
                },
                "startTime": "2024-01-01T00:00:00Z",
            }
        }
        mock_custom_api.get_namespaced_custom_object = AsyncMock(
            return_value=mock_response
        )

        operator = HyperPodOperator()
        status = await operator.get_job_status(
            job_name="test-job",
            namespace="test-ns",
        )

        assert status["status"] == TrainingJobStatus.RUNNING
        assert status["replica_statuses"]["Master"]["active"] == 1

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
    ):
        """测试Job不存在"""
        from kubernetes.client.exceptions import ApiException

        mock_custom_api.get_namespaced_custom_object = AsyncMock(
            side_effect=ApiException(status=404, reason="Not Found")
        )

        operator = HyperPodOperator()
        with pytest.raises(JobNotFoundError):
            await operator.get_job_status(
                job_name="non-existent-job",
                namespace="test-ns",
            )


class TestJobDeletion:
    """测试Job删除"""

    @pytest.mark.asyncio
    async def test_delete_job_success(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
    ):
        """测试成功删除Job"""
        mock_custom_api.delete_namespaced_custom_object = AsyncMock(
            return_value={}
        )

        operator = HyperPodOperator()
        result = await operator.delete_job(
            job_name="test-job",
            namespace="test-ns",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_job_not_found(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
    ):
        """测试删除不存在的Job"""
        from kubernetes.client.exceptions import ApiException

        mock_custom_api.delete_namespaced_custom_object = AsyncMock(
            side_effect=ApiException(status=404, reason="Not Found")
        )

        operator = HyperPodOperator()
        with pytest.raises(JobNotFoundError):
            await operator.delete_job(
                job_name="non-existent-job",
                namespace="test-ns",
            )


class TestJobNameGeneration:
    """测试Job名称生成"""

    def test_generate_job_name_format(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
        sample_training_job,
    ):
        """测试生成的Job名称格式"""
        operator = HyperPodOperator()
        job_name = operator._generate_job_name(sample_training_job)

        # 验证格式: prefix-id-timestamp
        assert "test-pytorch-training" in job_name
        assert str(sample_training_job.id) in job_name
        # 验证符合DNS-1123规范
        assert len(job_name) <= 63
        assert job_name.islower() or "-" in job_name

    def test_generate_job_name_uniqueness(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
        sample_training_job,
    ):
        """测试名称唯一性"""
        operator = HyperPodOperator()

        name1 = operator._generate_job_name(sample_training_job)
        # 模拟时间流逝
        import time

        time.sleep(1)
        name2 = operator._generate_job_name(sample_training_job)

        assert name1 != name2  # 时间戳不同


class TestTemplateRendering:
    """测试模板渲染"""

    def test_render_job_manifest(
        self,
        mock_k8s_config,
        mock_custom_api,
        mock_core_api,
        sample_training_job,
        sample_job_config,
    ):
        """测试YAML清单渲染"""
        operator = HyperPodOperator()
        manifest = operator._render_job_manifest(
            job=sample_training_job,
            config=sample_job_config,
            k8s_job_name="test-job-1-123456",
        )

        # 验证关键字段存在
        assert "test-job-1-123456" in manifest
        assert "ai-training-project-1" in manifest
        assert "pytorch/pytorch:2.1.0" in manifest
        assert "ml.p4d.24xlarge" in manifest
        assert "train.py" in manifest


# 集成测试(需要真实的K8s环境)
@pytest.mark.integration
@pytest.mark.skip(reason="需要真实的K8s集群")
class TestHyperPodOperatorIntegration:
    """集成测试(需要K8s集群)"""

    @pytest.mark.asyncio
    async def test_full_job_lifecycle(
        self,
        sample_training_job,
        sample_job_config,
    ):
        """测试完整的Job生命周期"""
        operator = HyperPodOperator()

        # 1. 创建Job
        job_name = await operator.create_pytorch_job(
            job=sample_training_job,
            config=sample_job_config,
        )
        assert job_name is not None

        # 2. 查询状态
        status = await operator.get_job_status(
            job_name=job_name,
            namespace=sample_training_job.k8s_namespace,
        )
        assert status["status"] in [
            TrainingJobStatus.QUEUED,
            TrainingJobStatus.RUNNING,
        ]

        # 3. 获取Pod列表
        pods = await operator.get_pod_list(
            job_name=job_name,
            namespace=sample_training_job.k8s_namespace,
        )
        assert len(pods) > 0

        # 4. 删除Job
        result = await operator.delete_job(
            job_name=job_name,
            namespace=sample_training_job.k8s_namespace,
        )
        assert result is True
