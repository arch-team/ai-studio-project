"""FSx Sync Service - FSx 同步业务逻辑。

提供 FSx 数据仓库同步的高层抽象:
- S3 → FSx 数据同步
- 数据预热 (预加载到 FSx 缓存)
- 缓存释放
- 同步状态查询

支持 SC-005 (S3 到 FSx 同步时间 <10分钟 for 1TB)。
"""

from typing import Any

from src.modules.datasets.domain.exceptions import (
    DatasetNotFoundError,
    FsxSyncTaskNotFoundError,
)
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.infrastructure.fsx import FsxClient


class FsxSyncService:
    """FSx 同步服务 - 管理数据集与 FSx 的同步操作。"""

    def __init__(
        self,
        dataset_repository: IDatasetRepository,
        fsx_client: FsxClient,
    ) -> None:
        """初始化 FSx 同步服务。

        Args:
            dataset_repository: 数据集仓库
            fsx_client: FSx 客户端
        """
        self._dataset_repository = dataset_repository
        self._fsx_client = fsx_client

    async def initiate_s3_to_fsx_sync(
        self,
        dataset_id: int,
    ) -> dict[str, Any]:
        """发起 S3 → FSx 同步。

        创建 FSx Data Repository Task 将数据集从 S3 同步到 FSx。
        仅同步元数据，实际数据按需加载。

        Args:
            dataset_id: 数据集 ID

        Returns:
            同步任务信息 {task_id, status, type}

        Raises:
            DatasetNotFoundError: 数据集不存在
        """
        # 验证数据集存在
        dataset = await self._dataset_repository.get_by_id(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id=dataset_id)

        # 构建同步路径
        sync_path = f"datasets/{dataset_id}/"

        # 创建导入任务
        task = await self._fsx_client.create_import_task(
            paths=[sync_path],
            report_enabled=False,
        )

        return {
            "task_id": task.get("TaskId"),
            "status": task.get("Lifecycle"),
            "type": task.get("Type", "IMPORT"),
            "dataset_id": dataset_id,
            "paths": [sync_path],
        }

    async def get_sync_status(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """获取同步任务状态。

        Args:
            task_id: FSx 任务 ID

        Returns:
            任务状态信息

        Raises:
            FsxSyncTaskNotFoundError: 任务不存在
        """
        task = await self._fsx_client.get_task_status(task_id=task_id)
        if task is None:
            raise FsxSyncTaskNotFoundError(task_id=task_id)

        status_info = task.get("Status", {})
        return {
            "task_id": task.get("TaskId"),
            "status": task.get("Lifecycle"),
            "type": task.get("Type"),
            "progress": {
                "total": status_info.get("TotalCount", 0),
                "succeeded": status_info.get("SucceededCount", 0),
                "failed": status_info.get("FailedCount", 0),
            },
            "paths": task.get("Paths", []),
        }

    async def prefetch_dataset(
        self,
        dataset_id: int,
        paths: list[str] | None = None,
    ) -> dict[str, Any]:
        """预热数据集 (预加载到 FSx 缓存)。

        为训练任务预先加载数据集到 FSx，减少首次访问延迟。

        Args:
            dataset_id: 数据集 ID
            paths: 要预热的子路径列表 (可选，默认整个数据集)

        Returns:
            预热任务信息

        Raises:
            DatasetNotFoundError: 数据集不存在
        """
        # 验证数据集存在
        dataset = await self._dataset_repository.get_by_id(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id=dataset_id)

        # 构建预热路径
        if paths:
            sync_paths = [f"datasets/{dataset_id}/{p}" for p in paths]
        else:
            sync_paths = [f"datasets/{dataset_id}/"]

        # 创建导入任务
        task = await self._fsx_client.create_import_task(
            paths=sync_paths,
            report_enabled=False,
        )

        return {
            "task_id": task.get("TaskId"),
            "status": task.get("Lifecycle"),
            "type": "PREFETCH",
            "dataset_id": dataset_id,
            "paths": sync_paths,
        }

    async def release_dataset(
        self,
        dataset_id: int,
    ) -> dict[str, Any]:
        """释放数据集缓存。

        释放数据集在 FSx 上占用的存储空间。
        数据仍保留在 S3，可在需要时重新加载。

        Args:
            dataset_id: 数据集 ID

        Returns:
            释放任务信息

        Raises:
            DatasetNotFoundError: 数据集不存在
        """
        # 验证数据集存在
        dataset = await self._dataset_repository.get_by_id(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id=dataset_id)

        # 构建释放路径
        release_path = f"datasets/{dataset_id}/"

        # 创建释放任务
        task = await self._fsx_client.create_release_task(
            paths=[release_path],
        )

        return {
            "task_id": task.get("TaskId"),
            "status": task.get("Lifecycle"),
            "type": "RELEASE",
            "dataset_id": dataset_id,
            "paths": [release_path],
        }

    async def get_dataset_fsx_path(
        self,
        dataset_id: int,
    ) -> dict[str, Any]:
        """获取数据集的 FSx 路径信息。

        Args:
            dataset_id: 数据集 ID

        Returns:
            路径信息 {dataset_id, fsx_path, s3_path}

        Raises:
            DatasetNotFoundError: 数据集不存在
        """
        # 验证数据集存在
        dataset = await self._dataset_repository.get_by_id(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id=dataset_id)

        return {
            "dataset_id": dataset_id,
            "fsx_path": self._fsx_client.get_fsx_path_for_dataset(dataset_id),
            "s3_path": self._fsx_client.get_s3_path_for_dataset(dataset_id),
            "storage_uri": dataset.storage_uri,
        }

    async def check_fsx_availability(self) -> dict[str, Any]:
        """检查 FSx 文件系统可用性。

        Returns:
            可用性信息 {available, filesystem_id, storage_capacity_gb, lifecycle}
        """
        try:
            fs_info = await self._fsx_client.describe_filesystem()
            return {
                "available": fs_info.get("Lifecycle") == "AVAILABLE",
                "filesystem_id": fs_info.get("FileSystemId"),
                "storage_capacity_gb": fs_info.get("StorageCapacity"),
                "lifecycle": fs_info.get("Lifecycle"),
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }
