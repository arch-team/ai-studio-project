"""训练任务业务逻辑服务

处理训练任务的创建、启动、停止、监控等核心业务逻辑
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.training import (
    TrainingJob,
    TrainingJobConfig,
    TrainingJobStatus,
    TrainingJobType,
    FrameworkType,
)
from models.user import Project, User
from services.k8s.job_manager import JobManager
from services.k8s.pod_manager import PodManager

logger = logging.getLogger(__name__)


class TrainingJobService:
    """训练任务服务

    封装训练任务的完整业务逻辑
    """

    def __init__(self):
        """初始化训练任务服务"""
        self.job_manager = JobManager()
        self.pod_manager = PodManager()

    async def create_training_job(
        self,
        db: AsyncSession,
        project_id: int,
        creator_id: int,
        name: str,
        job_type: TrainingJobType,
        framework: FrameworkType,
        config: dict,
        description: str | None = None,
    ) -> TrainingJob:
        """创建训练任务

        Args:
            db: 数据库会话
            project_id: 项目ID
            creator_id: 创建者ID
            name: 任务名称
            job_type: 任务类型
            framework: 训练框架
            config: 任务配置
            description: 任务描述

        Returns:
            TrainingJob: 创建的训练任务

        Raises:
            ValueError: 参数验证失败
        """
        # 验证项目是否存在
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 创建训练任务记录
        training_job = TrainingJob(
            name=name,
            description=description,
            status=TrainingJobStatus.PENDING,
            job_type=job_type,
            framework=framework,
            project_id=project_id,
            creator_id=creator_id,
            k8s_namespace=project.namespace,
        )

        db.add(training_job)
        await db.flush()  # 获取训练任务ID

        # 创建训练任务配置
        job_config = TrainingJobConfig(
            job_id=training_job.id,
            node_count=config.get("node_count", 1),
            gpu_per_node=config.get("gpu_per_node", 1),
            cpu_per_node=config.get("cpu_per_node", 8),
            memory_per_node_gb=config.get("memory_per_node_gb", 32),
            gpu_type=config.get("gpu_type"),
            docker_image=config["docker_image"],
            command=config["command"],
            args=config.get("args"),
            env_vars=config.get("env_vars"),
            dataset_path=config.get("dataset_path"),
            checkpoint_path=config.get("checkpoint_path"),
            output_path=config["output_path"],
            hyperparameters=config.get("hyperparameters"),
            distributed_config=config.get("distributed_config"),
            timeout_seconds=config.get("timeout_seconds"),
            max_retries=config.get("max_retries", 0),
        )

        db.add(job_config)
        await db.commit()
        await db.refresh(training_job)

        logger.info(f"创建训练任务成功: {training_job.id} - {name}")
        return training_job

    async def start_training_job(
        self, db: AsyncSession, job_id: int
    ) -> TrainingJob:
        """启动训练任务

        Args:
            db: 数据库会话
            job_id: 训练任务ID

        Returns:
            TrainingJob: 更新后的训练任务

        Raises:
            ValueError: 任务状态不允许启动
        """
        # 查询训练任务和配置
        result = await db.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"训练任务不存在: {job_id}")

        # 检查任务状态
        if job.status != TrainingJobStatus.PENDING:
            raise ValueError(f"任务状态不允许启动: {job.status}")

        # 加载配置
        result = await db.execute(
            select(TrainingJobConfig).where(TrainingJobConfig.job_id == job_id)
        )
        config = result.scalar_one()

        try:
            # 生成K8S Job名称
            k8s_job_name = f"training-{job.id}-{int(datetime.utcnow().timestamp())}"

            # 准备标签
            labels = {
                "app": "ai-training-platform",
                "training-job-id": str(job.id),
                "framework": job.framework.value,
                "job-type": job.job_type.value,
            }

            # 创建K8S Job
            k8s_job = self.job_manager.create_training_job(
                namespace=job.k8s_namespace,
                job_name=k8s_job_name,
                image=config.docker_image,
                command=config.command,
                args=config.args,
                env_vars=config.env_vars,
                node_count=config.node_count,
                gpu_per_node=config.gpu_per_node,
                cpu_per_node=config.cpu_per_node,
                memory_per_node_gb=config.memory_per_node_gb,
                gpu_type=config.gpu_type,
                labels=labels,
                timeout_seconds=config.timeout_seconds,
            )

            # 更新任务状态
            job.status = TrainingJobStatus.QUEUED
            job.k8s_job_name = k8s_job_name
            job.queued_at = datetime.utcnow()

            await db.commit()
            await db.refresh(job)

            logger.info(f"启动训练任务成功: {job.id} - K8S Job: {k8s_job_name}")
            return job

        except Exception as e:
            # 启动失败,更新任务状态
            job.status = TrainingJobStatus.FAILED
            job.error_message = str(e)
            await db.commit()
            logger.error(f"启动训练任务失败: {job.id} - {e}")
            raise

    async def stop_training_job(
        self, db: AsyncSession, job_id: int
    ) -> TrainingJob:
        """停止训练任务

        Args:
            db: 数据库会话
            job_id: 训练任务ID

        Returns:
            TrainingJob: 更新后的训练任务

        Raises:
            ValueError: 任务状态不允许停止
        """
        # 查询训练任务
        result = await db.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"训练任务不存在: {job_id}")

        # 检查任务状态
        if not job.is_active:
            raise ValueError(f"任务状态不允许停止: {job.status}")

        try:
            # 删除K8S Job
            if job.k8s_job_name:
                self.job_manager.delete_job(
                    namespace=job.k8s_namespace,
                    job_name=job.k8s_job_name,
                    propagation_policy="Foreground",  # 前台删除,等待所有Pod删除
                )

            # 更新任务状态
            job.status = TrainingJobStatus.CANCELLED
            job.completed_at = datetime.utcnow()

            await db.commit()
            await db.refresh(job)

            logger.info(f"停止训练任务成功: {job.id}")
            return job

        except Exception as e:
            logger.error(f"停止训练任务失败: {job.id} - {e}")
            raise

    async def delete_training_job(
        self, db: AsyncSession, job_id: int, force: bool = False
    ) -> bool:
        """删除训练任务

        Args:
            db: 数据库会话
            job_id: 训练任务ID
            force: 是否强制删除(活跃任务)

        Returns:
            bool: 删除是否成功

        Raises:
            ValueError: 任务状态不允许删除
        """
        # 查询训练任务
        result = await db.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return False

        # 检查任务状态
        if job.is_active and not force:
            raise ValueError(f"活跃任务不允许删除,使用force=True强制删除")

        try:
            # 如果任务正在运行,先停止
            if job.is_active and job.k8s_job_name:
                self.job_manager.delete_job(
                    namespace=job.k8s_namespace,
                    job_name=job.k8s_job_name,
                )

            # 软删除训练任务(级联删除配置和指标)
            job.deleted_at = datetime.utcnow()
            await db.commit()

            logger.info(f"删除训练任务成功: {job.id}")
            return True

        except Exception as e:
            logger.error(f"删除训练任务失败: {job.id} - {e}")
            raise

    async def get_training_job_status(
        self, db: AsyncSession, job_id: int
    ) -> dict:
        """获取训练任务状态

        Args:
            db: 数据库会话
            job_id: 训练任务ID

        Returns:
            dict: 任务状态信息(包含K8S状态)

        Raises:
            ValueError: 任务不存在
        """
        # 查询训练任务
        result = await db.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"训练任务不存在: {job_id}")

        status = {
            "id": job.id,
            "name": job.name,
            "status": job.status.value,
            "is_active": job.is_active,
            "is_terminal": job.is_terminal,
            "queued_at": job.queued_at.isoformat() if job.queued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "error_message": job.error_message,
            "k8s_job_name": job.k8s_job_name,
        }

        # 如果有K8S Job,查询K8S状态
        if job.k8s_job_name:
            try:
                k8s_status = self.job_manager.get_job_status(
                    namespace=job.k8s_namespace,
                    job_name=job.k8s_job_name,
                )
                if k8s_status:
                    status["k8s_status"] = k8s_status

                    # 查询Pod信息
                    pods = self.pod_manager.list_pods_for_job(
                        namespace=job.k8s_namespace,
                        job_name=job.k8s_job_name,
                    )
                    status["pods"] = [
                        {
                            "name": pod["metadata"]["name"],
                            "phase": pod["status"]["phase"],
                            "start_time": pod["status"].get("start_time"),
                        }
                        for pod in pods
                    ]

            except Exception as e:
                logger.warning(f"查询K8S状态失败: {job_id} - {e}")
                status["k8s_error"] = str(e)

        return status

    async def sync_job_status(self, db: AsyncSession, job_id: int) -> TrainingJob:
        """同步训练任务状态(从K8S)

        Args:
            db: 数据库会话
            job_id: 训练任务ID

        Returns:
            TrainingJob: 更新后的训练任务
        """
        result = await db.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job or not job.k8s_job_name:
            return job

        try:
            # 查询K8S Job状态
            k8s_status = self.job_manager.get_job_status(
                namespace=job.k8s_namespace,
                job_name=job.k8s_job_name,
            )

            if not k8s_status:
                return job

            # 更新任务状态
            if k8s_status["succeeded"] > 0:
                job.status = TrainingJobStatus.COMPLETED
                job.completed_at = k8s_status.get("completion_time") or datetime.utcnow()
            elif k8s_status["failed"] > 0:
                job.status = TrainingJobStatus.FAILED
                job.completed_at = datetime.utcnow()
            elif k8s_status["active"] > 0:
                if job.status == TrainingJobStatus.QUEUED:
                    job.status = TrainingJobStatus.RUNNING
                    job.started_at = k8s_status.get("start_time") or datetime.utcnow()

            # 更新Pod名称列表
            pods = self.pod_manager.list_pods_for_job(
                namespace=job.k8s_namespace,
                job_name=job.k8s_job_name,
            )
            job.k8s_pod_names = [pod["metadata"]["name"] for pod in pods]

            await db.commit()
            await db.refresh(job)

            return job

        except Exception as e:
            logger.error(f"同步任务状态失败: {job_id} - {e}")
            return job


__all__ = ["TrainingJobService"]
