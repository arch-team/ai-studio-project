"""测试 FsxSyncService - FSx 同步服务。"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestFsxSyncServiceInit:
    """测试 FsxSyncService 初始化。"""

    def test_init_with_dependencies(self) -> None:
        """验证使用依赖项初始化。"""
        from src.modules.datasets.application.services import FsxSyncService

        mock_dataset_repo = MagicMock()
        mock_fsx_client = MagicMock()

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        assert service._dataset_repository == mock_dataset_repo
        assert service._fsx_client == mock_fsx_client


class TestFsxSyncServiceInitiateSync:
    """测试 initiate_s3_to_fsx_sync 方法。"""

    @pytest.mark.asyncio
    async def test_initiate_sync_success(self) -> None:
        """验证成功发起 S3→FSx 同步。"""
        from src.modules.datasets.application.services import FsxSyncService
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = AsyncMock()

        # Mock dataset
        mock_dataset = Dataset(
            id=10,
            name="test-dataset",
            version="v1",
            description=None,
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/datasets/10/",
            dataset_type=DatasetType.CUSTOM,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.AVAILABLE,
            owner_id=100,
        )
        mock_dataset_repo.get_by_id.return_value = mock_dataset

        # Mock FSx create_import_task
        mock_fsx_client.create_import_task.return_value = {
            "TaskId": "task-123",
            "Lifecycle": "PENDING",
            "Type": "IMPORT_METADATA_FROM_REPOSITORY",
        }

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        result = await service.initiate_s3_to_fsx_sync(dataset_id=10)

        assert result["task_id"] == "task-123"
        assert result["status"] == "PENDING"
        mock_fsx_client.create_import_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_sync_dataset_not_found(self) -> None:
        """验证数据集不存在时抛出错误。"""
        from src.modules.datasets.application.services import FsxSyncService
        from src.modules.datasets.domain.exceptions import DatasetNotFoundError

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = AsyncMock()

        mock_dataset_repo.get_by_id.return_value = None

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        with pytest.raises(DatasetNotFoundError):
            await service.initiate_s3_to_fsx_sync(dataset_id=999)


class TestFsxSyncServiceGetSyncStatus:
    """测试 get_sync_status 方法。"""

    @pytest.mark.asyncio
    async def test_get_sync_status_success(self) -> None:
        """验证获取同步状态。"""
        from src.modules.datasets.application.services import FsxSyncService

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = AsyncMock()

        mock_fsx_client.get_task_status.return_value = {
            "TaskId": "task-123",
            "Lifecycle": "SUCCEEDED",
            "Status": {
                "TotalCount": 100,
                "SucceededCount": 100,
                "FailedCount": 0,
            },
        }

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        result = await service.get_sync_status(task_id="task-123")

        assert result["task_id"] == "task-123"
        assert result["status"] == "SUCCEEDED"
        assert result["progress"]["total"] == 100
        assert result["progress"]["succeeded"] == 100

    @pytest.mark.asyncio
    async def test_get_sync_status_not_found(self) -> None:
        """验证任务不存在时抛出错误。"""
        from src.modules.datasets.application.services import FsxSyncService
        from src.modules.datasets.domain.exceptions import FsxSyncTaskNotFoundError

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = AsyncMock()

        mock_fsx_client.get_task_status.return_value = None

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        with pytest.raises(FsxSyncTaskNotFoundError):
            await service.get_sync_status(task_id="nonexistent")


class TestFsxSyncServicePrefetchDataset:
    """测试 prefetch_dataset 方法 (数据预热)。"""

    @pytest.mark.asyncio
    async def test_prefetch_dataset_success(self) -> None:
        """验证成功预热数据集。"""
        from src.modules.datasets.application.services import FsxSyncService
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = AsyncMock()

        mock_dataset = Dataset(
            id=10,
            name="test-dataset",
            version="v1",
            description=None,
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/datasets/10/",
            dataset_type=DatasetType.CUSTOM,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.AVAILABLE,
            owner_id=100,
        )
        mock_dataset_repo.get_by_id.return_value = mock_dataset

        mock_fsx_client.create_import_task.return_value = {
            "TaskId": "task-456",
            "Lifecycle": "PENDING",
        }

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        result = await service.prefetch_dataset(
            dataset_id=10,
            paths=["train/", "val/"],
        )

        assert result["task_id"] == "task-456"
        # 验证调用时传入了完整路径 (datasets/{id}/{path})
        call_args = mock_fsx_client.create_import_task.call_args
        assert "datasets/10/train/" in call_args.kwargs["paths"]
        assert "datasets/10/val/" in call_args.kwargs["paths"]


class TestFsxSyncServiceReleaseDataset:
    """测试 release_dataset 方法 (释放缓存)。"""

    @pytest.mark.asyncio
    async def test_release_dataset_success(self) -> None:
        """验证成功释放数据集缓存。"""
        from src.modules.datasets.application.services import FsxSyncService
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = AsyncMock()

        mock_dataset = Dataset(
            id=10,
            name="test-dataset",
            version="v1",
            description=None,
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/datasets/10/",
            dataset_type=DatasetType.CUSTOM,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.AVAILABLE,
            owner_id=100,
        )
        mock_dataset_repo.get_by_id.return_value = mock_dataset

        mock_fsx_client.create_release_task.return_value = {
            "TaskId": "task-789",
            "Lifecycle": "PENDING",
        }

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        result = await service.release_dataset(dataset_id=10)

        assert result["task_id"] == "task-789"
        mock_fsx_client.create_release_task.assert_called_once()


class TestFsxSyncServiceGetDatasetPath:
    """测试 get_dataset_fsx_path 方法。"""

    @pytest.mark.asyncio
    async def test_get_dataset_fsx_path_success(self) -> None:
        """验证获取数据集 FSx 路径。"""
        from src.modules.datasets.application.services import FsxSyncService
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = MagicMock()

        mock_dataset = Dataset(
            id=10,
            name="test-dataset",
            version="v1",
            description=None,
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/datasets/10/",
            dataset_type=DatasetType.CUSTOM,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.AVAILABLE,
            owner_id=100,
        )
        mock_dataset_repo.get_by_id.return_value = mock_dataset
        mock_fsx_client.get_fsx_path_for_dataset.return_value = "/fsx/datasets/10"

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        result = await service.get_dataset_fsx_path(dataset_id=10)

        assert result["dataset_id"] == 10
        assert result["fsx_path"] == "/fsx/datasets/10"


class TestFsxSyncServiceCheckAvailability:
    """测试 check_fsx_availability 方法。"""

    @pytest.mark.asyncio
    async def test_check_fsx_availability_success(self) -> None:
        """验证检查 FSx 可用性。"""
        from src.modules.datasets.application.services import FsxSyncService

        mock_dataset_repo = AsyncMock()
        mock_fsx_client = AsyncMock()

        mock_fsx_client.describe_filesystem.return_value = {
            "FileSystemId": "fs-123456789",
            "Lifecycle": "AVAILABLE",
            "StorageCapacity": 1200,
        }

        service = FsxSyncService(
            dataset_repository=mock_dataset_repo,
            fsx_client=mock_fsx_client,
        )

        result = await service.check_fsx_availability()

        assert result["available"] is True
        assert result["filesystem_id"] == "fs-123456789"
        assert result["storage_capacity_gb"] == 1200
