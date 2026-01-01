"""训练任务业务逻辑服务

处理训练任务的创建、启动、停止、监控等核心业务逻辑
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.training import (
    TrainingJob,
    TrainingJobConfig,
    TrainingJobStatus,
    TrainingJobType,
    FrameworkType,
)
from models.user import Project, User
from api.schemas.training import TrainingJobCreate, TrainingJobUpdate
from services.training.operators import (
    HyperPodOperator,
    JobCreationError,
    HyperPodOperatorError,
)

logger = logging.getLogger(__name__)


class TrainingJobService:
    """训练任务服务

    封装训练任务的完整业务逻辑
    """

    def __init__(self, session: AsyncSession):
        """初始化训练任务服务

        Args:
            session: 数据库异步会话
        """
        self.session = session
        # 初始化HyperPod Operator(延迟初始化,避免在非K8s环境启动失败)
        self._operator: Optional[HyperPodOperator] = None

    async def create_training_job(
        self,
        job_data: TrainingJobCreate,
        creator: User,
    ) -> TrainingJob:
        """创建训练任务

        Args:
            job_data: 训练任务创建数据
            creator: 创建者用户对象

        Returns:
            创建的训练任务对象

        Raises:
            ValueError: 项目不存在或用户无权访问
        """
        # 验证项目存在
        project = await self._get_project(job_data.project_id)
        if not project:
            raise ValueError(f"项目 {job_data.project_id} 不存在")

        # 生成K8s命名空间(基于项目ID)
        k8s_namespace = f"ai-training-{job_data.project_id}"

        # 创建训练任务对象(包含Kueue Gang Scheduling参数)
        training_job = TrainingJob(
            name=job_data.name,
            description=job_data.description,
            status=TrainingJobStatus.PENDING,
            job_type=job_data.job_type,
            framework=job_data.framework,
            project_id=job_data.project_id,
            creator_id=creator.id,
            k8s_namespace=k8s_namespace,
            # Kueue Gang Scheduling支持
            priority=job_data.priority,  # 从请求中获取priority
            queue_name=job_data.queue_name,  # 从请求中获取queue_name
        )

        # 创建训练配置对象
        config = TrainingJobConfig(
            node_count=job_data.config.node_count,
            gpu_per_node=job_data.config.gpu_per_node,
            cpu_per_node=job_data.config.cpu_per_node,
            memory_per_node_gb=job_data.config.memory_per_node_gb,
            gpu_type=job_data.config.gpu_type,
            docker_image=job_data.config.docker_image,
            command=job_data.config.command,
            args=job_data.config.args,
            env_vars=job_data.config.env_vars,
            dataset_path=job_data.config.dataset_path,
            checkpoint_path=job_data.config.checkpoint_path,
            output_path=job_data.config.output_path,
            hyperparameters=job_data.config.hyperparameters,
            distributed_config=job_data.config.distributed_config,
            timeout_seconds=job_data.config.timeout_seconds,
            max_retries=job_data.config.max_retries,
        )

        # 关联配置到任务
        training_job.config = config

        # 保存到数据库
        self.session.add(training_job)
        await self.session.commit()
        # 刷新以获取数据库生成的值(created_at, updated_at)
        # 预加载config关系以避免MissingGreenlet错误
        await self.session.refresh(training_job, ["config"])

        logger.info(f"创建训练任务成功: {training_job.id} - {job_data.name}")
        return training_job

    async def get_training_job(
        self,
        job_id: int,
        include_config: bool = False,
    ) -> Optional[TrainingJob]:
        """获取训练任务详情

        Args:
            job_id: 训练任务ID
            include_config: 是否包含配置信息

        Returns:
            训练任务对象,不存在返回None
        """
        query = select(TrainingJob).where(
            TrainingJob.id == job_id,
            TrainingJob.deleted_at.is_(None),
        )

        # 预加载配置
        if include_config:
            query = query.options(selectinload(TrainingJob.config))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_training_jobs(
        self,
        project_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        status: Optional[TrainingJobStatus] = None,
        framework: Optional[FrameworkType] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[TrainingJob], int]:
        """列出训练任务

        Args:
            project_id: 项目ID过滤
            creator_id: 创建者ID过滤
            status: 状态过滤
            framework: 框架过滤
            page: 页码(从1开始)
            size: 每页数量

        Returns:
            (训练任务列表, 总数)
        """
        # 构建查询
        query = select(TrainingJob).where(TrainingJob.deleted_at.is_(None))

        # 应用过滤
        if project_id is not None:
            query = query.where(TrainingJob.project_id == project_id)
        if creator_id is not None:
            query = query.where(TrainingJob.creator_id == creator_id)
        if status is not None:
            query = query.where(TrainingJob.status == status)
        if framework is not None:
            query = query.where(TrainingJob.framework == framework)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询
        query = query.order_by(TrainingJob.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        # 预加载config关系避免MissingGreenlet
        query = query.options(selectinload(TrainingJob.config))

        result = await self.session.execute(query)
        jobs = result.scalars().all()

        return list(jobs), total

    async def update_training_job(
        self,
        job_id: int,
        job_data: TrainingJobUpdate,
    ) -> Optional[TrainingJob]:
        """更新训练任务

        Args:
            job_id: 训练任务ID
            job_data: 更新数据

        Returns:
            更新后的训练任务对象,不存在返回None
        """
        job = await self.get_training_job(job_id, include_config=True)
        if not job:
            return None

        # 更新字段
        if job_data.name is not None:
            job.name = job_data.name
        if job_data.description is not None:
            job.description = job_data.description

        await self.session.commit()
        # refresh加载所有更新的字段(如updated_at服务端默认值)
        # config在get_training_job时已预加载，expire_on_commit=False保持其加载状态
        await self.session.refresh(job)

        logger.info(f"更新训练任务成功: {job_id}")
        return job

    async def delete_training_job(self, job_id: int) -> bool:
        """删除训练任务(软删除)

        Args:
            job_id: 训练任务ID

        Returns:
            是否删除成功
        """
        job = await self.get_training_job(job_id)
        if not job:
            return False

        # 只能删除终止状态的任务
        if not job.is_terminal:
            raise ValueError(f"无法删除活跃状态的任务: {job.status.value}")

        # 软删除(设置deleted_at即可,is_deleted会自动计算)
        job.deleted_at = datetime.utcnow()

        await self.session.commit()
        logger.info(f"删除训练任务成功: {job_id}")
        return True

    async def start_training_job(self, job_id: int) -> TrainingJob:
        """启动训练任务

        Args:
            job_id: 训练任务ID

        Returns:
            更新后的训练任务对象

        Raises:
            ValueError: 任务不存在或状态不允许启动
        """
        job = await self.get_training_job(job_id, include_config=True)
        if not job:
            raise ValueError(f"训练任务 {job_id} 不存在")

        # 验证状态(只有PENDING可以启动)
        if job.status != TrainingJobStatus.PENDING:
            raise ValueError(f"任务状态 {job.status.value} 不允许启动")

        # 更新状态为QUEUED
        job.status = TrainingJobStatus.QUEUED
        job.queued_at = datetime.utcnow()

        try:
            # 创建K8s HyperPodPytorchJob资源(传递Kueue参数)
            operator = self._get_operator()
            k8s_job_name = await operator.create_pytorch_job(
                job=job,
                config=job.config,
                priority=job.priority or "normal",  # 使用任务的priority,默认normal
                queue_name=job.queue_name,  # 使用任务的queue_name,None时使用项目队列
            )
            job.k8s_job_name = k8s_job_name

            # 保存K8s Job名称
            await self.session.commit()
            # refresh加载所有更新的字段
            # config在get_training_job时已预加载，expire_on_commit=False保持其加载状态
            await self.session.refresh(job)

            logger.info(
                f"启动训练任务成功: {job_id} (K8s Job: {k8s_job_name})"
            )
            return job

        except JobCreationError as e:
            # K8s Job创建失败,回滚状态
            logger.error(f"K8s Job创建失败: {e}")
            job.status = TrainingJobStatus.FAILED
            job.error_message = f"K8s Job创建失败: {str(e)}"
            job.completed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(job)
            raise ValueError(f"训练任务启动失败: {str(e)}") from e
        except Exception as e:
            # 其他异常
            logger.error(f"训练任务启动失败: {e}", exc_info=True)
            job.status = TrainingJobStatus.FAILED
            job.error_message = f"任务启动失败: {str(e)}"
            job.completed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(job)
            raise ValueError(f"训练任务启动失败: {str(e)}") from e

    async def stop_training_job(
        self,
        job_id: int,
        save_checkpoint: bool = True,
    ) -> TrainingJob:
        """停止训练任务

        Args:
            job_id: 训练任务ID
            save_checkpoint: 是否保存检查点

        Returns:
            更新后的训练任务对象

        Raises:
            ValueError: 任务不存在或状态不允许停止
        """
        job = await self.get_training_job(job_id, include_config=True)
        if not job:
            raise ValueError(f"训练任务 {job_id} 不存在")

        # 验证状态(只有活跃状态可以停止)
        if not job.is_active:
            raise ValueError(f"任务状态 {job.status.value} 不允许停止")

        # TODO: T040 - 如果需要保存检查点,先保存(CheckpointService)
        # if save_checkpoint:
        #     await self._save_checkpoint(job)

        try:
            # 删除K8s资源
            if job.k8s_job_name:
                operator = self._get_operator()
                await operator.delete_job(
                    job_name=job.k8s_job_name,
                    namespace=job.k8s_namespace,
                )
                logger.info(f"K8s Job已删除: {job.k8s_job_name}")
        except Exception as e:
            # K8s资源清理失败不应阻止状态更新
            logger.warning(f"K8s Job删除失败(继续更新状态): {e}")

        # 更新状态为CANCELLED
        job.status = TrainingJobStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        await self.session.commit()
        # refresh加载所有更新的字段
        # config在get_training_job时已预加载，expire_on_commit=False保持其加载状态
        await self.session.refresh(job)

        logger.info(f"停止训练任务成功: {job_id}")
        return job

    async def sync_job_status(self, job_id: int) -> TrainingJob:
        """同步训练任务状态

        从K8s查询最新状态并更新数据库

        Args:
            job_id: 训练任务ID

        Returns:
            更新后的训练任务对象

        Raises:
            ValueError: 任务不存在或尚未创建K8s Job
        """
        job = await self.get_training_job(job_id, include_config=True)
        if not job:
            raise ValueError(f"训练任务 {job_id} 不存在")

        if not job.k8s_job_name:
            raise ValueError(f"训练任务 {job_id} 尚未创建K8s Job")

        # 如果任务已处于终止状态,无需同步
        if job.is_terminal:
            logger.debug(f"训练任务 {job_id} 已处于终止状态,跳过同步")
            return job

        try:
            # 从K8s同步状态
            operator = self._get_operator()
            new_status, error_message, exit_code = await operator.sync_job_status(
                job=job
            )

            # 更新数据库状态
            old_status = job.status
            job.status = new_status

            # 更新时间戳
            if new_status == TrainingJobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif new_status in [
                TrainingJobStatus.COMPLETED,
                TrainingJobStatus.FAILED,
                TrainingJobStatus.CANCELLED,
                TrainingJobStatus.TIMEOUT,
            ]:
                if not job.completed_at:
                    job.completed_at = datetime.utcnow()

            # 更新错误信息
            if error_message:
                job.error_message = error_message
            if exit_code is not None:
                job.exit_code = exit_code

            await self.session.commit()
            await self.session.refresh(job)

            if old_status != new_status:
                logger.info(
                    f"训练任务状态已同步: {job_id} ({old_status.value} -> {new_status.value})"
                )

            return job

        except HyperPodOperatorError as e:
            logger.error(f"训练任务状态同步失败: {job_id} - {e}")
            raise ValueError(f"状态同步失败: {str(e)}") from e

    # ========== 内部辅助方法 ==========

    def _get_operator(self) -> HyperPodOperator:
        """获取HyperPod Operator实例(延迟初始化)

        Returns:
            HyperPodOperator实例

        Raises:
            HyperPodOperatorError: Operator初始化失败
        """
        if self._operator is None:
            try:
                self._operator = HyperPodOperator()
                logger.info("HyperPod Operator初始化成功")
            except Exception as e:
                raise HyperPodOperatorError(
                    f"HyperPod Operator初始化失败: {str(e)}"
                ) from e
        return self._operator

    async def _get_project(self, project_id: int) -> Optional[Project]:
        """获取项目对象

        Args:
            project_id: 项目ID

        Returns:
            项目对象,不存在返回None
        """
        result = await self.session.execute(
            select(Project).where(
                Project.id == project_id,
                Project.deleted_at.is_(None),  # 使用deleted_at而不是is_deleted
            )
        )
        return result.scalar_one_or_none()


__all__ = ["TrainingJobService"]
