"""Training Job Service - Business logic for training job management."""

from datetime import datetime

from src.modules.training.application.interfaces import IHyperPodClient
from src.modules.training.domain.entities import TrainingJob
from src.modules.training.domain.exceptions import TrainingJobNotFoundError
from src.modules.training.domain.repositories import ITrainingJobRepository
from src.modules.training.domain.value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
)
from src.shared.application.enhanced_base_service import EnhancedBaseService
from src.shared.domain.exceptions import (
    DuplicateEntityError,
    InvalidStateTransitionError,
)


class TrainingJobService(EnhancedBaseService[TrainingJob, int]):
    """Service for managing training jobs."""

    def __init__(
        self,
        repository: ITrainingJobRepository,
        hyperpod_client: IHyperPodClient,
        cluster_name: str = "default-cluster",
    ):
        super().__init__(repository, "TrainingJob")
        self._not_found_error_factory = TrainingJobNotFoundError
        self._hyperpod_client = hyperpod_client
        self._cluster_name = cluster_name

    async def create_job(self, owner_id: int, data: dict) -> TrainingJob:
        """Create a new training job."""
        job_name = data["job_name"]

        # Use base class method for unique field validation
        await self._validate_unique_field("name", job_name)

        # Create domain entity
        job = self._build_training_job(owner_id, data)

        # Submit to HyperPod
        await self._submit_to_hyperpod(job)

        # Save to database
        return await self._repository.create(job)

    def _build_training_job(self, owner_id: int, data: dict) -> TrainingJob:
        """构建训练任务实体

        Args:
            owner_id: 任务所有者 ID
            data: 任务配置数据

        Returns:
            TrainingJob: 训练任务实体
        """
        # 使用 EnumMapper 统一处理枚举转换
        from src.shared.utils import EnumMapper

        distribution_strategy = EnumMapper.from_string(
            data.get("distribution_strategy", "DDP"),
            DistributionStrategy,
            DistributionStrategy.DDP
        )
        priority = EnumMapper.from_string(
            data.get("priority", "MEDIUM"),
            JobPriority,
            JobPriority.MEDIUM
        )

        # 提取默认值常量
        DEFAULT_NODE_COUNT = 1
        DEFAULT_TASKS_PER_NODE = 1
        DEFAULT_DATA_MOUNT = "/data"
        DEFAULT_CHECKPOINT_MOUNT = "/checkpoints"

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
            data_mount_path=data.get("data_mount_path", DEFAULT_DATA_MOUNT),
            checkpoint_mount_path=data.get("checkpoint_mount_path", DEFAULT_CHECKPOINT_MOUNT),
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

    async def _submit_to_hyperpod(self, job: TrainingJob) -> None:
        """提交任务到 HyperPod

        Args:
            job: 训练任务实体
        """
        job_config = self._build_job_config(job)
        await self._hyperpod_client.submit_training_job(
            cluster_name=self._cluster_name,
            job_name=job.job_name,
            job_config=job_config,
        )

    def _build_job_config(self, job: TrainingJob) -> dict:
        """构建 HyperPod 任务配置"""
        return {
            "image_uri": job.image_uri,
            "instance_type": job.instance_type,
            "node_count": job.node_count,
            "tasks_per_node": job.tasks_per_node,
            "command": job.entrypoint_command,
            "environment": job.environment_variables,
        }

    async def get_job(self, job_id: int) -> TrainingJob:
        """Get training job by ID."""
        return await self._get_or_raise(job_id)

    async def list_jobs(
        self,
        owner_id: int | None = None,
        status: JobStatus | None = None,
        priority: JobPriority | None = None,
        submitted_after: datetime | None = None,
        submitted_before: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[TrainingJob], int]:
        """List training jobs with filters and pagination."""
        return await self._repository.list_jobs(
            owner_id=owner_id,
            status=status,
            priority=priority,
            submitted_after=submitted_after,
            submitted_before=submitted_before,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def pause_job(self, job_id: int) -> TrainingJob:
        """Pause a running training job."""
        job = await self._get_or_raise(job_id)

        # Use base class method for state transition validation
        self._validate_state_transition(
            job, JobStatus.PAUSED, [JobStatus.RUNNING]
        )

        await self._hyperpod_client.stop_training_job(
            cluster_name=self._cluster_name,
            job_name=job.job_name,
        )

        job.pause()
        return await self._repository.update(job)

    async def resume_job(self, job_id: int) -> TrainingJob:
        """Resume a paused or preempted training job."""
        job = await self._get_or_raise(job_id)

        # Use base class method for state transition validation
        self._validate_state_transition(
            job, JobStatus.RUNNING, [JobStatus.PAUSED, JobStatus.PREEMPTED]
        )

        job_config = self._build_job_config(job)
        await self._hyperpod_client.submit_training_job(
            cluster_name=self._cluster_name,
            job_name=job.job_name,
            job_config=job_config,
        )

        job.resume()
        return await self._repository.update(job)

    async def cancel_job(self, job_id: int) -> TrainingJob:
        """Cancel a training job."""
        job = await self._get_or_raise(job_id)

        if job.is_terminal():
            raise InvalidStateTransitionError(
                "TrainingJob", job.status.value, JobStatus.FAILED.value
            )

        if job.status in (JobStatus.RUNNING, JobStatus.SUBMITTED):
            await self._hyperpod_client.stop_training_job(
                cluster_name=self._cluster_name,
                job_name=job.job_name,
            )

        job.fail(
            error_message="Job cancelled by user", failure_reason="CANCELLED_BY_USER"
        )
        return await self._repository.update(job)

    async def delete_job(self, job_id: int) -> None:
        """Delete a training job (soft delete)."""
        job = await self._get_or_raise(job_id)

        if job.status in (JobStatus.RUNNING, JobStatus.SUBMITTED):
            await self._hyperpod_client.stop_training_job(
                cluster_name=self._cluster_name,
                job_name=job.job_name,
            )
            job.fail(error_message="Job deleted by user", failure_reason="USER_DELETED")
            await self._repository.update(job)

        await self._repository.soft_delete(job_id)
