"""Checkpoint分层存储迁移服务

负责checkpoint在NVMe/FSx/S3之间的自动迁移:
- NVMe → FSx: 7天后
- FSx → S3: 30天后
- 最后checkpoint → S3: 立即
"""

import asyncio
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.training import (
    Checkpoint,
    CheckpointStorageType,
    TrainingJob,
    TrainingJobStatus,
)
from services.checkpoint.s3_migration_service import S3MigrationService
from config.settings import settings

logger = logging.getLogger(__name__)


class StorageMigrationService:
    """Checkpoint分层存储迁移服务

    负责checkpoint在NVMe/FSx/S3之间的自动迁移:
    - NVMe → FSx: 7天后
    - FSx → S3: 30天后
    - 最后checkpoint → S3: 立即
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.s3_service = S3MigrationService()

    async def migrate_nvme_to_fsx(
        self,
        checkpoint: Checkpoint,
        delete_source: bool = True,
    ) -> bool:
        """迁移checkpoint从NVMe到FSx

        Args:
            checkpoint: Checkpoint对象
            delete_source: 是否删除源文件

        Returns:
            是否迁移成功
        """
        if checkpoint.storage_type != CheckpointStorageType.LOCAL:
            logger.warning(f"Checkpoint {checkpoint.id} 不在NVMe,跳过迁移")
            return False

        try:
            # 生成FSx路径
            fsx_path = self._generate_fsx_path(checkpoint)

            # 复制文件到FSx
            await asyncio.to_thread(self._copy_file, checkpoint.storage_path, fsx_path)

            # 更新数据库
            old_path = checkpoint.storage_path
            checkpoint.storage_path = fsx_path
            checkpoint.storage_type = CheckpointStorageType.FSX
            await self.session.commit()

            # 删除源文件
            if delete_source:
                await asyncio.to_thread(Path(old_path).unlink, missing_ok=True)
                logger.info(f"删除NVMe源文件: {old_path}")

            logger.info(
                f"Checkpoint {checkpoint.id} 迁移成功: NVMe → FSx ({fsx_path})"
            )
            return True

        except Exception as e:
            logger.error(f"NVMe→FSx迁移失败: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def migrate_fsx_to_s3(
        self,
        checkpoint: Checkpoint,
        delete_source: bool = True,
    ) -> bool:
        """迁移checkpoint从FSx到S3

        Args:
            checkpoint: Checkpoint对象
            delete_source: 是否删除源文件

        Returns:
            是否迁移成功
        """
        if checkpoint.storage_type != CheckpointStorageType.FSX:
            logger.warning(f"Checkpoint {checkpoint.id} 不在FSx,跳过迁移")
            return False

        try:
            # 使用S3MigrationService上传
            s3_uri = await self.s3_service.migrate_to_s3(
                checkpoint=checkpoint, delete_source=delete_source
            )

            # 更新数据库
            checkpoint.storage_path = s3_uri
            checkpoint.storage_type = CheckpointStorageType.S3
            await self.session.commit()

            logger.info(f"Checkpoint {checkpoint.id} 迁移成功: FSx → S3 ({s3_uri})")
            return True

        except Exception as e:
            logger.error(f"FSx→S3迁移失败: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def run_migration_policy(self) -> dict:
        """执行分层存储迁移策略

        定时任务调用,扫描所有checkpoint并根据策略迁移

        Returns:
            迁移统计: {"nvme_to_fsx": N, "fsx_to_s3": M, "errors": E}
        """
        stats = {"nvme_to_fsx": 0, "fsx_to_s3": 0, "errors": 0}

        # 1. NVMe → FSx (配置的天数后)
        nvme_checkpoints = await self._get_old_checkpoints(
            storage_type=CheckpointStorageType.LOCAL,
            older_than_days=settings.checkpoint_migration_nvme_to_fsx_days,
        )

        for ckpt in nvme_checkpoints:
            success = await self.migrate_nvme_to_fsx(ckpt)
            if success:
                stats["nvme_to_fsx"] += 1
            else:
                stats["errors"] += 1

        # 2. FSx → S3 (配置的天数后)
        fsx_checkpoints = await self._get_old_checkpoints(
            storage_type=CheckpointStorageType.FSX,
            older_than_days=settings.checkpoint_migration_fsx_to_s3_days,
        )

        for ckpt in fsx_checkpoints:
            success = await self.migrate_fsx_to_s3(ckpt)
            if success:
                stats["fsx_to_s3"] += 1
            else:
                stats["errors"] += 1

        # 3. 最后checkpoint特殊处理: 训练完成的Job的最后checkpoint立即迁移到S3
        completed_jobs_last_ckpts = (
            await self._get_last_checkpoints_of_completed_jobs()
        )

        for ckpt in completed_jobs_last_ckpts:
            if ckpt.storage_type == CheckpointStorageType.LOCAL:
                await self.migrate_nvme_to_fsx(ckpt, delete_source=False)

            if ckpt.storage_type == CheckpointStorageType.FSX:
                success = await self.migrate_fsx_to_s3(ckpt)
                if success:
                    stats["fsx_to_s3"] += 1

        logger.info(f"分层存储迁移完成: {stats}")
        return stats

    async def _get_old_checkpoints(
        self,
        storage_type: CheckpointStorageType,
        older_than_days: int,
    ) -> list[Checkpoint]:
        """查询旧checkpoint(超过N天)

        Args:
            storage_type: 存储类型
            older_than_days: 天数阈值

        Returns:
            Checkpoint列表
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        query = select(Checkpoint).where(
            Checkpoint.storage_type == storage_type,
            Checkpoint.created_at < cutoff_date,
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_last_checkpoints_of_completed_jobs(self) -> list[Checkpoint]:
        """获取已完成训练任务的最后checkpoint

        Returns:
            Checkpoint列表
        """
        # 查询已完成的训练任务
        completed_jobs_query = select(TrainingJob.id).where(
            TrainingJob.status.in_(
                [
                    TrainingJobStatus.COMPLETED,
                    TrainingJobStatus.FAILED,
                    TrainingJobStatus.CANCELLED,
                ]
            )
        )

        completed_job_ids = (
            await self.session.execute(completed_jobs_query)
        ).scalars().all()

        # 为每个任务查询最后checkpoint
        last_checkpoints = []
        for job_id in completed_job_ids:
            query = (
                select(Checkpoint)
                .where(Checkpoint.job_id == job_id)
                .order_by(Checkpoint.step.desc())
                .limit(1)
            )
            result = await self.session.execute(query)
            ckpt = result.scalar_one_or_none()
            if ckpt and ckpt.storage_type != CheckpointStorageType.S3:
                last_checkpoints.append(ckpt)

        return last_checkpoints

    def _generate_fsx_path(self, checkpoint: Checkpoint) -> str:
        """生成FSx存储路径

        格式: /mnt/fsx/checkpoints/{job_id}/step-{step}.pt
        """
        fsx_mount = settings.checkpoint_fsx_mount
        return f"{fsx_mount}/{checkpoint.job_id}/step-{checkpoint.step}.pt"

    def _copy_file(self, source: str, dest: str) -> None:
        """复制文件(同步操作)

        使用shutil.copy2保留元数据
        """
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        logger.debug(f"文件复制成功: {source} → {dest}")


__all__ = ["StorageMigrationService"]
