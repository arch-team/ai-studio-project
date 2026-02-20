"""Checkpoint Trigger Service - 特定场景触发的检查点创建."""

from src.modules.training.application.services.checkpoint_creation_service import CheckpointCreationService
from src.modules.training.domain.entities import Checkpoint
from src.modules.training.domain.exceptions import (
    CheckpointStorageError,
    InvalidJobStateError,
    TrainingJobNotFoundError,
)
from src.modules.training.domain.repositories import ITrainingJobRepository
from src.modules.training.domain.value_objects import CheckpointTriggerType, JobStatus
from src.shared.utils import utc_now


class CheckpointTriggerService:
    """特定场景触发的检查点创建服务."""

    def __init__(
        self,
        creation_service: CheckpointCreationService,
        training_job_repo: ITrainingJobRepository | None = None,
    ):
        self._creation_service = creation_service
        self._training_job_repo = training_job_repo

    async def create_scheduled_checkpoints(self) -> list[Checkpoint]:
        """为所有 Running 状态的任务创建定期检查点.

        由定时任务调用，按配置的 checkpoint_interval 执行。

        Returns:
            list[Checkpoint]: 创建的检查点列表
        """
        if self._training_job_repo is None:
            return []

        # 查询所有 Running 状态的任务
        running_jobs, _ = await self._training_job_repo.list_jobs(
            status=JobStatus.RUNNING,
            page=1,
            page_size=1000,  # 假设不会超过 1000 个并行任务
        )

        checkpoints = []
        for job in running_jobs:
            if job.id is None:
                continue
            try:
                checkpoint = await self._creation_service.create_checkpoint(
                    job_id=job.id,
                    trigger_type=CheckpointTriggerType.SCHEDULED,
                )
                checkpoints.append(checkpoint)
            except (InvalidJobStateError, CheckpointStorageError):
                # 跳过无法创建检查点的任务，继续处理其他任务
                continue

        return checkpoints

    async def create_checkpoint_on_interrupt(self, job_id: int) -> Checkpoint | None:
        """训练中断时创建检查点.

        Args:
            job_id: 训练任务 ID

        Returns:
            Checkpoint | None: 创建的检查点，失败返回 None
        """
        return await self._safe_create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.INTERRUPT,
        )

    async def create_checkpoint_on_node_failure(
        self,
        job_id: int,
        pod_name: str,
    ) -> Checkpoint | None:
        """节点故障时创建检查点.

        当检测到 PodsReady=False 持续 >30s 时触发。

        Args:
            job_id: 训练任务 ID
            pod_name: 故障 Pod 名称

        Returns:
            Checkpoint | None: 创建的检查点，失败返回 None
        """
        checkpoint_name = f"node-failure-{pod_name}-{utc_now().strftime('%Y%m%d%H%M%S')}"
        return await self._safe_create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.NODE_FAILURE,
            checkpoint_name=checkpoint_name,
            metrics={"failed_pod": pod_name},
        )

    async def create_checkpoint_on_preemption(
        self,
        job_id: int,
        timeout_seconds: int = 300,
    ) -> Checkpoint | None:
        """资源抢占时创建检查点.

        在抢占前触发，必须在 timeout_seconds 内完成。

        Args:
            job_id: 训练任务 ID
            timeout_seconds: 超时时间 (默认 5 分钟)

        Returns:
            Checkpoint | None: 创建的检查点，失败返回 None
        """
        # TODO: 实现超时控制逻辑
        return await self._safe_create_checkpoint(
            job_id=job_id,
            trigger_type=CheckpointTriggerType.PREEMPTION,
        )

    async def _safe_create_checkpoint(
        self,
        job_id: int,
        trigger_type: CheckpointTriggerType,
        checkpoint_name: str | None = None,
        metrics: dict | None = None,
    ) -> Checkpoint | None:
        """安全创建检查点 - 错误时返回 None 而不是抛出异常."""
        try:
            return await self._creation_service.create_checkpoint(
                job_id=job_id,
                trigger_type=trigger_type,
                checkpoint_name=checkpoint_name,
                metrics=metrics,
            )
        except (TrainingJobNotFoundError, InvalidJobStateError, CheckpointStorageError):
            return None
