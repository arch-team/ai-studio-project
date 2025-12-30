"""模型管理服务

处理模型和模型版本的业务逻辑
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Model, ModelVersion, ModelDeployment, User, Project, TrainingJob
from models import ModelStatus, ModelFramework
from services.storage.model_storage import ModelStorageService

logger = logging.getLogger(__name__)


class ModelService:
    """模型管理服务

    负责模型和版本的创建、查询、更新、删除等业务逻辑
    """

    def __init__(self, storage_service: ModelStorageService):
        """初始化服务

        Args:
            storage_service: 模型存储服务
        """
        self.storage = storage_service

    async def create_model(
        self,
        db: AsyncSession,
        name: str,
        framework: ModelFramework,
        project_id: int,
        creator_id: int,
        description: str | None = None,
        task_type: str | None = None,
        source_training_job_id: int | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> Model:
        """创建新模型

        Args:
            db: 数据库会话
            name: 模型名称
            framework: 模型框架
            project_id: 所属项目ID
            creator_id: 创建者ID
            description: 描述
            task_type: 任务类型
            source_training_job_id: 来源训练任务ID
            tags: 标签列表
            metadata: 元数据

        Returns:
            Model: 创建的模型
        """
        try:
            # 验证项目存在
            project = await db.get(Project, project_id)
            if not project or project.deleted_at is not None:
                raise ValueError(f"项目不存在: {project_id}")

            # 验证创建者存在
            creator = await db.get(User, creator_id)
            if not creator or creator.deleted_at is not None:
                raise ValueError(f"用户不存在: {creator_id}")

            # 如果有来源训练任务,验证其存在
            if source_training_job_id:
                job = await db.get(TrainingJob, source_training_job_id)
                if not job or job.deleted_at is not None:
                    raise ValueError(f"训练任务不存在: {source_training_job_id}")

            # 创建模型
            model = Model(
                name=name,
                description=description,
                framework=framework,
                task_type=task_type,
                project_id=project_id,
                creator_id=creator_id,
                source_training_job_id=source_training_job_id,
                tags=tags,
                metadata=metadata,
            )

            db.add(model)
            await db.commit()
            await db.refresh(model)

            logger.info(f"创建模型成功: id={model.id}, name={name}, framework={framework}")

            return model

        except Exception as e:
            await db.rollback()
            logger.error(f"创建模型失败: {e}")
            raise

    async def get_model(
        self,
        db: AsyncSession,
        model_id: int,
        load_versions: bool = False,
    ) -> Model | None:
        """获取模型详情

        Args:
            db: 数据库会话
            model_id: 模型ID
            load_versions: 是否加载版本列表

        Returns:
            Model | None: 模型对象或None
        """
        query = select(Model).where(
            and_(
                Model.id == model_id,
                Model.deleted_at.is_(None)
            )
        )

        if load_versions:
            query = query.options(selectinload(Model.versions))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_models(
        self,
        db: AsyncSession,
        project_id: int | None = None,
        framework: ModelFramework | None = None,
        task_type: str | None = None,
        creator_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Model], int]:
        """查询模型列表

        Args:
            db: 数据库会话
            project_id: 项目ID过滤
            framework: 框架过滤
            task_type: 任务类型过滤
            creator_id: 创建者过滤
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            tuple: (模型列表, 总数)
        """
        # 构建查询条件
        conditions = [Model.deleted_at.is_(None)]

        if project_id:
            conditions.append(Model.project_id == project_id)
        if framework:
            conditions.append(Model.framework == framework)
        if task_type:
            conditions.append(Model.task_type == task_type)
        if creator_id:
            conditions.append(Model.creator_id == creator_id)

        # 查询总数
        count_query = select(func.count(Model.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询列表
        query = (
            select(Model)
            .where(and_(*conditions))
            .order_by(Model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        models = list(result.scalars().all())

        return models, total

    async def update_model(
        self,
        db: AsyncSession,
        model_id: int,
        **update_data,
    ) -> Model:
        """更新模型信息

        Args:
            db: 数据库会话
            model_id: 模型ID
            **update_data: 更新字段

        Returns:
            Model: 更新后的模型
        """
        model = await self.get_model(db, model_id)
        if not model:
            raise ValueError(f"模型不存在: {model_id}")

        # 更新字段
        for key, value in update_data.items():
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)

        await db.commit()
        await db.refresh(model)

        logger.info(f"更新模型成功: id={model_id}")

        return model

    async def delete_model(
        self,
        db: AsyncSession,
        model_id: int,
        force: bool = False,
    ) -> bool:
        """删除模型(软删除或硬删除)

        Args:
            db: 数据库会话
            model_id: 模型ID
            force: 是否强制删除(硬删除存储文件)

        Returns:
            bool: 删除是否成功
        """
        model = await self.get_model(db, model_id, load_versions=True)
        if not model:
            raise ValueError(f"模型不存在: {model_id}")

        try:
            # 软删除数据库记录
            model.deleted_at = datetime.utcnow()

            # 软删除所有版本
            for version in model.versions:
                if version.deleted_at is None:
                    version.deleted_at = datetime.utcnow()

            await db.commit()

            # 如果强制删除,删除存储文件
            if force:
                self.storage.delete_model(model_id)

            logger.info(f"删除模型成功: id={model_id}, force={force}")

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"删除模型失败: {e}")
            raise

    async def create_model_version(
        self,
        db: AsyncSession,
        model_id: int,
        version: str,
        file_stream: BinaryIO | None = None,
        filename: str | None = None,
        source_dir: Path | None = None,
        description: str | None = None,
        model_format: str | None = None,
        model_architecture: str | None = None,
        metrics: dict | None = None,
        hyperparameters: dict | None = None,
        dependencies: dict | None = None,
    ) -> ModelVersion:
        """创建模型版本

        Args:
            db: 数据库会话
            model_id: 模型ID
            version: 版本号
            file_stream: 文件流(单文件上传)
            filename: 文件名(单文件上传)
            source_dir: 源目录(从训练任务复制)
            description: 版本描述
            model_format: 模型格式
            model_architecture: 模型架构
            metrics: 性能指标
            hyperparameters: 超参数
            dependencies: 依赖信息

        Returns:
            ModelVersion: 创建的模型版本
        """
        # 验证模型存在
        model = await self.get_model(db, model_id)
        if not model:
            raise ValueError(f"模型不存在: {model_id}")

        # 检查版本是否已存在
        existing = await db.execute(
            select(ModelVersion).where(
                and_(
                    ModelVersion.model_id == model_id,
                    ModelVersion.version == version,
                    ModelVersion.deleted_at.is_(None)
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"版本已存在: {version}")

        try:
            # 创建版本记录(初始状态为UPLOADING)
            model_version = ModelVersion(
                model_id=model_id,
                version=version,
                description=description,
                status=ModelStatus.UPLOADING,
                storage_path="",  # 待更新
                model_format=model_format,
                model_architecture=model_architecture,
                metrics=metrics,
                hyperparameters=hyperparameters,
                dependencies=dependencies,
            )

            db.add(model_version)
            await db.flush()  # 获取ID但不提交

            # 保存文件
            if file_stream and filename:
                # 单文件上传
                storage_path, file_size, checksum = self.storage.save_model_file(
                    model_id, version, file_stream, filename
                )
                model_version.storage_path = storage_path
                model_version.storage_size_bytes = file_size
                model_version.checksum_md5 = checksum

            elif source_dir:
                # 从目录复制
                storage_path, total_size = self.storage.save_model_directory(
                    model_id, version, source_dir
                )
                model_version.storage_path = storage_path
                model_version.storage_size_bytes = total_size

            else:
                raise ValueError("必须提供file_stream+filename或source_dir")

            # 更新状态为AVAILABLE
            model_version.status = ModelStatus.AVAILABLE

            # 更新模型的最新版本
            model.latest_version = version
            model.latest_version_id = model_version.id

            await db.commit()
            await db.refresh(model_version)

            logger.info(
                f"创建模型版本成功: model_id={model_id}, version={version}, "
                f"size={model_version.storage_size_bytes}"
            )

            return model_version

        except Exception as e:
            await db.rollback()
            # 标记为失败
            if model_version.id:
                model_version.status = ModelStatus.FAILED
                model_version.error_message = str(e)
                await db.commit()

            logger.error(f"创建模型版本失败: {e}")
            raise

    async def get_model_version(
        self,
        db: AsyncSession,
        version_id: int,
    ) -> ModelVersion | None:
        """获取模型版本详情

        Args:
            db: 数据库会话
            version_id: 版本ID

        Returns:
            ModelVersion | None: 版本对象或None
        """
        result = await db.execute(
            select(ModelVersion).where(
                and_(
                    ModelVersion.id == version_id,
                    ModelVersion.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_model_versions(
        self,
        db: AsyncSession,
        model_id: int,
        status: ModelStatus | None = None,
    ) -> list[ModelVersion]:
        """查询模型的所有版本

        Args:
            db: 数据库会话
            model_id: 模型ID
            status: 状态过滤

        Returns:
            list[ModelVersion]: 版本列表
        """
        conditions = [
            ModelVersion.model_id == model_id,
            ModelVersion.deleted_at.is_(None)
        ]

        if status:
            conditions.append(ModelVersion.status == status)

        query = (
            select(ModelVersion)
            .where(and_(*conditions))
            .order_by(ModelVersion.created_at.desc())
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_model_version(
        self,
        db: AsyncSession,
        version_id: int,
        **update_data,
    ) -> ModelVersion:
        """更新模型版本信息

        Args:
            db: 数据库会话
            version_id: 版本ID
            **update_data: 更新字段

        Returns:
            ModelVersion: 更新后的版本
        """
        version = await self.get_model_version(db, version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")

        # 更新字段
        for key, value in update_data.items():
            if hasattr(version, key) and value is not None:
                setattr(version, key, value)

        await db.commit()
        await db.refresh(version)

        logger.info(f"更新模型版本成功: id={version_id}")

        return version

    async def publish_model_version(
        self,
        db: AsyncSession,
        version_id: int,
        publisher_id: int,
    ) -> ModelVersion:
        """发布模型版本

        Args:
            db: 数据库会话
            version_id: 版本ID
            publisher_id: 发布者ID

        Returns:
            ModelVersion: 发布后的版本
        """
        version = await self.get_model_version(db, version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")

        if version.status != ModelStatus.AVAILABLE:
            raise ValueError(f"只能发布AVAILABLE状态的版本,当前状态: {version.status}")

        version.is_published = True
        version.published_at = datetime.utcnow()
        version.published_by_id = publisher_id

        await db.commit()
        await db.refresh(version)

        logger.info(f"发布模型版本成功: id={version_id}")

        return version

    async def delete_model_version(
        self,
        db: AsyncSession,
        version_id: int,
        force: bool = False,
    ) -> bool:
        """删除模型版本

        Args:
            db: 数据库会话
            version_id: 版本ID
            force: 是否强制删除(硬删除存储文件)

        Returns:
            bool: 删除是否成功
        """
        version = await self.get_model_version(db, version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")

        try:
            # 软删除
            version.deleted_at = datetime.utcnow()
            await db.commit()

            # 如果强制删除,删除存储文件
            if force:
                self.storage.delete_model_version(version.model_id, version.version)

            logger.info(f"删除模型版本成功: id={version_id}, force={force}")

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"删除模型版本失败: {e}")
            raise

    async def get_model_files(
        self,
        model_id: int,
        version: str,
    ) -> list[dict]:
        """获取模型版本的文件列表

        Args:
            model_id: 模型ID
            version: 版本号

        Returns:
            list[dict]: 文件信息列表
        """
        return self.storage.list_model_files(model_id, version)

    async def get_storage_stats(
        self,
        model_id: int | None = None,
    ) -> dict:
        """获取存储统计信息

        Args:
            model_id: 模型ID(None表示所有模型)

        Returns:
            dict: 统计信息
        """
        return self.storage.get_storage_stats(model_id)


__all__ = ["ModelService"]
