"""训练任务模板渲染器

负责根据任务类型和框架选择合适的K8s模板并渲染
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from models.training import (
    FrameworkType,
    TrainingJob,
    TrainingJobConfig,
    TrainingJobType,
)

logger = logging.getLogger(__name__)


class TemplateRendererError(Exception):
    """模板渲染异常基类"""

    pass


class TemplateNotFoundError(TemplateRendererError):
    """模板文件不存在异常"""

    pass


class TemplateRenderError(TemplateRendererError):
    """模板渲染失败异常"""

    pass


class TemplateRenderer:
    """训练任务模板渲染器

    根据TrainingJobType和FrameworkType智能选择模板,
    渲染生成Kubernetes PyTorchJob资源定义
    """

    # 模板选择映射规则
    TEMPLATE_MAPPING = {
        # 单节点训练 - 所有框架使用简化模板
        (TrainingJobType.SINGLE_NODE, FrameworkType.PYTORCH): "single-node-template.yaml",
        (TrainingJobType.SINGLE_NODE, FrameworkType.TENSORFLOW): "single-node-template.yaml",
        (TrainingJobType.SINGLE_NODE, FrameworkType.JFLUX): "single-node-template.yaml",
        (TrainingJobType.SINGLE_NODE, FrameworkType.DEEPSPEED): "single-node-template.yaml",
        (TrainingJobType.SINGLE_NODE, FrameworkType.MEGATRON): "single-node-template.yaml",
        # 数据并行 - 根据框架选择
        (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.PYTORCH): "ddp-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.DEEPSPEED): "deepspeed-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.TENSORFLOW): "ddp-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.JFLUX): "ddp-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.MEGATRON): "ddp-job-template.yaml",
        # 模型并行 - 使用FSDP或DeepSpeed
        (TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.PYTORCH): "fsdp-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.DEEPSPEED): "deepspeed-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.TENSORFLOW): "fsdp-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.JFLUX): "fsdp-job-template.yaml",
        (TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.MEGATRON): "fsdp-job-template.yaml",
        # 混合并行 - 优先使用DeepSpeed或FSDP
        (TrainingJobType.HYBRID_PARALLEL, FrameworkType.PYTORCH): "fsdp-job-template.yaml",
        (TrainingJobType.HYBRID_PARALLEL, FrameworkType.DEEPSPEED): "deepspeed-job-template.yaml",
        (TrainingJobType.HYBRID_PARALLEL, FrameworkType.TENSORFLOW): "fsdp-job-template.yaml",
        (TrainingJobType.HYBRID_PARALLEL, FrameworkType.JFLUX): "fsdp-job-template.yaml",
        (TrainingJobType.HYBRID_PARALLEL, FrameworkType.MEGATRON): "deepspeed-job-template.yaml",
    }

    def __init__(self, templates_dir: Path | None = None):
        """初始化模板渲染器

        Args:
            templates_dir: 模板文件目录,默认为当前文件同级目录
        """
        if templates_dir is None:
            # 默认使用当前文件同级目录
            templates_dir = Path(__file__).parent

        self.templates_dir = templates_dir

        # 验证模板目录存在
        if not self.templates_dir.exists():
            raise TemplateRendererError(
                f"模板目录不存在: {self.templates_dir}"
            )

        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(f"模板渲染器初始化成功,模板目录: {self.templates_dir}")

    def render_pytorch_job(
        self,
        job: TrainingJob,
        config: TrainingJobConfig,
        k8s_job_name: str,
        priority: str = "normal",
        queue_name: str | None = None,
    ) -> str:
        """渲染PyTorchJob YAML清单

        Args:
            job: 训练任务对象
            config: 训练任务配置
            k8s_job_name: K8s Job名称
            priority: Kueue优先级(low/normal/high),默认normal
            queue_name: Kueue LocalQueue名称,默认使用项目队列

        Returns:
            渲染后的YAML字符串

        Raises:
            TemplateNotFoundError: 模板文件不存在
            TemplateRenderError: 模板渲染失败
        """
        try:
            # 确定queue_name (如果未指定,使用项目级别队列)
            if queue_name is None:
                queue_name = f"project-{job.project_id}-queue"

            # 选择模板
            template = self._select_template(job.job_type, job.framework)

            # 准备模板变量
            template_vars = self._prepare_template_vars(
                job=job,
                config=config,
                k8s_job_name=k8s_job_name,
                priority=priority,
                queue_name=queue_name,
            )

            # 渲染模板
            rendered = template.render(**template_vars)

            logger.info(
                f"模板渲染成功: job_type={job.job_type.value}, "
                f"framework={job.framework.value}, template={template.name}, "
                f"priority={priority}, queue={queue_name}"
            )

            return rendered

        except TemplateNotFound as e:
            error_msg = (
                f"模板文件不存在: {e.name} "
                f"(job_type={job.job_type.value}, framework={job.framework.value})"
            )
            logger.error(error_msg)
            raise TemplateNotFoundError(error_msg) from e

        except Exception as e:
            error_msg = f"模板渲染失败: {str(e)}"
            logger.error(error_msg)
            raise TemplateRenderError(error_msg) from e

    def _select_template(
        self,
        job_type: TrainingJobType,
        framework: FrameworkType,
    ) -> Template:
        """选择合适的模板

        Args:
            job_type: 训练任务类型
            framework: 训练框架类型

        Returns:
            Jinja2模板对象

        Raises:
            TemplateNotFoundError: 未找到匹配的模板
        """
        # 查找映射表
        template_key = (job_type, framework)
        template_name = self.TEMPLATE_MAPPING.get(template_key)

        if not template_name:
            # 如果没有精确匹配,使用默认模板
            logger.warning(
                f"未找到精确模板映射: job_type={job_type.value}, "
                f"framework={framework.value}, 使用默认DDP模板"
            )
            template_name = "ddp-job-template.yaml"

        # 加载模板
        try:
            template = self.jinja_env.get_template(template_name)
            logger.debug(f"选择模板: {template_name}")
            return template

        except TemplateNotFound:
            raise TemplateNotFoundError(
                f"模板文件不存在: {template_name} "
                f"(templates_dir={self.templates_dir})"
            )

    def _prepare_template_vars(
        self,
        job: TrainingJob,
        config: TrainingJobConfig,
        k8s_job_name: str,
        priority: str = "normal",
        queue_name: str | None = None,
    ) -> dict[str, Any]:
        """准备模板变量

        Args:
            job: 训练任务对象
            config: 训练任务配置
            k8s_job_name: K8s Job名称
            priority: Kueue优先级
            queue_name: Kueue队列名称

        Returns:
            模板变量字典
        """
        # 基础变量
        template_vars = {
            # 基本信息
            "job_name": k8s_job_name,
            "namespace": job.k8s_namespace,
            "job_id": str(job.id),
            "job_type": job.job_type.value,
            "project_id": str(job.project_id),
            # Kueue Gang Scheduling支持
            "priority": priority,
            "queue_name": queue_name or f"project-{job.project_id}-queue",
            "suspend": True,  # Gang Scheduling要求初始suspended,等待Kueue调度
            # 资源配置
            "node_count": config.node_count,
            "gpu_per_node": config.gpu_per_node,
            "cpu_per_node": config.cpu_per_node,
            "memory_per_node_gb": config.memory_per_node_gb,
            "gpu_type": config.gpu_type,
            "world_size": config.node_count * config.gpu_per_node,
            # 训练配置
            "docker_image": config.docker_image,
            "command": config.command,
            "args": config.args or [],
            "env_vars": config.env_vars or {},
            # 数据路径
            "dataset_path": config.dataset_path,
            "dataset_pvc": self._get_dataset_pvc_name(config.dataset_path),
            "output_path": config.output_path,
            "output_pvc": self._get_output_pvc_name(config.output_path),
            # 超时和重试
            "timeout_seconds": config.timeout_seconds,
            "max_retries": config.max_retries,
        }

        # 添加框架特定变量
        if job.framework == FrameworkType.DEEPSPEED:
            template_vars.update(self._get_deepspeed_vars(config))
        elif job.job_type in [
            TrainingJobType.DISTRIBUTED_MODEL_PARALLEL,
            TrainingJobType.HYBRID_PARALLEL,
        ]:
            # FSDP配置
            template_vars.update(self._get_fsdp_vars(config))

        return template_vars

    def _get_deepspeed_vars(self, config: TrainingJobConfig) -> dict[str, Any]:
        """获取DeepSpeed特定变量

        Args:
            config: 训练任务配置

        Returns:
            DeepSpeed配置变量
        """
        # 从环境变量或默认值提取DeepSpeed配置
        env_vars = config.env_vars or {}

        return {
            "zero_stage": env_vars.get("ZERO_STAGE", "2"),
            "offload_optimizer": env_vars.get("OFFLOAD_OPTIMIZER", "False"),
            "offload_param": env_vars.get("OFFLOAD_PARAM", "False"),
            "gradient_accumulation_steps": env_vars.get(
                "GRADIENT_ACCUMULATION_STEPS", "1"
            ),
            "gradient_clipping": env_vars.get("GRADIENT_CLIPPING", "1.0"),
            "fp16_enabled": env_vars.get("FP16_ENABLED", "False"),
            "bf16_enabled": env_vars.get("BF16_ENABLED", "True"),
            "loss_scale": env_vars.get("LOSS_SCALE", "0"),
            "deepspeed_config_path": env_vars.get(
                "DEEPSPEED_CONFIG", "/mnt/config/deepspeed_config.json"
            ),
            "train_batch_size": env_vars.get("TRAIN_BATCH_SIZE", "32"),
            "micro_batch_size": env_vars.get("MICRO_BATCH_SIZE", "1"),
            "learning_rate": env_vars.get("LEARNING_RATE", "3e-4"),
        }

    def _get_fsdp_vars(self, config: TrainingJobConfig) -> dict[str, Any]:
        """获取FSDP特定变量

        Args:
            config: 训练任务配置

        Returns:
            FSDP配置变量
        """
        env_vars = config.env_vars or {}

        return {
            "fsdp_sharding_strategy": env_vars.get(
                "FSDP_SHARDING_STRATEGY", "FULL_SHARD"
            ),
            "fsdp_cpu_offload": env_vars.get("FSDP_CPU_OFFLOAD", "False"),
            "fsdp_backward_prefetch": env_vars.get(
                "FSDP_BACKWARD_PREFETCH", "BACKWARD_PRE"
            ),
            "fsdp_auto_wrap_policy": env_vars.get(
                "FSDP_AUTO_WRAP_POLICY", "transformer"
            ),
            "fsdp_use_orig_params": env_vars.get("FSDP_USE_ORIG_PARAMS", "True"),
            "fsdp_sync_module_states": env_vars.get(
                "FSDP_SYNC_MODULE_STATES", "True"
            ),
            "fsdp_mixed_precision": env_vars.get("FSDP_MIXED_PRECISION", "bf16"),
            "fsdp_activation_checkpointing": env_vars.get(
                "FSDP_ACTIVATION_CHECKPOINTING", "True"
            ),
        }

    def _get_dataset_pvc_name(self, dataset_path: str | None) -> str:
        """获取数据集PVC名称

        Args:
            dataset_path: 数据集路径

        Returns:
            PVC名称
        """
        # TODO: 实现PVC映射逻辑(根据路径查找对应的PVC)
        # 临时方案: 使用默认PVC
        if not dataset_path:
            return "fsx-datasets"

        # 简单路径解析(实际应该查询数据库或配置)
        if "s3://" in dataset_path:
            return "s3-datasets"
        elif "fsx://" in dataset_path:
            return "fsx-datasets"
        else:
            return "fsx-datasets"

    def _get_output_pvc_name(self, output_path: str) -> str:
        """获取输出PVC名称

        Args:
            output_path: 输出路径

        Returns:
            PVC名称
        """
        # TODO: 实现PVC映射逻辑
        # 临时方案: 使用默认PVC
        if "s3://" in output_path:
            return "s3-outputs"
        elif "fsx://" in output_path:
            return "fsx-outputs"
        else:
            return "fsx-outputs"

    def list_available_templates(self) -> list[str]:
        """列出所有可用的模板

        Returns:
            模板文件名列表
        """
        templates = []
        for template_file in self.templates_dir.glob("*.yaml"):
            if template_file.name != "__init__.py":
                templates.append(template_file.name)

        logger.debug(f"可用模板: {templates}")
        return templates

    def validate_template(self, template_name: str) -> bool:
        """验证模板是否存在且有效

        Args:
            template_name: 模板文件名

        Returns:
            是否有效
        """
        try:
            template = self.jinja_env.get_template(template_name)
            # 尝试简单渲染测试
            template.render(
                job_name="test",
                namespace="default",
                job_id="test-id",
                job_type="SINGLE_NODE",
                node_count=1,
                gpu_per_node=1,
                cpu_per_node=4,
                memory_per_node_gb=32,
                world_size=1,
                docker_image="pytorch:latest",
                command=["python", "train.py"],
                args=[],
                env_vars={},
                dataset_path=None,
                dataset_pvc="fsx-datasets",
                output_path="/outputs",
                output_pvc="fsx-outputs",
                timeout_seconds=3600,
                max_retries=3,
            )
            return True
        except Exception as e:
            logger.error(f"模板验证失败: {template_name}, 错误: {e}")
            return False


__all__ = [
    "TemplateRenderer",
    "TemplateRendererError",
    "TemplateNotFoundError",
    "TemplateRenderError",
]
