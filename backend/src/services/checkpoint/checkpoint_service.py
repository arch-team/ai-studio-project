"""检查点管理服务

提供训练检查点的创建、查询、删除和存储管理功能
支持分层存储策略: Local NVMe -> FSx -> S3
"""

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.training import Checkpoint, CheckpointStorageType, TrainingJob

logger = logging.getLogger(__name__)


class CheckpointService:
    """检查点服务

    功能:
    1. 注册checkpoint到数据库
    2. 列举任务的所有checkpoint
    3. 获取最新checkpoint (用于恢复训练)
    4. 删除旧checkpoint (清理策略)

    Args:
        session: 异步数据库会话
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_checkpoint(
        self,
        job_id: int,
        step: int,
        storage_path: str,
        storage_type: CheckpointStorageType,
        size_bytes: int,
        epoch: Optional[int] = None,
        metadata: Optional[dict] = None,
        metrics: Optional[dict] = None,
    ) -> Checkpoint:
        """注册新的checkpoint

        训练脚本保存checkpoint后调用此接口记录到数据库

        Args:
            job_id: 训练任务ID
            step: 训练步数
            storage_path: 存储路径(绝对路径或S3 URI)
            storage_type: 存储类型(LOCAL/FSX/S3)
            size_bytes: 文件大小(字节)
            epoch: 训练轮次(可选)
            metadata: 元数据(学习率、优化器配置等)
            metrics: 训练指标快照(loss, accuracy等)

        Returns:
            创建的Checkpoint对象

        Raises:
            ValueError: 训练任务不存在
        """
        # 验证训练任务存在
        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"训练任务不存在: job_id={job_id}")

        # 创建checkpoint记录
        checkpoint = Checkpoint(
            job_id=job_id,
            step=step,
            epoch=epoch,
            storage_path=storage_path,
            storage_type=storage_type,
            size_bytes=size_bytes,
            checkpoint_metadata=metadata or {},
            checkpoint_metrics=metrics,
        )

        self.session.add(checkpoint)
        await self.session.commit()
        await self.session.refresh(checkpoint)

        logger.info(
            f"注册checkpoint成功: job={job_id}, step={step}, "
            f"type={storage_type.value}, size={size_bytes}bytes"
        )
        return checkpoint

    async def list_checkpoints(
        self,
        job_id: int,
        storage_type: Optional[CheckpointStorageType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Checkpoint]:
        """列举训练任务的checkpoint

        Args:
            job_id: 训练任务ID
            storage_type: 存储类型过滤(可选,如只查询S3上的checkpoint)
            limit: 最大返回数量
            offset: 偏移量

        Returns:
            Checkpoint列表(按step降序排列,最新的在前)
        """
        query = select(Checkpoint).where(Checkpoint.job_id == job_id)

        # 可选的存储类型过滤
        if storage_type:
            query = query.where(Checkpoint.storage_type == storage_type)

        # 按step降序排列(最新的checkpoint在前)
        query = query.order_by(Checkpoint.step.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        checkpoints = list(result.scalars().all())

        logger.debug(
            f"列举checkpoint: job={job_id}, type={storage_type}, "
            f"count={len(checkpoints)}"
        )
        return checkpoints

    async def get_checkpoint_by_id(self, checkpoint_id: int) -> Optional[Checkpoint]:
        """根据ID获取checkpoint

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint对象,不存在返回None
        """
        result = await self.session.execute(
            select(Checkpoint).where(Checkpoint.id == checkpoint_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_checkpoint(
        self,
        job_id: int,
        storage_type: Optional[CheckpointStorageType] = None,
    ) -> Optional[Checkpoint]:
        """获取最新checkpoint(用于恢复训练)

        优先查找LOCAL/FSX,最后查S3(按性能排序)

        Args:
            job_id: 训练任务ID
            storage_type: 存储类型过滤(可选)

        Returns:
            最新Checkpoint对象,无则返回None
        """
        checkpoints = await self.list_checkpoints(
            job_id=job_id, storage_type=storage_type, limit=1
        )
        checkpoint = checkpoints[0] if checkpoints else None

        if checkpoint:
            logger.info(
                f"获取最新checkpoint: job={job_id}, step={checkpoint.step}, "
                f"type={checkpoint.storage_type.value}"
            )
        else:
            logger.warning(f"未找到checkpoint: job={job_id}")

        return checkpoint

    async def get_checkpoint_by_step(
        self, job_id: int, step: int
    ) -> Optional[Checkpoint]:
        """根据step获取checkpoint

        Args:
            job_id: 训练任务ID
            step: 训练步数

        Returns:
            Checkpoint对象,不存在返回None
        """
        result = await self.session.execute(
            select(Checkpoint).where(
                Checkpoint.job_id == job_id, Checkpoint.step == step
            )
        )
        return result.scalar_one_or_none()

    async def delete_checkpoint(self, checkpoint_id: int) -> bool:
        """删除单个checkpoint

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            删除成功返回True,不存在返回False
        """
        checkpoint = await self.get_checkpoint_by_id(checkpoint_id)
        if not checkpoint:
            logger.warning(f"Checkpoint不存在,无法删除: id={checkpoint_id}")
            return False

        await self.session.delete(checkpoint)
        await self.session.commit()

        logger.info(
            f"删除checkpoint成功: id={checkpoint_id}, job={checkpoint.job_id}, "
            f"step={checkpoint.step}"
        )
        return True

    async def delete_old_checkpoints(
        self,
        job_id: int,
        keep_last_n: int = 5,
        storage_type: Optional[CheckpointStorageType] = None,
    ) -> int:
        """删除旧checkpoint(保留最近N个)

        清理策略: 保留最近N个checkpoint,删除其余

        Args:
            job_id: 训练任务ID
            keep_last_n: 保留最近N个checkpoint (默认5个)
            storage_type: 存储类型过滤(可选,如只清理LOCAL checkpoint)

        Returns:
            删除的checkpoint数量
        """
        # 获取所有checkpoint (按step降序)
        checkpoints = await self.list_checkpoints(
            job_id=job_id, storage_type=storage_type, limit=1000  # 假设不会超过1000个
        )

        if len(checkpoints) <= keep_last_n:
            logger.debug(
                f"Checkpoint数量({len(checkpoints)}) <= 保留数量({keep_last_n}), "
                f"无需清理"
            )
            return 0

        # 保留最近keep_last_n个,删除其余
        to_delete = checkpoints[keep_last_n:]
        deleted_count = 0

        for ckpt in to_delete:
            await self.session.delete(ckpt)
            logger.info(
                f"删除旧checkpoint: id={ckpt.id}, job={job_id}, step={ckpt.step}, "
                f"type={ckpt.storage_type.value}"
            )
            deleted_count += 1

        await self.session.commit()

        logger.info(
            f"清理旧checkpoint完成: job={job_id}, deleted={deleted_count}, "
            f"kept={keep_last_n}"
        )
        return deleted_count

    async def count_checkpoints(
        self,
        job_id: int,
        storage_type: Optional[CheckpointStorageType] = None,
    ) -> int:
        """统计checkpoint数量

        Args:
            job_id: 训练任务ID
            storage_type: 存储类型过滤(可选)

        Returns:
            Checkpoint数量
        """
        checkpoints = await self.list_checkpoints(
            job_id=job_id, storage_type=storage_type, limit=10000
        )
        return len(checkpoints)

    def generate_checkpoint_path(
        self,
        job_id: int,
        step: int,
        storage_type: CheckpointStorageType,
        local_dir: str = "/mnt/nvme/checkpoints",
        fsx_dir: str = "/mnt/fsx/checkpoints",
        s3_bucket: str = "ai-platform-checkpoints",
    ) -> str:
        """生成checkpoint存储路径

        辅助方法,用于生成规范的checkpoint存储路径

        Args:
            job_id: 训练任务ID
            step: 训练步数
            storage_type: 存储类型
            local_dir: NVMe本地存储根目录
            fsx_dir: FSx存储根目录
            s3_bucket: S3存储桶名称

        Returns:
            完整存储路径 (本地路径或S3 URI)
        """
        checkpoint_filename = f"checkpoint-step-{step}.pt"

        if storage_type == CheckpointStorageType.LOCAL:
            path = Path(local_dir) / str(job_id) / checkpoint_filename
            return str(path)
        elif storage_type == CheckpointStorageType.FSX:
            path = Path(fsx_dir) / str(job_id) / checkpoint_filename
            return str(path)
        else:  # S3
            return f"s3://{s3_bucket}/checkpoints/{job_id}/{checkpoint_filename}"


__all__ = ["CheckpointService"]
