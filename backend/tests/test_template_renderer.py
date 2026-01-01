"""TemplateRenderer测试

测试训练任务模板渲染功能
"""

import pytest
import yaml
from pathlib import Path

from models.training import (
    FrameworkType,
    TrainingJob,
    TrainingJobConfig,
    TrainingJobType,
    TrainingJobStatus,
)
from services.training.templates import (
    TemplateRenderer,
    TemplateNotFoundError,
    TemplateRenderError,
)


class TestTemplateRenderer:
    """TemplateRenderer测试类"""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """获取模板目录"""
        return (
            Path(__file__).parent.parent
            / "src"
            / "services"
            / "training"
            / "templates"
        )

    @pytest.fixture
    def renderer(self, templates_dir: Path) -> TemplateRenderer:
        """创建TemplateRenderer实例"""
        return TemplateRenderer(templates_dir=templates_dir)

    @pytest.fixture
    def sample_job(self) -> TrainingJob:
        """创建示例训练任务"""
        job = TrainingJob(
            id=1,
            name="test-training-job",
            description="测试训练任务",
            status=TrainingJobStatus.PENDING,
            job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
            framework=FrameworkType.PYTORCH,
            project_id=1,
            creator_id=1,
            k8s_namespace="ai-training-platform",
        )
        return job

    @pytest.fixture
    def sample_config(self) -> TrainingJobConfig:
        """创建示例训练配置"""
        return TrainingJobConfig(
            node_count=2,
            gpu_per_node=8,
            cpu_per_node=64,
            memory_per_node_gb=512,
            gpu_type="p4d.24xlarge",
            docker_image="pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel",
            command=["python", "train.py"],
            args=["--epochs", "100", "--batch-size", "32"],
            env_vars={
                "NCCL_DEBUG": "INFO",
                "TORCH_DISTRIBUTED_DEBUG": "DETAIL",
            },
            dataset_path="/mnt/datasets/imagenet",
            output_path="/mnt/outputs/experiment-001",
            timeout_seconds=3600,
            max_retries=3,
        )

    def test_renderer_initialization(self, templates_dir: Path):
        """测试渲染器初始化"""
        renderer = TemplateRenderer(templates_dir=templates_dir)
        assert renderer.templates_dir == templates_dir
        assert renderer.jinja_env is not None

    def test_renderer_invalid_directory(self):
        """测试无效目录初始化"""
        with pytest.raises(Exception):  # TemplateRendererError
            TemplateRenderer(templates_dir=Path("/nonexistent/path"))

    def test_list_available_templates(self, renderer: TemplateRenderer):
        """测试列出可用模板"""
        templates = renderer.list_available_templates()
        assert len(templates) > 0
        assert "ddp-job-template.yaml" in templates
        assert "fsdp-job-template.yaml" in templates
        assert "deepspeed-job-template.yaml" in templates
        assert "single-node-template.yaml" in templates

    def test_validate_template_valid(self, renderer: TemplateRenderer):
        """测试验证有效模板"""
        assert renderer.validate_template("ddp-job-template.yaml") is True
        assert renderer.validate_template("fsdp-job-template.yaml") is True
        assert renderer.validate_template("deepspeed-job-template.yaml") is True
        assert renderer.validate_template("single-node-template.yaml") is True

    def test_validate_template_invalid(self, renderer: TemplateRenderer):
        """测试验证无效模板"""
        assert renderer.validate_template("nonexistent-template.yaml") is False

    def test_select_template_ddp(self, renderer: TemplateRenderer):
        """测试选择DDP模板"""
        template = renderer._select_template(
            TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.PYTORCH
        )
        assert template.name == "ddp-job-template.yaml"

    def test_select_template_fsdp(self, renderer: TemplateRenderer):
        """测试选择FSDP模板"""
        template = renderer._select_template(
            TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.PYTORCH
        )
        assert template.name == "fsdp-job-template.yaml"

    def test_select_template_deepspeed(self, renderer: TemplateRenderer):
        """测试选择DeepSpeed模板"""
        template = renderer._select_template(
            TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.DEEPSPEED
        )
        assert template.name == "deepspeed-job-template.yaml"

    def test_select_template_single_node(self, renderer: TemplateRenderer):
        """测试选择单节点模板"""
        template = renderer._select_template(
            TrainingJobType.SINGLE_NODE, FrameworkType.PYTORCH
        )
        assert template.name == "single-node-template.yaml"

    def test_render_ddp_job(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试渲染DDP任务"""
        sample_job.job_type = TrainingJobType.DISTRIBUTED_DATA_PARALLEL
        sample_job.framework = FrameworkType.PYTORCH

        rendered = renderer.render_pytorch_job(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-job-001",
        )

        # 验证渲染结果
        assert rendered is not None
        assert isinstance(rendered, str)
        assert "PyTorchJob" in rendered
        assert "test-job-001" in rendered
        assert "distributed-strategy: ddp" in rendered

        # 验证YAML有效性
        job_dict = yaml.safe_load(rendered)
        assert job_dict["kind"] == "PyTorchJob"
        assert job_dict["metadata"]["name"] == "test-job-001"
        assert (
            job_dict["metadata"]["labels"]["distributed-strategy"] == "ddp"
        )

    def test_render_fsdp_job(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试渲染FSDP任务"""
        sample_job.job_type = TrainingJobType.DISTRIBUTED_MODEL_PARALLEL
        sample_job.framework = FrameworkType.PYTORCH

        rendered = renderer.render_pytorch_job(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-fsdp-job",
        )

        assert "distributed-strategy: fsdp" in rendered
        assert "FSDP_SHARDING_STRATEGY" in rendered
        assert "FSDP_CPU_OFFLOAD" in rendered

        # 验证YAML
        job_dict = yaml.safe_load(rendered)
        assert job_dict["metadata"]["labels"]["distributed-strategy"] == "fsdp"

    def test_render_deepspeed_job(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试渲染DeepSpeed任务"""
        sample_job.job_type = TrainingJobType.DISTRIBUTED_DATA_PARALLEL
        sample_job.framework = FrameworkType.DEEPSPEED

        rendered = renderer.render_pytorch_job(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-deepspeed-job",
        )

        assert "distributed-strategy: deepspeed" in rendered
        assert "ZERO_STAGE" in rendered
        assert "DEEPSPEED_CONFIG" in rendered
        assert "deepspeed_config.json" in rendered

        # 验证YAML(包含ConfigMap)
        docs = list(yaml.safe_load_all(rendered))
        assert len(docs) == 2  # PyTorchJob + ConfigMap
        assert docs[0]["kind"] == "PyTorchJob"
        assert docs[1]["kind"] == "ConfigMap"
        assert "deepspeed_config.json" in docs[1]["data"]

    def test_render_single_node_job(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试渲染单节点任务"""
        sample_job.job_type = TrainingJobType.SINGLE_NODE
        sample_job.framework = FrameworkType.PYTORCH
        sample_config.node_count = 1

        rendered = renderer.render_pytorch_job(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-single-node",
        )

        assert "distributed-strategy: single-node" in rendered
        # 单节点不应该有Worker replicas
        assert "Worker:" not in rendered or "replicas: 0" in rendered

        # 验证YAML
        job_dict = yaml.safe_load(rendered)
        assert (
            job_dict["metadata"]["labels"]["distributed-strategy"]
            == "single-node"
        )

    def test_prepare_template_vars(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试准备模板变量"""
        vars = renderer._prepare_template_vars(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-job",
        )

        # 验证基础变量
        assert vars["job_name"] == "test-job"
        assert vars["namespace"] == "ai-training-platform"
        assert vars["node_count"] == 2
        assert vars["gpu_per_node"] == 8
        assert vars["world_size"] == 16  # 2 * 8

        # 验证资源配置
        assert vars["docker_image"] == sample_config.docker_image
        assert vars["command"] == sample_config.command
        assert vars["args"] == sample_config.args

        # 验证环境变量
        assert vars["env_vars"]["NCCL_DEBUG"] == "INFO"

    def test_deepspeed_specific_vars(
        self, renderer: TemplateRenderer, sample_config: TrainingJobConfig
    ):
        """测试DeepSpeed特定变量"""
        sample_config.env_vars = {
            "ZERO_STAGE": "3",
            "OFFLOAD_OPTIMIZER": "True",
            "FP16_ENABLED": "True",
        }

        vars = renderer._get_deepspeed_vars(sample_config)

        assert vars["zero_stage"] == "3"
        assert vars["offload_optimizer"] == "True"
        assert vars["fp16_enabled"] == "True"
        assert "bf16_enabled" in vars

    def test_fsdp_specific_vars(
        self, renderer: TemplateRenderer, sample_config: TrainingJobConfig
    ):
        """测试FSDP特定变量"""
        sample_config.env_vars = {
            "FSDP_SHARDING_STRATEGY": "HYBRID_SHARD",
            "FSDP_CPU_OFFLOAD": "True",
            "FSDP_MIXED_PRECISION": "fp16",
        }

        vars = renderer._get_fsdp_vars(sample_config)

        assert vars["fsdp_sharding_strategy"] == "HYBRID_SHARD"
        assert vars["fsdp_cpu_offload"] == "True"
        assert vars["fsdp_mixed_precision"] == "fp16"

    def test_render_with_custom_env_vars(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试自定义环境变量渲染"""
        sample_config.env_vars = {
            "CUSTOM_VAR_1": "value1",
            "CUSTOM_VAR_2": "value2",
            "NCCL_DEBUG": "WARN",
        }

        rendered = renderer.render_pytorch_job(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-custom-env",
        )

        assert "CUSTOM_VAR_1" in rendered
        assert "value1" in rendered
        assert "CUSTOM_VAR_2" in rendered
        assert "value2" in rendered

    def test_render_multi_node_job(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试多节点任务渲染"""
        sample_config.node_count = 4

        rendered = renderer.render_pytorch_job(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-multi-node",
        )

        # 验证Worker副本数
        job_dict = yaml.safe_load(rendered)
        worker_replicas = job_dict["spec"]["pytorchReplicaSpecs"]["Worker"][
            "replicas"
        ]
        assert worker_replicas == 3  # node_count - 1

    def test_pvc_name_mapping(self, renderer: TemplateRenderer):
        """测试PVC名称映射"""
        # S3路径
        assert "s3" in renderer._get_dataset_pvc_name("s3://bucket/data")

        # FSx路径
        assert "fsx" in renderer._get_dataset_pvc_name("fsx://volume/data")

        # 默认路径
        assert "fsx" in renderer._get_dataset_pvc_name("/local/path")

        # 输出PVC
        assert "s3" in renderer._get_output_pvc_name("s3://bucket/output")

    def test_render_with_no_dataset(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试无数据集路径的渲染"""
        sample_config.dataset_path = None

        rendered = renderer.render_pytorch_job(
            job=sample_job,
            config=sample_config,
            k8s_job_name="test-no-dataset",
        )

        # 验证没有数据集卷挂载
        job_dict = yaml.safe_load(rendered)
        master_volumes = job_dict["spec"]["pytorchReplicaSpecs"]["Master"][
            "template"
        ]["spec"]["volumes"]

        dataset_volumes = [v for v in master_volumes if v["name"] == "dataset"]
        assert len(dataset_volumes) == 0

    def test_error_handling_invalid_template(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试错误处理 - 无效模板"""
        # 修改映射使其指向不存在的模板
        original_mapping = renderer.TEMPLATE_MAPPING.copy()
        renderer.TEMPLATE_MAPPING = {
            (sample_job.job_type, sample_job.framework): "nonexistent.yaml"
        }

        try:
            with pytest.raises(TemplateNotFoundError):
                renderer.render_pytorch_job(
                    job=sample_job,
                    config=sample_config,
                    k8s_job_name="test-error",
                )
        finally:
            # 恢复原始映射
            renderer.TEMPLATE_MAPPING = original_mapping

    def test_yaml_validity_all_templates(
        self,
        renderer: TemplateRenderer,
        sample_job: TrainingJob,
        sample_config: TrainingJobConfig,
    ):
        """测试所有模板的YAML有效性"""
        test_cases = [
            (
                TrainingJobType.SINGLE_NODE,
                FrameworkType.PYTORCH,
                "single-node",
            ),
            (
                TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
                FrameworkType.PYTORCH,
                "ddp",
            ),
            (
                TrainingJobType.DISTRIBUTED_MODEL_PARALLEL,
                FrameworkType.PYTORCH,
                "fsdp",
            ),
            (
                TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
                FrameworkType.DEEPSPEED,
                "deepspeed",
            ),
        ]

        for job_type, framework, strategy in test_cases:
            sample_job.job_type = job_type
            sample_job.framework = framework

            rendered = renderer.render_pytorch_job(
                job=sample_job,
                config=sample_config,
                k8s_job_name=f"test-{strategy}",
            )

            # 验证YAML可解析
            if strategy == "deepspeed":
                docs = list(yaml.safe_load_all(rendered))
                assert len(docs) >= 1
            else:
                job_dict = yaml.safe_load(rendered)
                assert job_dict["kind"] == "PyTorchJob"


# 运行测试: pytest tests/test_template_renderer.py -v
