"""FSx for Lustre 客户端。"""

import asyncio
from enum import Enum
from typing import Any

import aioboto3
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


class FsxClient:
    """FSx for Lustre 客户端。"""

    def __init__(
        self,
        filesystem_id: str,
        region: str = "us-east-1",
        mount_path: str = "/fsx",
        s3_bucket: str | None = None,
    ) -> None:
        """初始化 FSx 客户端。"""
        self._filesystem_id = filesystem_id
        self._region = region
        self._mount_path = mount_path
        self._s3_bucket = s3_bucket
        self._session = aioboto3.Session()

    async def create_import_task(
        self,
        paths: list[str],
        report_enabled: bool = False,
        report_path: str | None = None,
    ) -> dict[str, Any]:
        """创建数据导入任务 (S3 → FSx)。

        Raises:
            FsxClientError: 创建任务失败
        """
        params = self._build_task_params(
            "IMPORT_METADATA_FROM_REPOSITORY",
            paths,
            report_enabled,
            report_path,
        )

        try:
            async with self._session.client("fsx", region_name=self._region) as fsx:
                response = await fsx.create_data_repository_task(**params)
                return response.get("DataRepositoryTask", {})
        except ClientError as e:
            raise FsxClientError(f"Failed to create import task: {e}") from e

    async def create_release_task(
        self,
        paths: list[str],
        duration_since_last_access_minutes: int = 60,
    ) -> dict[str, Any]:
        """创建数据释放任务 (释放 FSx 缓存)。

        使用 RELEASE_DATA_FROM_FILESYSTEM 类型，释放文件占用的存储空间。
        数据仍保留在 S3 中，可在需要时重新加载。

        Args:
            paths: 要释放的路径列表
            duration_since_last_access_minutes: 释放最后访问时间超过该分钟数的文件 (默认 60)

        Raises:
            FsxClientError: 创建任务失败
        """
        params = self._build_task_params("RELEASE_DATA_FROM_FILESYSTEM", paths)
        # RELEASE_DATA_FROM_FILESYSTEM 需要 ReleaseConfiguration
        params["ReleaseConfiguration"] = {
            "DurationSinceLastAccess": {"Unit": "MINUTES", "Value": duration_since_last_access_minutes}
        }

        try:
            async with self._session.client("fsx", region_name=self._region) as fsx:
                response = await fsx.create_data_repository_task(**params)
                return response.get("DataRepositoryTask", {})
        except ClientError as e:
            raise FsxClientError(f"Failed to create release task: {e}") from e

    async def get_task_status(
        self,
        task_id: str,
    ) -> dict[str, Any] | None:
        """获取任务状态。

        Raises:
            FsxClientError: 查询失败
        """
        try:
            async with self._session.client("fsx", region_name=self._region) as fsx:
                response = await fsx.describe_data_repository_tasks(TaskIds=[task_id])
                tasks = response.get("DataRepositoryTasks", [])
                return tasks[0] if tasks else None
        except ClientError as e:
            raise FsxClientError(f"Failed to get task status: {e}") from e

    async def describe_filesystem(self) -> dict[str, Any]:
        """获取文件系统信息。

        Raises:
            FsxClientError: 查询失败或文件系统不存在
        """
        try:
            async with self._session.client("fsx", region_name=self._region) as fsx:
                response = await fsx.describe_file_systems(FileSystemIds=[self._filesystem_id])
                filesystems = response.get("FileSystems", [])
                if not filesystems:
                    raise FsxClientError(f"Filesystem {self._filesystem_id} not found")
                return filesystems[0]
        except ClientError as e:
            raise FsxClientError(f"Failed to describe filesystem: {e}") from e

    def get_fsx_path_for_dataset(self, dataset_id: int) -> str:
        """获取数据集的 FSx 路径。"""
        return f"{self._mount_path}/datasets/{dataset_id}"

    def get_s3_path_for_dataset(self, dataset_id: int) -> str:
        """获取数据集的 S3 路径。"""
        return f"s3://{self._s3_bucket}/datasets/{dataset_id}"

    async def wait_for_task_completion(
        self,
        task_id: str,
        poll_interval: int = 30,
        max_wait_time: int = 3600,
    ) -> dict[str, Any]:
        """等待任务完成。

        Raises:
            FsxClientError: 任务失败或超时
        """
        import time

        start_time = time.time()
        terminal_states = {
            FsxTaskLifecycle.SUCCEEDED.value,
            FsxTaskLifecycle.FAILED.value,
            FsxTaskLifecycle.CANCELED.value,
        }

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise FsxClientError(f"Task {task_id} timed out after {max_wait_time}s")

            status = await self.get_task_status(task_id)
            if status is None:
                raise FsxClientError(f"Task {task_id} not found")

            lifecycle = status.get("Lifecycle")
            if lifecycle in terminal_states:
                if lifecycle == FsxTaskLifecycle.FAILED.value:
                    failure_details = status.get("FailureDetails", {})
                    raise FsxClientError(f"Task {task_id} failed: {failure_details.get('Message', 'Unknown error')}")
                return status

            await asyncio.sleep(poll_interval)

    def _build_task_params(
        self,
        task_type: str,
        paths: list[str],
        report_enabled: bool = False,
        report_path: str | None = None,
    ) -> dict[str, Any]:
        """构建任务参数。"""
        params: dict[str, Any] = {
            "FileSystemId": self._filesystem_id,
            "Type": task_type,
            "Paths": paths,
            # Report 参数是 AWS FSx API 必填项
            "Report": {"Enabled": False},
        }

        if report_enabled and report_path:
            params["Report"] = {
                "Enabled": True,
                "Path": report_path,
                "Format": "REPORT_CSV_20191124",
                "Scope": "FAILED_FILES_ONLY",
            }

        return params
