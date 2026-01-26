"""训练任务构建辅助类"""

from typing import Any

from src.modules.training.domain.entities import TrainingJob
from src.modules.training.domain.value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
)
from src.modules.training.domain.value_objects.constants import (
    DEFAULT_CHECKPOINT_MOUNT_PATH,
    DEFAULT_DATA_MOUNT_PATH,
    DEFAULT_NODE_COUNT,
    DEFAULT_TASKS_PER_NODE,
)
from src.shared.utils import EnumMapper


class TrainingJobBuilder:
    """训练任务构建器 - 简化任务实体创建"""

    @staticmethod
    def build_from_dict(owner_id: int, data: dict[str, Any]) -> TrainingJob:
        """从字典构建训练任务实体

        Args:
            owner_id: 任务所有者 ID
            data: 任务配置数据

        Returns:
            TrainingJob: 训练任务实体
        """
        # 统一处理枚举转换
        distribution_strategy = EnumMapper.from_string(
            data.get("distribution_strategy", "DDP"),
            DistributionStrategy,
            DistributionStrategy.DDP,
        )
        priority = EnumMapper.from_string(
            data.get("priority", "MEDIUM"),
            JobPriority,
            JobPriority.MEDIUM,
        )

        return TrainingJob(
            id=0,
            job_name=data["job_name"],
            owner_id=owner_id,
            image_uri=data["image_uri"],
            instance_type=data["instance_type"],
            entrypoint_command=data["entrypoint_command"],
            display_name=data.get("display_name"),
            description=data.get("description"),
            node_count=data.get("node_count", DEFAULT_NODE_COUNT),
            tasks_per_node=data.get("tasks_per_node", DEFAULT_TASKS_PER_NODE),
            environment_variables=data.get("environment_variables"),
            dataset_id=data.get("dataset_id"),
            data_mount_path=data.get("data_mount_path", DEFAULT_DATA_MOUNT_PATH),
            checkpoint_mount_path=data.get("checkpoint_mount_path", DEFAULT_CHECKPOINT_MOUNT_PATH),
            checkpoint_interval=data.get("checkpoint_interval"),
            hyperparameters=data.get("hyperparameters"),
            max_epochs=data.get("max_epochs"),
            batch_size=data.get("batch_size"),
            learning_rate=data.get("learning_rate"),
            distribution_strategy=distribution_strategy,
            priority=priority,
            mixed_precision=data.get("mixed_precision", False),
            use_spot_instances=data.get("use_spot_instances", False),
            status=JobStatus.SUBMITTED,
        )

    @staticmethod
    def build_job_config(job: TrainingJob) -> dict[str, Any]:
        """构建 HyperPod 任务配置

        Args:
            job: 训练任务实体

        Returns:
            HyperPod 任务配置字典
        """
        return {
            "image_uri": job.image_uri,
            "instance_type": job.instance_type,
            "node_count": job.node_count,
            "tasks_per_node": job.tasks_per_node,
            "command": job.entrypoint_command,
            "environment": job.environment_variables,
            "gpu_count": TrainingJobBuilder.estimate_gpu_count(job.instance_type),
        }

    @staticmethod
    def estimate_gpu_count(instance_type: str) -> int:
        """估算实例类型的 GPU 数量

        Args:
            instance_type: AWS 实例类型

        Returns:
            GPU 数量
        """
        from src.modules.training.domain.value_objects.constants import GPU_INSTANCE_MAPPING

        return GPU_INSTANCE_MAPPING.get(instance_type, 1)
