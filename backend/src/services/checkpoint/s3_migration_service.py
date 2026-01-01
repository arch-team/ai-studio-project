"""Checkpoint S3迁移服务

负责将FSx/Local checkpoint迁移到S3长期存储
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from config.settings import settings
from models.training import Checkpoint, CheckpointStorageType

logger = logging.getLogger(__name__)


class S3MigrationService:
    """Checkpoint S3迁移服务

    负责将FSx/Local checkpoint迁移到S3长期存储
    """

    def __init__(self):
        """初始化S3客户端"""
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bucket_name = (
            settings.s3_bucket or "ai-platform-checkpoints"
        )  # 从settings获取

    async def migrate_to_s3(
        self,
        checkpoint: Checkpoint,
        delete_source: bool = False,
    ) -> str:
        """迁移checkpoint到S3

        Args:
            checkpoint: Checkpoint对象
            delete_source: 是否删除源文件(迁移后清理本地/FSx)

        Returns:
            S3 URI (s3://bucket/key)

        Raises:
            ValueError: checkpoint已经在S3上
            FileNotFoundError: 源文件不存在
            ClientError: S3上传失败
        """
        # 检查checkpoint是否已在S3
        if checkpoint.storage_type == CheckpointStorageType.S3:
            logger.warning(
                f"Checkpoint已在S3,无需迁移: id={checkpoint.id}, "
                f"path={checkpoint.storage_path}"
            )
            raise ValueError("Checkpoint已在S3,无需迁移")

        # 验证源文件存在
        source_path = Path(checkpoint.storage_path)
        if not source_path.exists():
            logger.error(
                f"源文件不存在,无法迁移: id={checkpoint.id}, "
                f"path={checkpoint.storage_path}"
            )
            raise FileNotFoundError(f"源文件不存在: {checkpoint.storage_path}")

        # 生成S3 key: checkpoints/{job_id}/step-{step}.tar
        s3_key = (
            f"checkpoints/{checkpoint.job_id}/"
            f"step-{checkpoint.step}-{checkpoint.id}.pt"
        )

        try:
            # 上传到S3 (使用asyncio.to_thread包装同步操作)
            await asyncio.to_thread(
                self.s3_client.upload_file,
                str(source_path),
                self.bucket_name,
                s3_key,
            )

            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(
                f"Checkpoint迁移到S3成功: id={checkpoint.id}, "
                f"source={checkpoint.storage_path}, s3_uri={s3_uri}"
            )

            # 可选: 删除源文件(FSx/Local)
            if delete_source:
                await self._delete_source_file(source_path)
                logger.info(
                    f"删除源文件成功: id={checkpoint.id}, " f"path={source_path}"
                )

            return s3_uri

        except ClientError as e:
            logger.error(
                f"S3上传失败: id={checkpoint.id}, error={e}", exc_info=True
            )
            raise

    async def download_from_s3(
        self,
        checkpoint: Checkpoint,
        local_path: str,
    ) -> str:
        """从S3下载checkpoint到本地

        Args:
            checkpoint: Checkpoint对象(必须是S3类型)
            local_path: 本地下载路径

        Returns:
            本地文件路径

        Raises:
            ValueError: checkpoint不在S3上
            ClientError: S3下载失败
        """
        if checkpoint.storage_type != CheckpointStorageType.S3:
            raise ValueError("Checkpoint不在S3上,无法下载")

        # 从S3 URI提取bucket和key
        s3_uri = checkpoint.storage_path
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"无效的S3 URI: {s3_uri}")

        # 解析S3 URI: s3://bucket/key
        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        # 确保本地目录存在
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 从S3下载 (使用asyncio.to_thread包装同步操作)
            await asyncio.to_thread(
                self.s3_client.download_file,
                bucket,
                key,
                str(local_file),
            )

            logger.info(
                f"从S3下载checkpoint成功: id={checkpoint.id}, "
                f"s3_uri={s3_uri}, local={local_file}"
            )
            return str(local_file)

        except ClientError as e:
            logger.error(
                f"S3下载失败: id={checkpoint.id}, error={e}", exc_info=True
            )
            raise

    async def delete_from_s3(self, checkpoint: Checkpoint) -> bool:
        """从S3删除checkpoint

        Args:
            checkpoint: Checkpoint对象(必须是S3类型)

        Returns:
            删除成功返回True

        Raises:
            ValueError: checkpoint不在S3上
            ClientError: S3删除失败
        """
        if checkpoint.storage_type != CheckpointStorageType.S3:
            raise ValueError("Checkpoint不在S3上,无法删除")

        # 从S3 URI提取bucket和key
        s3_uri = checkpoint.storage_path
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"无效的S3 URI: {s3_uri}")

        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        try:
            # 从S3删除
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=bucket,
                Key=key,
            )

            logger.info(
                f"从S3删除checkpoint成功: id={checkpoint.id}, s3_uri={s3_uri}"
            )
            return True

        except ClientError as e:
            logger.error(
                f"S3删除失败: id={checkpoint.id}, error={e}", exc_info=True
            )
            raise

    async def _delete_source_file(self, file_path: Path) -> None:
        """删除源文件(私有方法)

        Args:
            file_path: 文件路径
        """
        try:
            await asyncio.to_thread(file_path.unlink)
        except Exception as e:
            logger.warning(f"删除源文件失败: path={file_path}, error={e}")

    async def check_s3_object_exists(self, s3_uri: str) -> bool:
        """检查S3对象是否存在

        Args:
            s3_uri: S3 URI (s3://bucket/key)

        Returns:
            存在返回True,否则返回False
        """
        if not s3_uri.startswith("s3://"):
            return False

        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        try:
            await asyncio.to_thread(
                self.s3_client.head_object,
                Bucket=bucket,
                Key=key,
            )
            return True
        except ClientError:
            return False


__all__ = ["S3MigrationService"]
