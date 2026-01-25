"""测试 FSx for Lustre 客户端。

使用 aioboto3 原生异步模式进行测试。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class AsyncContextManagerMock:
    """异步上下文管理器 Mock，用于模拟 aioboto3 客户端。"""

    def __init__(self, mock_client: MagicMock) -> None:
        self.mock_client = mock_client

    async def __aenter__(self) -> MagicMock:
        return self.mock_client

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


def create_mock_session(mock_fsx_client: MagicMock) -> MagicMock:
    """创建 mock aioboto3.Session，返回异步上下文管理器客户端。"""
    mock_session = MagicMock()
    mock_session.client.return_value = AsyncContextManagerMock(mock_fsx_client)
    return mock_session


class TestFsxClientInit:
    """测试 FsxClient 初始化。"""

    def test_init_with_filesystem_id(self) -> None:
        """验证使用 filesystem_id 初始化。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        with patch("aioboto3.Session") as mock_session_class:
            mock_session_class.return_value = MagicMock()

            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
            )

            assert client._filesystem_id == "fs-123456789"
            assert client._region == "us-west-2"
            mock_session_class.assert_called_once()

    def test_init_with_mount_path(self) -> None:
        """验证设置挂载路径。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        with patch("aioboto3.Session"):
            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
                mount_path="/fsx",
            )

            assert client._mount_path == "/fsx"


class TestFsxClientCreateImportTask:
    """测试 create_import_task 方法 (S3→FSx 同步)。"""

    @pytest.mark.asyncio
    async def test_create_import_task_success(self) -> None:
        """验证成功创建导入任务。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        mock_fsx = MagicMock()
        mock_fsx.create_data_repository_task = AsyncMock(
            return_value={
                "DataRepositoryTask": {
                    "TaskId": "task-123",
                    "Lifecycle": "PENDING",
                    "Type": "IMPORT_METADATA_FROM_REPOSITORY",
                    "Paths": ["datasets/10/"],
                    "FileSystemId": "fs-123456789",
                }
            }
        )

        with patch("aioboto3.Session") as mock_session_class:
            mock_session_class.return_value = create_mock_session(mock_fsx)

            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
            )

            result = await client.create_import_task(
                paths=["datasets/10/"],
                report_enabled=False,
            )

            assert result["TaskId"] == "task-123"
            assert result["Lifecycle"] == "PENDING"
            mock_fsx.create_data_repository_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_import_task_with_report(self) -> None:
        """验证创建带报告的导入任务。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        mock_fsx = MagicMock()
        mock_fsx.create_data_repository_task = AsyncMock(
            return_value={
                "DataRepositoryTask": {
                    "TaskId": "task-456",
                    "Lifecycle": "PENDING",
                }
            }
        )

        with patch("aioboto3.Session") as mock_session_class:
            mock_session_class.return_value = create_mock_session(mock_fsx)

            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
            )

            await client.create_import_task(
                paths=["datasets/10/"],
                report_enabled=True,
                report_path="s3://bucket/reports/",
            )

            call_args = mock_fsx.create_data_repository_task.call_args
            assert "Report" in call_args.kwargs


class TestFsxClientCreateReleaseTask:
    """测试 create_release_task 方法 (释放 FSx 缓存)。"""

    @pytest.mark.asyncio
    async def test_create_release_task_success(self) -> None:
        """验证成功创建释放任务。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        mock_fsx = MagicMock()
        mock_fsx.create_data_repository_task = AsyncMock(
            return_value={
                "DataRepositoryTask": {
                    "TaskId": "task-789",
                    "Lifecycle": "PENDING",
                    "Type": "RELEASE_DATA_FROM_FILESYSTEM",
                }
            }
        )

        with patch("aioboto3.Session") as mock_session_class:
            mock_session_class.return_value = create_mock_session(mock_fsx)

            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
            )

            result = await client.create_release_task(
                paths=["datasets/10/"],
            )

            assert result["TaskId"] == "task-789"


class TestFsxClientGetTaskStatus:
    """测试 get_task_status 方法。"""

    @pytest.mark.asyncio
    async def test_get_task_status_success(self) -> None:
        """验证获取任务状态。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        mock_fsx = MagicMock()
        mock_fsx.describe_data_repository_tasks = AsyncMock(
            return_value={
                "DataRepositoryTasks": [
                    {
                        "TaskId": "task-123",
                        "Lifecycle": "SUCCEEDED",
                        "Type": "IMPORT_METADATA_FROM_REPOSITORY",
                        "Status": {
                            "TotalCount": 100,
                            "SucceededCount": 100,
                            "FailedCount": 0,
                        },
                    }
                ]
            }
        )

        with patch("aioboto3.Session") as mock_session_class:
            mock_session_class.return_value = create_mock_session(mock_fsx)

            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
            )

            result = await client.get_task_status(task_id="task-123")

            assert result["Lifecycle"] == "SUCCEEDED"
            assert result["Status"]["TotalCount"] == 100

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self) -> None:
        """验证任务不存在时返回 None。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        mock_fsx = MagicMock()
        mock_fsx.describe_data_repository_tasks = AsyncMock(return_value={"DataRepositoryTasks": []})

        with patch("aioboto3.Session") as mock_session_class:
            mock_session_class.return_value = create_mock_session(mock_fsx)

            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
            )

            result = await client.get_task_status(task_id="nonexistent")

            assert result is None


class TestFsxClientPathMapping:
    """测试路径映射方法。"""

    def test_get_fsx_path_for_dataset(self) -> None:
        """验证获取数据集的 FSx 路径。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        with patch("aioboto3.Session"):
            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
                mount_path="/fsx",
            )

            fsx_path = client.get_fsx_path_for_dataset(dataset_id=10)

            assert fsx_path == "/fsx/datasets/10"

    def test_get_s3_path_for_dataset(self) -> None:
        """验证获取数据集的 S3 路径。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        with patch("aioboto3.Session"):
            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
                s3_bucket="my-bucket",
            )

            s3_path = client.get_s3_path_for_dataset(dataset_id=10)

            assert s3_path == "s3://my-bucket/datasets/10"


class TestFsxClientDescribeFilesystem:
    """测试 describe_filesystem 方法。"""

    @pytest.mark.asyncio
    async def test_describe_filesystem_success(self) -> None:
        """验证获取文件系统信息。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        mock_fsx = MagicMock()
        mock_fsx.describe_file_systems = AsyncMock(
            return_value={
                "FileSystems": [
                    {
                        "FileSystemId": "fs-123456789",
                        "Lifecycle": "AVAILABLE",
                        "StorageCapacity": 1200,
                        "StorageType": "SSD",
                        "LustreConfiguration": {
                            "DeploymentType": "PERSISTENT_2",
                            "PerUnitStorageThroughput": 250,
                        },
                    }
                ]
            }
        )

        with patch("aioboto3.Session") as mock_session_class:
            mock_session_class.return_value = create_mock_session(mock_fsx)

            client = FsxClient(
                filesystem_id="fs-123456789",
                region="us-west-2",
            )

            result = await client.describe_filesystem()

            assert result["FileSystemId"] == "fs-123456789"
            assert result["Lifecycle"] == "AVAILABLE"
            assert result["StorageCapacity"] == 1200


class TestFsxTaskLifecycle:
    """测试 FSx 任务生命周期常量。"""

    def test_task_lifecycle_values(self) -> None:
        """验证任务生命周期枚举值。"""
        from src.modules.datasets.infrastructure.fsx import FsxTaskLifecycle

        assert FsxTaskLifecycle.PENDING.value == "PENDING"
        assert FsxTaskLifecycle.EXECUTING.value == "EXECUTING"
        assert FsxTaskLifecycle.SUCCEEDED.value == "SUCCEEDED"
        assert FsxTaskLifecycle.FAILED.value == "FAILED"
        assert FsxTaskLifecycle.CANCELED.value == "CANCELED"
