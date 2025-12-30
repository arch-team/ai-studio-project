"""模型存储服务

处理模型文件的上传、下载和存储管理
"""

import hashlib
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from config.settings import settings

logger = logging.getLogger(__name__)


class ModelStorageService:
    """模型存储服务

    负责模型文件的本地存储管理(未来可扩展为对象存储)
    """

    def __init__(self, base_storage_path: str | None = None):
        """初始化存储服务

        Args:
            base_storage_path: 存储根路径,默认使用配置中的路径
        """
        self.base_path = Path(base_storage_path or settings.model_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"模型存储服务初始化: {self.base_path}")

    def _get_model_dir(self, model_id: int, version: str) -> Path:
        """获取模型版本的存储目录

        Args:
            model_id: 模型ID
            version: 版本号

        Returns:
            Path: 存储目录路径
        """
        return self.base_path / f"model_{model_id}" / version

    def save_model_file(
        self,
        model_id: int,
        version: str,
        file_stream: BinaryIO,
        filename: str,
    ) -> tuple[str, int, str]:
        """保存模型文件

        Args:
            model_id: 模型ID
            version: 版本号
            file_stream: 文件流
            filename: 文件名

        Returns:
            tuple: (存储路径, 文件大小字节, MD5校验和)
        """
        try:
            # 创建目录
            model_dir = self._get_model_dir(model_id, version)
            model_dir.mkdir(parents=True, exist_ok=True)

            # 保存文件并计算MD5
            file_path = model_dir / filename
            md5_hash = hashlib.md5()
            file_size = 0

            with open(file_path, "wb") as f:
                while chunk := file_stream.read(8192):
                    f.write(chunk)
                    md5_hash.update(chunk)
                    file_size += len(chunk)

            storage_path = str(file_path.relative_to(self.base_path))
            checksum = md5_hash.hexdigest()

            logger.info(
                f"保存模型文件成功: model_id={model_id}, version={version}, "
                f"size={file_size}, md5={checksum}"
            )

            return storage_path, file_size, checksum

        except Exception as e:
            logger.error(f"保存模型文件失败: {e}")
            raise

    def save_model_directory(
        self,
        model_id: int,
        version: str,
        source_dir: Path,
    ) -> tuple[str, int]:
        """保存模型目录(用于从训练任务输出复制)

        Args:
            model_id: 模型ID
            version: 版本号
            source_dir: 源目录路径

        Returns:
            tuple: (存储路径, 总大小字节)
        """
        try:
            model_dir = self._get_model_dir(model_id, version)

            # 如果目标目录存在,先删除
            if model_dir.exists():
                shutil.rmtree(model_dir)

            # 复制整个目录
            shutil.copytree(source_dir, model_dir)

            # 计算总大小
            total_size = sum(
                f.stat().st_size for f in model_dir.rglob("*") if f.is_file()
            )

            storage_path = str(model_dir.relative_to(self.base_path))

            logger.info(
                f"复制模型目录成功: model_id={model_id}, version={version}, "
                f"size={total_size}"
            )

            return storage_path, total_size

        except Exception as e:
            logger.error(f"复制模型目录失败: {e}")
            raise

    def get_model_file_path(self, storage_path: str) -> Path:
        """获取模型文件的完整路径

        Args:
            storage_path: 存储路径(相对路径)

        Returns:
            Path: 完整文件路径
        """
        return self.base_path / storage_path

    def verify_file_checksum(self, storage_path: str, expected_md5: str) -> bool:
        """验证文件MD5校验和

        Args:
            storage_path: 存储路径
            expected_md5: 期望的MD5值

        Returns:
            bool: 校验是否通过
        """
        try:
            file_path = self.get_model_file_path(storage_path)

            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False

            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    md5_hash.update(chunk)

            actual_md5 = md5_hash.hexdigest()
            is_valid = actual_md5 == expected_md5

            if not is_valid:
                logger.warning(
                    f"文件校验失败: expected={expected_md5}, actual={actual_md5}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"校验文件失败: {e}")
            return False

    def delete_model_version(self, model_id: int, version: str) -> bool:
        """删除模型版本的所有文件

        Args:
            model_id: 模型ID
            version: 版本号

        Returns:
            bool: 删除是否成功
        """
        try:
            model_dir = self._get_model_dir(model_id, version)

            if model_dir.exists():
                shutil.rmtree(model_dir)
                logger.info(f"删除模型版本目录成功: {model_dir}")
                return True
            else:
                logger.warning(f"模型版本目录不存在: {model_dir}")
                return False

        except Exception as e:
            logger.error(f"删除模型版本目录失败: {e}")
            raise

    def delete_model(self, model_id: int) -> bool:
        """删除模型的所有版本文件

        Args:
            model_id: 模型ID

        Returns:
            bool: 删除是否成功
        """
        try:
            model_dir = self.base_path / f"model_{model_id}"

            if model_dir.exists():
                shutil.rmtree(model_dir)
                logger.info(f"删除模型目录成功: {model_dir}")
                return True
            else:
                logger.warning(f"模型目录不存在: {model_dir}")
                return False

        except Exception as e:
            logger.error(f"删除模型目录失败: {e}")
            raise

    def list_model_files(self, model_id: int, version: str) -> list[dict]:
        """列出模型版本的所有文件

        Args:
            model_id: 模型ID
            version: 版本号

        Returns:
            list: 文件信息列表
        """
        try:
            model_dir = self._get_model_dir(model_id, version)

            if not model_dir.exists():
                return []

            files = []
            for file_path in model_dir.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(model_dir)),
                        "size": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })

            return files

        except Exception as e:
            logger.error(f"列出模型文件失败: {e}")
            raise

    def get_storage_stats(self, model_id: int | None = None) -> dict:
        """获取存储统计信息

        Args:
            model_id: 可选的模型ID,None表示统计所有模型

        Returns:
            dict: 统计信息
        """
        try:
            if model_id:
                target_dir = self.base_path / f"model_{model_id}"
            else:
                target_dir = self.base_path

            if not target_dir.exists():
                return {
                    "total_size": 0,
                    "file_count": 0,
                    "version_count": 0,
                }

            total_size = 0
            file_count = 0
            version_count = 0

            if model_id:
                # 统计单个模型
                version_dirs = [d for d in target_dir.iterdir() if d.is_dir()]
                version_count = len(version_dirs)
                for version_dir in version_dirs:
                    for file_path in version_dir.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
            else:
                # 统计所有模型
                for model_dir in target_dir.iterdir():
                    if model_dir.is_dir() and model_dir.name.startswith("model_"):
                        version_dirs = [d for d in model_dir.iterdir() if d.is_dir()]
                        version_count += len(version_dirs)
                        for version_dir in version_dirs:
                            for file_path in version_dir.rglob("*"):
                                if file_path.is_file():
                                    total_size += file_path.stat().st_size
                                    file_count += 1

            return {
                "total_size": total_size,
                "file_count": file_count,
                "version_count": version_count,
            }

        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            raise


__all__ = ["ModelStorageService"]
