"""训练任务状态同步服务 (T037)

职责:
- 定时同步 HyperPod 训练状态到数据库
- 处理状态转换事件
- 记录状态变更日志
- 处理抢占计数和连续失败逻辑

遵循 Constitution I.B: 优先使用 sagemaker-hyperpod SDK
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

from src.modules.training.application.interfaces import IHyperPodClient
from src.modules.training.domain.entities.training_job import TrainingJob
from src.modules.training.domain.repositories.training_job_repository import (
    ITrainingJobRepository,
)
from src.modules.training.domain.value_objects import JobStatus
from src.shared.domain.exceptions import EntityNotFoundError

logger = structlog.get_logger(__name__)

# 连续抢占次数上限
MAX_PREEMPTION_COUNT = 3

# HyperPod 状态到平台状态的映射
HYPERPOD_TO_PLATFORM_STATUS = {
    "Pending": JobStatus.SUBMITTED,
    "Starting": JobStatus.SUBMITTED,
    "Running": JobStatus.RUNNING,
    "Stopping": JobStatus.RUNNING,
    "Stopped": JobStatus.PAUSED,
    "Succeeded": JobStatus.COMPLETED,
    "Failed": JobStatus.FAILED,
    "Preempted": JobStatus.PREEMPTED,
}


@dataclass
class SyncResult:
    """状态同步结果统计"""

    synced_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    errors: list[str] = field(default_factory=list)


class TrainingSyncService:
    """训练任务状态同步服务 (T037)"""

    def __init__(
        self,
        training_job_repository: ITrainingJobRepository,
        hyperpod_client: IHyperPodClient,
        cluster_name: str,
    ) -> None:
        """初始化同步服务"""
        self._repo = training_job_repository
        self._hyperpod = hyperpod_client
        self._cluster_name = cluster_name

    async def sync_all_active_jobs(self) -> SyncResult:
        """同步所有活跃任务状态

        查询所有非终态任务 (SUBMITTED, RUNNING, PAUSED, PREEMPTED)，
        从 HyperPod 获取最新状态并更新数据库。

        Returns:
            SyncResult: 同步结果统计
        """
        result = SyncResult()
        active_jobs = await self._get_active_jobs()

        for job in active_jobs:
            sync_result = await self._sync_job_internal(job)
            if sync_result is True:
                result.synced_count += 1
            elif sync_result is False:
                result.failed_count += 1
                result.errors.append(f"Job {job.job_name}: sync failed")
            else:  # sync_result is None
                result.skipped_count += 1

        logger.info(
            "sync_completed",
            synced=result.synced_count,
            skipped=result.skipped_count,
            failed=result.failed_count,
        )
        return result

    async def sync_job(self, job: TrainingJob) -> bool:
        """同步单个任务状态（公开 API，保持向后兼容）

        Args:
            job: 训练任务实体

        Returns:
            bool: 是否成功同步（状态有变化并更新）
        """
        result = await self._sync_job_internal(job)
        return result is True

    async def _sync_job_internal(self, job: TrainingJob) -> bool | None:
        """同步单个任务状态（内部实现）

        Returns:
            True: 成功同步且状态有变化
            False: 同步失败（错误或非法转换）
            None: 状态未变化（跳过）
        """
        try:
            # 从 HyperPod 获取最新状态
            hyperpod_response = await self._fetch_job_status(job)
            if hyperpod_response is None:
                return False

            # 验证并处理状态变化
            return await self._process_status_change(job, hyperpod_response)

        except Exception as e:
            logger.exception(
                "sync_job_failed",
                job_id=job.id,
                job_name=job.job_name,
                error_type=type(e).__name__,
                error=str(e),
            )
            return False

    async def _process_status_change(self, job: TrainingJob, hyperpod_response: dict[str, Any]) -> bool | None:
        """处理状态变化

        Returns:
            True: 状态已更新
            False: 状态转换非法
            None: 状态未变化
        """
        # 映射并验证状态
        hyperpod_status = hyperpod_response.get("status")
        if hyperpod_status is None or not isinstance(hyperpod_status, str):
            logger.warning("missing_hyperpod_status", response=hyperpod_response)
            return False
        new_status = HYPERPOD_TO_PLATFORM_STATUS.get(hyperpod_status)
        if new_status is None:
            logger.warning("unknown_hyperpod_status", status=hyperpod_response.get("status"))
            return False

        # 状态未变化，跳过
        if new_status == job.status:
            return None

        # 检查状态转换是否合法
        if not job.can_transition_to(new_status):
            logger.warning(
                "invalid_status_transition",
                job_name=job.job_name,
                from_status=job.status.value,
                to_status=new_status.value,
            )
            return False

        # 执行状态转换
        await self._apply_status_transition(job, new_status, hyperpod_response)
        return True

    async def _fetch_job_status(self, job: TrainingJob) -> dict[str, Any] | None:
        """从 HyperPod 获取任务状态，处理异常情况"""
        try:
            return await self._hyperpod.get_training_job_status(
                cluster_name=self._cluster_name,
                job_name=job.job_name,
            )
        except EntityNotFoundError:
            # HyperPod 中找不到任务，标记为 Failed
            logger.warning("job_not_found_in_hyperpod", job_name=job.job_name)
            job.fail(
                error_message=f"HyperPod 中找不到任务 {job.job_name}",
                failure_reason="JobNotFoundInHyperPod",
            )
            await self._repo.update(job)
            return None
        except Exception as e:
            logger.exception(
                "fetch_job_status_failed",
                job_id=job.id,
                job_name=job.job_name,
                error_type=type(e).__name__,
                error=str(e),
            )
            return None

    async def _apply_status_transition(
        self,
        job: TrainingJob,
        new_status: JobStatus,
        hyperpod_response: dict[str, Any],
    ) -> None:
        """应用状态转换并更新数据库"""
        old_status = job.status

        # 处理特殊状态
        if new_status == JobStatus.PREEMPTED:
            await self._handle_preemption(job)
        elif new_status == JobStatus.FAILED:
            error_message = hyperpod_response.get("error_message")
            job.fail(error_message=error_message, failure_reason="HyperPodFailed")
        else:
            job.transition_to(new_status)

        await self._repo.update(job)
        logger.info(
            "job_status_updated",
            job_name=job.job_name,
            from_status=old_status.value,
            to_status=new_status.value,
        )

    async def _handle_preemption(self, job: TrainingJob) -> None:
        """处理抢占状态转换"""
        new_preemption_count = job.preemption_count + 1

        if new_preemption_count >= MAX_PREEMPTION_COUNT:
            # 连续抢占次数超限，标记为 Failed
            job.preemption_count = new_preemption_count
            job.fail(
                error_message=f"连续抢占次数超限 ({new_preemption_count}/{MAX_PREEMPTION_COUNT})",
                failure_reason="PreemptionExhausted",
            )
            logger.warning(
                "preemption_exhausted",
                job_name=job.job_name,
                preemption_count=new_preemption_count,
                max_count=MAX_PREEMPTION_COUNT,
            )
        else:
            # 正常抢占，transition_to 会累加 preemption_count
            job.transition_to(JobStatus.PREEMPTED)
            logger.info(
                "job_preempted",
                job_name=job.job_name,
                preemption_count=job.preemption_count,
            )

    async def _get_active_jobs(self) -> list[TrainingJob]:
        """获取所有需要同步的活跃任务"""
        active_statuses = [
            JobStatus.SUBMITTED,
            JobStatus.RUNNING,
            JobStatus.PAUSED,
            JobStatus.PREEMPTED,
        ]
        return await self._repo.list_by_statuses(active_statuses)

