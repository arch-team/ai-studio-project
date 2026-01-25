"""FSx for Lustre Client - FSx 文件系统集成。

提供 FSx Data Repository Task API 封装:
- S3 → FSx 数据导入 (IMPORT_METADATA_FROM_REPOSITORY)
- FSx 缓存释放 (RELEASE_DATA_FROM_FILESYSTEM)
- 任务状态查询
- 文件系统信息查询

支持 SC-005 (S3 到 FSx 同步时间 <10分钟 for 1TB)。
"""

import asyncio
from enum import Enum
from typing import Any

import boto3
from botocore.exceptions import ClientError


class FsxTaskLifecycle(Enum):
    """FSx Data Repository Task 生命周期状态。"""

    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class FsxClientError(Exception):
    """FSx 客户端错误基类。"""

    pass


class FsxClient:
    """FSx for Lustre 客户端。

    封装 boto3 FSx 客户端，提供异步数据仓库任务操作。
    所有操作使用 run_in_executor 实现异步。
    """

    def __init__(
        self,
        filesystem_id: str,
        region: str = "us-west-2",
        mount_path: str = "/fsx",
        s3_bucket: str | None = None,
    ) -> None:
        """初始化 FSx 客户端。

        Args:
            filesystem_id: FSx 文件系统 ID
            region: AWS 区域
            mount_path: FSx 挂载路径 (HyperPod 节点上的路径)
            s3_bucket: 关联的 S3 桶名 (用于路径映射)
        """
        self._filesystem_id = filesystem_id
        self._region = region
        self._mount_path = mount_path
        self._s3_bucket = s3_bucket
        self._fsx_client = boto3.client("fsx", region_name=region)

    async def create_import_task(
        self,
        paths: list[str],
        report_enabled: bool = False,
        report_path: str | None = None,
    ) -> dict[str, Any]:
        """创建数据导入任务 (S3 → FSx)。

        使用 IMPORT_METADATA_FROM_REPOSITORY 类型，仅导入元数据。
        实际数据在首次访问时按需加载 (Lazy Loading)。

        Args:
            paths: 要导入的路径列表 (相对于 Data Repository Association)
            report_enabled: 是否启用完成报告
            report_path: 报告存储的 S3 路径

        Returns:
            任务信息字典

        Raises:
            FsxClientError: 创建任务失败
        """
        # 构建导入任务参数
        params = self._build_task_params(
            "IMPORT_METADATA_FROM_REPOSITORY",
            paths,
            report_enabled,
            report_path
        )

        return await self._create_repository_task(params, "import")

    async def create_release_task(
        self,
        paths: list[str],
    ) -> dict[str, Any]:
        """创建数据释放任务 (释放 FSx 缓存)。

        使用 RELEASE_DATA_FROM_FILESYSTEM 类型，释放文件占用的存储空间。
        数据仍保留在 S3 中，可在需要时重新加载。

        Args:
            paths: 要释放的路径列表

        Returns:
            任务信息字典

        Raises:
            FsxClientError: 创建任务失败
        """
        # 构建释放任务参数
        params = self._build_task_params(
            "RELEASE_DATA_FROM_FILESYSTEM",
            paths
        )

        return await self._create_repository_task(params, "release")

    async def get_task_status(
        self,
        task_id: str,
    ) -> dict[str, Any] | None:
        """获取任务状态。

        Args:
            task_id: 任务 ID

        Returns:
            任务信息字典，不存在返回 None

        Raises:
            FsxClientError: 查询失败
        """
        loop = asyncio.get_event_loop()

        def _get_status() -> dict[str, Any] | None:
            try:
                response = self._fsx_client.describe_data_repository_tasks(
                    TaskIds=[task_id],
                )
                tasks = response.get("DataRepositoryTasks", [])
                return tasks[0] if tasks else None
            except ClientError as e:
                raise FsxClientError(
                    f"Failed to get task status: {e}"
                ) from e

        return await loop.run_in_executor(None, _get_status)

    async def describe_filesystem(self) -> dict[str, Any]:
        """获取文件系统信息。

        Returns:
            文件系统信息字典

        Raises:
            FsxClientError: 查询失败或文件系统不存在
        """
        loop = asyncio.get_event_loop()

        def _describe() -> dict[str, Any]:
            try:
                response = self._fsx_client.describe_file_systems(
                    FileSystemIds=[self._filesystem_id],
                )
                filesystems = response.get("FileSystems", [])
                if not filesystems:
                    raise FsxClientError(
                        f"Filesystem {self._filesystem_id} not found"
                    )
                return filesystems[0]
            except ClientError as e:
                raise FsxClientError(
                    f"Failed to describe filesystem: {e}"
                ) from e

        return await loop.run_in_executor(None, _describe)

    def get_fsx_path_for_dataset(self, dataset_id: int) -> str:
        """获取数据集的 FSx 路径。

        Args:
            dataset_id: 数据集 ID

        Returns:
            FSx 路径 (如 /fsx/datasets/10)
        """
        return f"{self._mount_path}/datasets/{dataset_id}"

    def get_s3_path_for_dataset(self, dataset_id: int) -> str:
        """获取数据集的 S3 路径。

        Args:
            dataset_id: 数据集 ID

        Returns:
            S3 URI (如 s3://bucket/datasets/10)
        """
        return f"s3://{self._s3_bucket}/datasets/{dataset_id}"

    async def wait_for_task_completion(
        self,
        task_id: str,
        poll_interval: int = 30,
        max_wait_time: int = 3600,
    ) -> dict[str, Any]:
        """等待任务完成。

        Args:
            task_id: 任务 ID
            poll_interval: 轮询间隔 (秒)
            max_wait_time: 最大等待时间 (秒)

        Returns:
            任务最终状态

        Raises:
            FsxClientError: 任务失败或超时
        """
        import time

        start_time = time.time()
        # 定义终止状态（成功、失败、取消）
        terminal_states = {
            FsxTaskLifecycle.SUCCEEDED.value,
            FsxTaskLifecycle.FAILED.value,
            FsxTaskLifecycle.CANCELED.value,
        }

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise FsxClientError(
                    f"Task {task_id} timed out after {max_wait_time}s"
                )

            status = await self.get_task_status(task_id)
            if status is None:
                raise FsxClientError(f"Task {task_id} not found")

            lifecycle = status.get("Lifecycle")
            if lifecycle in terminal_states:
                if lifecycle == FsxTaskLifecycle.FAILED.value:
                    failure_details = status.get("FailureDetails", {})
                    raise FsxClientError(
                        f"Task {task_id} failed: {failure_details.get('Message', 'Unknown error')}"
                    )
                return status

            await asyncio.sleep(poll_interval)

    # ========== 私有辅助方法 ==========

    def _build_task_params(
        self,
        task_type: str,
        paths: list[str],
        report_enabled: bool = False,
        report_path: str | None = None,
    ) -> dict[str, Any]:
        """构建任务参数。

        Args:
            task_type: 任务类型
            paths: 路径列表
            report_enabled: 是否启用报告
            report_path: 报告路径

        Returns:
            任务参数字典
        """
        params: dict[str, Any] = {
            "FileSystemId": self._filesystem_id,
            "Type": task_type,
            "Paths": paths,
        }

        if report_enabled and report_path:
            params["Report"] = {
                "Enabled": True,
                "Path": report_path,
                "Format": "REPORT_CSV_20191124",
                "Scope": "FAILED_FILES_ONLY",
            }

        return params

    async def _create_repository_task(
        self,
        params: dict[str, Any],
        task_name: str,
    ) -> dict[str, Any]:
        """创建数据仓库任务。

        Args:
            params: 任务参数
            task_name: 任务名称（用于错误消息）

        Returns:
            任务信息字典

        Raises:
            FsxClientError: 创建失败
        """
        loop = asyncio.get_event_loop()

        def _create() -> dict[str, Any]:
            try:
                response = self._fsx_client.create_data_repository_task(**params)
                return response.get("DataRepositoryTask", {})
            except ClientError as e:
                raise FsxClientError(
                    f"Failed to create {task_name} task: {e}"
                ) from e

        return await loop.run_in_executor(None, _create)
