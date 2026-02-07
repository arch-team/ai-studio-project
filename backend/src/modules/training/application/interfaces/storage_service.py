"""检查点存储服务接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StorageInfo:
    """存储信息"""

    path: str
    size_bytes: int
    checksum: str
    storage_tier: str | None = None


class IStorageService(ABC):
    """检查点存储服务接口 (T038)

    提供检查点的存储层操作能力，支持 NVMe、FSx、S3 三层存储。
    负责检查点文件的保存、迁移和完整性验证。
    """

    @abstractmethod
    async def check_nvme_available(self, job_id: int) -> bool:
        """检查 NVMe 存储是否可用

        Args:
            job_id: 训练任务 ID

        Returns:
            bool: NVMe 存储是否可用
        """

    @abstractmethod
    async def check_fsx_available(self, job_id: int) -> bool:
        """检查 FSx 存储是否可用

        Args:
            job_id: 训练任务 ID

        Returns:
            bool: FSx 存储是否可用
        """

    @abstractmethod
    async def get_storage_path(
        self,
        job_id: int,
        checkpoint_name: str,
        storage_tier: str,
    ) -> str:
        """生成检查点存储路径

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            storage_tier: 存储层级 (NVME, FSX, S3)

        Returns:
            str: 完整存储路径
        """

    @abstractmethod
    async def save_checkpoint(
        self,
        job_id: int,
        checkpoint_name: str,
        data: bytes,
        storage_tier: str,
    ) -> StorageInfo:
        """保存检查点到指定存储层

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            data: 检查点数据
            storage_tier: 存储层级

        Returns:
            StorageInfo: 存储信息
        """

    @abstractmethod
    async def load_checkpoint(
        self,
        job_id: int,
        checkpoint_name: str,
        storage_tier: str,
    ) -> bytes:
        """从指定存储层加载检查点

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            storage_tier: 存储层级

        Returns:
            bytes: 检查点数据
        """

    @abstractmethod
    async def migrate_checkpoint(
        self,
        job_id: int,
        checkpoint_name: str,
        from_tier: str,
        to_tier: str,
    ) -> StorageInfo:
        """在存储层之间迁移检查点

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            from_tier: 源存储层级
            to_tier: 目标存储层级

        Returns:
            StorageInfo: 新存储信息
        """

    @abstractmethod
    async def delete_checkpoint(
        self,
        job_id: int,
        checkpoint_name: str,
        storage_tier: str,
    ) -> None:
        """删除指定存储层的检查点

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            storage_tier: 存储层级
        """

    @abstractmethod
    async def list_checkpoints(
        self,
        job_id: int,
        storage_tier: str | None = None,
    ) -> list[StorageInfo]:
        """列出任务的所有检查点

        Args:
            job_id: 训练任务 ID
            storage_tier: 存储层级，None 表示所有层级

        Returns:
            list[StorageInfo]: 检查点存储信息列表
        """

    @abstractmethod
    async def verify_checkpoint_integrity(
        self,
        job_id: int,
        checkpoint_name: str,
        storage_tier: str,
        expected_checksum: str,
    ) -> bool:
        """验证检查点完整性

        Args:
            job_id: 训练任务 ID
            checkpoint_name: 检查点名称
            storage_tier: 存储层级
            expected_checksum: 预期校验和

        Returns:
            bool: 完整性验证是否通过
        """
