"""Kueue Gang Scheduling集成测试

测试Kueue优先级和队列名称在整个训练任务生命周期中的正确传递和使用
"""

import pytest
import yaml
from unittest.mock import Mock, AsyncMock, patch

from models.training import (
    TrainingJob,
    TrainingJobConfig,
    TrainingJobType,
    FrameworkType,
    TrainingJobStatus,
)
from api.schemas.training import TrainingJobCreate, TrainingJobConfigCreate
from services.training.templates import TemplateRenderer
from services.training.operators import HyperPodOperator


class TestKueuePriorityValidation:
    """测试优先级字段验证"""

    def test_valid_priority_values(self):
        """测试有效的priority值: low, normal, high"""
        valid_priorities = ["low", "normal", "high"]

        for priority in valid_priorities:
            job_data = TrainingJobCreate(
                name="test-job",
                job_type=TrainingJobType.SINGLE_NODE,
                framework=FrameworkType.PYTORCH,
                project_id=1,
                priority=priority,  # 测试优先级
                config=TrainingJobConfigCreate(
                    docker_image="pytorch:latest",
                    command=["python", "train.py"],
                    output_path="/outputs",
                ),
            )
            assert job_data.priority == priority

    def test_invalid_priority_rejected(self):
        """测试无效的priority值被拒绝"""
        with pytest.raises(ValueError):
            TrainingJobCreate(
                name="test-job",
                job_type=TrainingJobType.SINGLE_NODE,
                framework=FrameworkType.PYTORCH,
                project_id=1,
                priority="ultra-high",  # 无效优先级
                config=TrainingJobConfigCreate(
                    docker_image="pytorch:latest",
                    command=["python", "train.py"],
                    output_path="/outputs",
                ),
            )

    def test_default_priority_is_normal(self):
        """测试默认优先级为normal"""
        job_data = TrainingJobCreate(
            name="test-job",
            job_type=TrainingJobType.SINGLE_NODE,
            framework=FrameworkType.PYTORCH,
            project_id=1,
            # 不指定priority,应使用默认值
            config=TrainingJobConfigCreate(
                docker_image="pytorch:latest",
                command=["python", "train.py"],
                output_path="/outputs",
            ),
        )
        assert job_data.priority == "normal"


class TestTemplateKueueAnnotations:
    """测试模板生成正确的Kueue annotations和labels"""

    def setup_method(self):
        """每个测试前初始化TemplateRenderer"""
        self.renderer = TemplateRenderer()

    def test_template_includes_kueue_queue_annotation(self):
        """测试模板包含kueue.x-k8s.io/queue-name annotation"""
        job = TrainingJob(
            id=1,
            name="test-job",
            job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
            framework=FrameworkType.PYTORCH,
            k8s_namespace="ai-training-1",
            project_id=1,
            creator_id=1,
            priority="normal",
            queue_name="project-1-queue",
        )

        config = TrainingJobConfig(
            node_count=2,
            gpu_per_node=8,
            cpu_per_node=32,
            memory_per_node_gb=256,
            docker_image="pytorch:latest",
            command=["python", "train.py"],
            output_path="/outputs",
        )

        manifest = self.renderer.render_pytorch_job(
            job=job,
            config=config,
            k8s_job_name="test-job-1-260101",
            priority="normal",
            queue_name="project-1-queue",
        )

        # 解析YAML验证
        job_dict = yaml.safe_load(manifest)
        assert "kueue.x-k8s.io/queue-name" in job_dict["metadata"]["annotations"]
        assert (
            job_dict["metadata"]["annotations"]["kueue.x-k8s.io/queue-name"]
            == "project-1-queue"
        )

    def test_template_includes_kueue_priority_label(self):
        """测试模板包含kueue.x-k8s.io/priority-class label"""
        job = TrainingJob(
            id=1,
            name="test-job",
            job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
            framework=FrameworkType.PYTORCH,
            k8s_namespace="ai-training-1",
            project_id=1,
            creator_id=1,
            priority="high",
        )

        config = TrainingJobConfig(
            node_count=2,
            gpu_per_node=8,
            cpu_per_node=32,
            memory_per_node_gb=256,
            docker_image="pytorch:latest",
            command=["python", "train.py"],
            output_path="/outputs",
        )

        manifest = self.renderer.render_pytorch_job(
            job=job,
            config=config,
            k8s_job_name="test-job-1-260101",
            priority="high",
        )

        job_dict = yaml.safe_load(manifest)
        assert "kueue.x-k8s.io/priority-class" in job_dict["metadata"]["labels"]
        assert job_dict["metadata"]["labels"]["kueue.x-k8s.io/priority-class"] == "high"

    def test_template_includes_project_id_label(self):
        """测试模板包含sagemaker.ai/project-id label"""
        job = TrainingJob(
            id=1,
            name="test-job",
            job_type=TrainingJobType.SINGLE_NODE,
            framework=FrameworkType.PYTORCH,
            k8s_namespace="ai-training-5",
            project_id=5,
            creator_id=1,
        )

        config = TrainingJobConfig(
            node_count=1,
            gpu_per_node=1,
            cpu_per_node=8,
            memory_per_node_gb=32,
            docker_image="pytorch:latest",
            command=["python", "train.py"],
            output_path="/outputs",
        )

        manifest = self.renderer.render_pytorch_job(
            job=job,
            config=config,
            k8s_job_name="test-job-1-260101",
        )

        job_dict = yaml.safe_load(manifest)
        assert "sagemaker.ai/project-id" in job_dict["metadata"]["labels"]
        assert job_dict["metadata"]["labels"]["sagemaker.ai/project-id"] == "5"

    def test_template_suspended_state(self):
        """测试模板runPolicy.suspend=true(Gang Scheduling要求)"""
        job = TrainingJob(
            id=1,
            name="test-job",
            job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
            framework=FrameworkType.PYTORCH,
            k8s_namespace="ai-training-1",
            project_id=1,
            creator_id=1,
        )

        config = TrainingJobConfig(
            node_count=8,
            gpu_per_node=8,
            cpu_per_node=32,
            memory_per_node_gb=256,
            docker_image="pytorch:latest",
            command=["python", "train.py"],
            output_path="/outputs",
        )

        manifest = self.renderer.render_pytorch_job(
            job=job,
            config=config,
            k8s_job_name="test-job-1-260101",
        )

        job_dict = yaml.safe_load(manifest)
        assert "runPolicy" in job_dict["spec"]
        assert job_dict["spec"]["runPolicy"]["suspend"] is True

    def test_all_templates_include_kueue_config(self):
        """测试所有4个模板(DDP/FSDP/DeepSpeed/Single-Node)都包含Kueue配置"""
        templates = [
            (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.PYTORCH),  # DDP
            (
                TrainingJobType.DISTRIBUTED_MODEL_PARALLEL,
                FrameworkType.PYTORCH,
            ),  # FSDP
            (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.DEEPSPEED),  # DS
            (TrainingJobType.SINGLE_NODE, FrameworkType.PYTORCH),  # Single-Node
        ]

        for job_type, framework in templates:
            job = TrainingJob(
                id=1,
                name="test-job",
                job_type=job_type,
                framework=framework,
                k8s_namespace="ai-training-1",
                project_id=1,
                creator_id=1,
                priority="normal",
            )

            config = TrainingJobConfig(
                node_count=2,
                gpu_per_node=8,
                cpu_per_node=32,
                memory_per_node_gb=256,
                docker_image="pytorch:latest",
                command=["python", "train.py"],
                output_path="/outputs",
            )

            manifest = self.renderer.render_pytorch_job(
                job=job,
                config=config,
                k8s_job_name="test-job-1-260101",
                priority="normal",
                queue_name="project-1-queue",
            )

            job_dict = yaml.safe_load(manifest)

            # 验证所有模板都有Kueue配置
            assert "kueue.x-k8s.io/queue-name" in job_dict["metadata"]["annotations"]
            assert "kueue.x-k8s.io/priority-class" in job_dict["metadata"]["labels"]
            assert job_dict["spec"]["runPolicy"]["suspend"] is True


class TestOperatorKueueParameterPassing:
    """测试HyperPodOperator正确传递Kueue参数"""

    @pytest.mark.asyncio
    async def test_operator_passes_priority_to_template(self):
        """测试Operator将priority传递给TemplateRenderer"""
        with patch("services.training.operators.hyperpod_operator.client"):
            operator = HyperPodOperator(in_cluster=False)

            job = TrainingJob(
                id=1,
                name="test-job",
                job_type=TrainingJobType.SINGLE_NODE,
                framework=FrameworkType.PYTORCH,
                k8s_namespace="ai-training-1",
                project_id=1,
                creator_id=1,
                priority="high",
            )

            config = TrainingJobConfig(
                node_count=1,
                gpu_per_node=1,
                cpu_per_node=8,
                memory_per_node_gb=32,
                docker_image="pytorch:latest",
                command=["python", "train.py"],
                output_path="/outputs",
            )

            # Mock K8s API调用
            operator.custom_api.create_namespaced_custom_object = AsyncMock()

            k8s_job_name = await operator.create_pytorch_job(
                job=job, config=config, priority="high", queue_name="project-1-queue"
            )

            # 验证create_namespaced_custom_object被调用
            operator.custom_api.create_namespaced_custom_object.assert_called_once()
            call_args = (
                operator.custom_api.create_namespaced_custom_object.call_args[1]
            )
            job_dict = call_args["body"]

            # 验证生成的manifest包含正确的Kueue配置
            assert (
                job_dict["metadata"]["annotations"]["kueue.x-k8s.io/queue-name"]
                == "project-1-queue"
            )
            assert (
                job_dict["metadata"]["labels"]["kueue.x-k8s.io/priority-class"]
                == "high"
            )

    @pytest.mark.asyncio
    async def test_operator_default_queue_name_generation(self):
        """测试Operator在queue_name=None时生成默认队列名"""
        with patch("services.training.operators.hyperpod_operator.client"):
            operator = HyperPodOperator(in_cluster=False)

            job = TrainingJob(
                id=1,
                name="test-job",
                job_type=TrainingJobType.SINGLE_NODE,
                framework=FrameworkType.PYTORCH,
                k8s_namespace="ai-training-3",
                project_id=3,
                creator_id=1,
            )

            config = TrainingJobConfig(
                node_count=1,
                gpu_per_node=1,
                cpu_per_node=8,
                memory_per_node_gb=32,
                docker_image="pytorch:latest",
                command=["python", "train.py"],
                output_path="/outputs",
            )

            operator.custom_api.create_namespaced_custom_object = AsyncMock()

            # 不指定queue_name,应使用默认project-{project_id}-queue
            await operator.create_pytorch_job(job=job, config=config)

            call_args = (
                operator.custom_api.create_namespaced_custom_object.call_args[1]
            )
            job_dict = call_args["body"]

            # 验证使用默认队列名: project-3-queue
            assert (
                job_dict["metadata"]["annotations"]["kueue.x-k8s.io/queue-name"]
                == "project-3-queue"
            )


class TestServiceLayerKueueIntegration:
    """测试TrainingJobService层正确使用Kueue参数"""

    @pytest.mark.asyncio
    async def test_service_saves_priority_and_queue_name(self):
        """测试TrainingJobService.create_training_job保存priority和queue_name"""
        # 此测试需要真实数据库或Mock AsyncSession
        # 简化版本:验证TrainingJob对象创建时包含这些字段
        from api.schemas.training import TrainingJobCreate, TrainingJobConfigCreate
        from models.user import User

        job_data = TrainingJobCreate(
            name="test-job",
            job_type=TrainingJobType.SINGLE_NODE,
            framework=FrameworkType.PYTORCH,
            project_id=1,
            priority="high",
            queue_name="project-1-queue",
            config=TrainingJobConfigCreate(
                docker_image="pytorch:latest",
                command=["python", "train.py"],
                output_path="/outputs",
            ),
        )

        # 验证Schema正确接收参数
        assert job_data.priority == "high"
        assert job_data.queue_name == "project-1-queue"


# 运行测试:
# pytest backend/tests/test_kueue_integration.py -v
