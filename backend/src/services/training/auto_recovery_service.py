"""训练任务自动恢复服务

当训练任务因故障失败时,自动从最新checkpoint恢复训练
支持指数退避重试策略和可恢复错误类型识别
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.training import TrainingJob, TrainingJobStatus
from services.checkpoint.checkpoint_service import CheckpointService
from services.training.job_service import TrainingJobService

logger = logging.getLogger(__name__)


class AutoRecoveryService:
    """训练任务自动恢复服务

    功能:
    1. 判断任务是否可恢复(检查重试次数、错误类型、checkpoint可用性)
    2. 执行恢复操作(获取最新checkpoint、重启任务、更新重试计数)
    3. 批量处理失败任务(定期扫描并恢复)

    重试策略:
    - 第1次: 立即重试
    - 第2次: 等待2分钟
    - 第3次: 等待5分钟
    - 第4次及以上: 等待10分钟
    """

    # 不可恢复的错误类型关键词(代码错误、配置错误等)
    NON_RECOVERABLE_ERRORS = [
        "ImportError",
        "ModuleNotFoundError",
        "SyntaxError",
        "NameError",
        "TypeError",
        "ValueError",
        "AttributeError",
        "ConfigurationError",
        "InvalidArgumentError",
        "permission denied",
        "access denied",
        "unauthorized",
        "forbidden",
        "authentication failed",
    ]

    # 可恢复的错误类型关键词(OOM、节点故障等)
    RECOVERABLE_ERRORS = [
        "OutOfMemoryError",
        "OOM",
        "CUDA out of memory",
        "NodeLost",
        "node failure",
        "pod evicted",
        "preemption",
        "timeout",
        "connection reset",
        "broken pipe",
        "network error",
    ]

    def __init__(self, session: AsyncSession):
        """初始化自动恢复服务

        Args:
            session: 数据库异步会话
        """
        self.session = session
        self.checkpoint_service = CheckpointService(session)
        self.job_service = TrainingJobService(session)

    async def can_recover(self, job: TrainingJob) -> tuple[bool, str]:
        """判断训练任务是否可恢复

        检查条件:
        1. 是否超过最大重试次数
        2. 错误类型是否可恢复
        3. 是否有可用checkpoint
        4. 是否满足重试时间间隔(指数退避)

        Args:
            job: 训练任务对象(必须已预加载config)

        Returns:
            (is_recoverable, reason)
            - is_recoverable: 是否可恢复
            - reason: 不可恢复的原因(可恢复时为空字符串)
        """
        # 1. 检查任务是否处于FAILED状态
        if job.status != TrainingJobStatus.FAILED:
            return False, f"任务状态不是FAILED: {job.status.value}"

        # 2. 检查是否超过最大重试次数
        if not job.config:
            return False, "任务配置未加载"

        max_retries = job.config.max_retries
        if job.retry_count >= max_retries:
            return False, f"已达到最大重试次数: {job.retry_count}/{max_retries}"

        # 3. 检查错误类型是否可恢复
        error_message = job.error_message or ""

        # 优先判断是否为不可恢复错误
        for error_keyword in self.NON_RECOVERABLE_ERRORS:
            if error_keyword.lower() in error_message.lower():
                return False, f"检测到不可恢复错误类型: {error_keyword}"

        # 如果有明确的可恢复错误标识,允许恢复
        has_recoverable_error = any(
            keyword.lower() in error_message.lower()
            for keyword in self.RECOVERABLE_ERRORS
        )

        # 如果既不是明确的可恢复错误也不是不可恢复错误,默认允许恢复(可能是基础设施问题)
        # 但要限制重试次数避免无限循环

        # 4. 检查是否有可用checkpoint
        latest_checkpoint = await self.checkpoint_service.get_latest_checkpoint(
            job_id=job.id
        )
        if not latest_checkpoint:
            return False, "没有可用的checkpoint进行恢复"

        # 5. 检查是否满足重试时间间隔(指数退避)
        if job.last_retry_at:
            required_wait_time = self._calculate_backoff_time(job.retry_count)
            time_since_last_retry = datetime.utcnow() - job.last_retry_at

            if time_since_last_retry < required_wait_time:
                remaining_time = (required_wait_time - time_since_last_retry).total_seconds()
                return False, f"未达到重试间隔: 还需等待{remaining_time:.0f}秒"

        # 所有检查通过,可以恢复
        logger.info(
            f"训练任务可恢复: job_id={job.id}, retry_count={job.retry_count}, "
            f"checkpoint_step={latest_checkpoint.step}"
        )
        return True, ""

    def _calculate_backoff_time(self, retry_count: int) -> timedelta:
        """计算指数退避时间

        重试策略:
        - 第1次: 0秒(立即)
        - 第2次: 2分钟
        - 第3次: 5分钟
        - 第4次及以上: 10分钟

        Args:
            retry_count: 当前重试次数

        Returns:
            需要等待的时间间隔
        """
        if retry_count == 0:
            return timedelta(seconds=0)
        elif retry_count == 1:
            return timedelta(minutes=2)
        elif retry_count == 2:
            return timedelta(minutes=5)
        else:
            return timedelta(minutes=10)

    async def recover_job(self, job: TrainingJob) -> TrainingJob:
        """恢复训练任务

        执行步骤:
        1. 获取最新checkpoint
        2. 更新任务配置,添加resume参数
        3. 重置任务状态为PENDING
        4. 增加retry_count
        5. 更新last_retry_at
        6. 调用TrainingJobService启动任务

        Args:
            job: 训练任务对象(必须已预加载config)

        Returns:
            更新后的训练任务对象

        Raises:
            ValueError: 任务无法恢复或启动失败
        """
        # 1. 再次检查是否可恢复(防止并发问题)
        can_recover, reason = await self.can_recover(job)
        if not can_recover:
            raise ValueError(f"训练任务无法恢复: {reason}")

        # 2. 获取最新checkpoint
        latest_checkpoint = await self.checkpoint_service.get_latest_checkpoint(
            job_id=job.id
        )
        if not latest_checkpoint:
            raise ValueError("没有可用的checkpoint")

        logger.info(
            f"开始恢复训练任务: job_id={job.id}, retry_count={job.retry_count}, "
            f"checkpoint_path={latest_checkpoint.storage_path}"
        )

        # 3. 更新任务配置,添加checkpoint恢复参数
        if not job.config:
            raise ValueError("任务配置未加载")

        job.config.checkpoint_path = latest_checkpoint.storage_path

        # 更新命令参数,添加--resume-from-checkpoint
        if job.config.args is None:
            job.config.args = []

        # 移除旧的resume参数(如果存在)
        job.config.args = [
            arg for arg in job.config.args
            if not arg.startswith("--resume-from-checkpoint")
        ]

        # 添加新的resume参数
        job.config.args.append(f"--resume-from-checkpoint={latest_checkpoint.storage_path}")

        # 4. 重置任务状态为PENDING(准备重启)
        job.status = TrainingJobStatus.PENDING
        job.queued_at = None
        job.started_at = None
        job.completed_at = None
        job.k8s_job_name = None  # 重置K8s Job名称(启动时会生成新的)

        # 5. 更新重试计数和时间
        job.retry_count += 1
        job.last_retry_at = datetime.utcnow()

        # 6. 保存更新
        await self.session.commit()
        await self.session.refresh(job)

        logger.info(
            f"任务配置已更新: job_id={job.id}, retry_count={job.retry_count}, "
            f"resume_from={latest_checkpoint.storage_path}"
        )

        # 7. 启动任务
        try:
            recovered_job = await self.job_service.start_training_job(job.id)
            logger.info(
                f"训练任务恢复成功: job_id={job.id}, retry_count={job.retry_count}, "
                f"k8s_job_name={recovered_job.k8s_job_name}"
            )
            return recovered_job
        except Exception as e:
            logger.error(f"训练任务启动失败: job_id={job.id}, error={e}")
            # 启动失败不回滚retry_count,避免重复尝试
            raise ValueError(f"训练任务恢复失败: {str(e)}") from e

    async def process_failed_jobs(self) -> dict:
        """批量处理失败的训练任务

        扫描所有FAILED状态且未超过max_retries的任务,
        对每个任务执行can_recover判断,可恢复的执行recover_job

        Returns:
            统计信息字典:
            {
                "total_failed": 总失败任务数,
                "recoverable": 可恢复任务数,
                "recovered": 成功恢复任务数,
                "failed": 恢复失败任务数,
                "skipped": 跳过任务数(不可恢复),
                "errors": 错误列表
            }
        """
        logger.info("开始批量处理失败的训练任务")

        stats = {
            "total_failed": 0,
            "recoverable": 0,
            "recovered": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        try:
            # 查询所有FAILED状态的任务(预加载config)
            query = (
                select(TrainingJob)
                .where(
                    TrainingJob.status == TrainingJobStatus.FAILED,
                    TrainingJob.deleted_at.is_(None),
                )
                .options(selectinload(TrainingJob.config))
                .order_by(TrainingJob.completed_at.desc())
            )

            result = await self.session.execute(query)
            failed_jobs = result.scalars().all()

            stats["total_failed"] = len(failed_jobs)
            logger.info(f"找到{len(failed_jobs)}个失败的训练任务")

            # 处理每个失败任务
            for job in failed_jobs:
                try:
                    # 判断是否可恢复
                    can_recover, reason = await self.can_recover(job)

                    if can_recover:
                        stats["recoverable"] += 1
                        logger.info(f"尝试恢复任务: job_id={job.id}, name={job.name}")

                        # 执行恢复
                        await self.recover_job(job)
                        stats["recovered"] += 1

                        logger.info(
                            f"任务恢复成功: job_id={job.id}, retry_count={job.retry_count}"
                        )
                    else:
                        stats["skipped"] += 1
                        logger.debug(f"跳过任务: job_id={job.id}, reason={reason}")

                except Exception as e:
                    stats["failed"] += 1
                    error_msg = f"任务恢复失败: job_id={job.id}, error={str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

            logger.info(
                f"批量处理完成: total={stats['total_failed']}, "
                f"recovered={stats['recovered']}, failed={stats['failed']}, "
                f"skipped={stats['skipped']}"
            )

            return stats

        except Exception as e:
            error_msg = f"批量处理失败任务时发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            stats["errors"].append(error_msg)
            return stats


__all__ = ["AutoRecoveryService"]
