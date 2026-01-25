"""测试 DatasetUploadService - 数据集上传服务。"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestDatasetUploadServiceInit:
    """测试 DatasetUploadService 初始化。"""

    def test_init_with_dependencies(self) -> None:
        """验证使用依赖项初始化。"""
        from src.modules.datasets.application.services import DatasetUploadService

        mock_upload_repo = MagicMock()
        mock_dataset_repo = MagicMock()
        mock_s3_client = MagicMock()

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        assert service._upload_session_repository == mock_upload_repo
        assert service._dataset_repository == mock_dataset_repo
        assert service._s3_client == mock_s3_client


class TestDatasetUploadServiceInitiateUpload:
    """测试 initiate_multipart_upload 方法。"""

    @pytest.mark.asyncio
    async def test_initiate_multipart_upload_success(self) -> None:
        """验证成功初始化分片上传。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        # Mock dataset exists
        mock_dataset = Dataset(
            id=10,
            name="test-dataset",
            version="v1",
            description="Test dataset",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/datasets/10/",
            dataset_type=DatasetType.CUSTOM,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.PREPARING,
            owner_id=100,
        )
        mock_dataset_repo.get_by_id.return_value = mock_dataset

        # Mock no active upload session
        mock_upload_repo.get_active_by_dataset.return_value = None

        # Mock S3 create multipart upload
        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "upload-123",
            "Bucket": "test-bucket",
            "Key": "datasets/10/data.tar",
        }

        # Mock add returns the session
        async def mock_add(session):
            return session

        mock_upload_repo.add.side_effect = mock_add

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        result = await service.initiate_multipart_upload(
            dataset_id=10,
            filename="data.tar",
            content_type="application/x-tar",
            total_size=500_000_000,
            owner_id=100,
        )

        assert result.upload_id == "upload-123"
        assert result.dataset_id == 10
        mock_s3_client.create_multipart_upload.assert_called_once()
        mock_upload_repo.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_upload_dataset_not_found(self) -> None:
        """验证数据集不存在时抛出错误。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.exceptions import DatasetNotFoundError

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        mock_dataset_repo.get_by_id.return_value = None

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        with pytest.raises(DatasetNotFoundError):
            await service.initiate_multipart_upload(
                dataset_id=999,
                filename="data.tar",
                content_type="application/x-tar",
                total_size=100,
                owner_id=100,
            )

    @pytest.mark.asyncio
    async def test_initiate_upload_active_session_exists(self) -> None:
        """验证已有活跃上传会话时抛出错误。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.exceptions import UploadSessionActiveError
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
            UploadSession,
            UploadStatus,
        )

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        mock_dataset = Dataset(
            id=10,
            name="test-dataset",
            version="v1",
            description=None,
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/datasets/10/",
            dataset_type=DatasetType.CUSTOM,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.PREPARING,
            owner_id=100,
        )
        mock_dataset_repo.get_by_id.return_value = mock_dataset

        # Mock active session exists
        mock_active_session = UploadSession(
            upload_id="existing-upload",
            dataset_id=10,
            bucket="bucket",
            key="datasets/10/other.tar",
            filename="other.tar",
            content_type="application/x-tar",
            total_size=100,
            part_size=50,
            status=UploadStatus.IN_PROGRESS,
            owner_id=100,
        )
        mock_upload_repo.get_active_by_dataset.return_value = mock_active_session

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        with pytest.raises(UploadSessionActiveError):
            await service.initiate_multipart_upload(
                dataset_id=10,
                filename="data.tar",
                content_type="application/x-tar",
                total_size=100,
                owner_id=100,
            )


class TestDatasetUploadServicePresignedUrls:
    """测试 generate_presigned_urls 方法。"""

    @pytest.mark.asyncio
    async def test_generate_presigned_urls_success(self) -> None:
        """验证成功生成预签名 URL。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        # Mock upload session
        mock_session = UploadSession(
            upload_id="upload-123",
            dataset_id=10,
            bucket="test-bucket",
            key="datasets/10/data.tar",
            filename="data.tar",
            content_type="application/x-tar",
            total_size=500_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=100,
        )
        mock_upload_repo.get_by_upload_id.return_value = mock_session

        # Mock presigned URLs
        mock_s3_client.generate_presigned_urls_batch.return_value = [
            {"part_number": 1, "presigned_url": "https://url1"},
            {"part_number": 2, "presigned_url": "https://url2"},
        ]

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        urls = await service.generate_presigned_urls(
            upload_id="upload-123",
            part_numbers=[1, 2],
            expiration=3600,
        )

        assert len(urls) == 2
        mock_s3_client.generate_presigned_urls_batch.assert_called_once()


class TestDatasetUploadServiceRegisterPart:
    """测试 register_part_completion 方法。"""

    @pytest.mark.asyncio
    async def test_register_part_completion_success(self) -> None:
        """验证成功注册分片完成。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        # Mock upload session
        mock_session = UploadSession(
            upload_id="upload-123",
            dataset_id=10,
            bucket="test-bucket",
            key="datasets/10/data.tar",
            filename="data.tar",
            content_type="application/x-tar",
            total_size=200_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=100,
        )
        mock_upload_repo.get_by_upload_id.return_value = mock_session

        # Mock update
        async def mock_update(session):
            return session

        mock_upload_repo.update.side_effect = mock_update

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        await service.register_part_completion(
            upload_id="upload-123",
            part_number=1,
            etag='"etag1"',
            size_bytes=100_000_000,
            md5_checksum="abc123",
        )

        mock_upload_repo.update.assert_called_once()


class TestDatasetUploadServiceGetProgress:
    """测试 get_upload_progress 方法。"""

    @pytest.mark.asyncio
    async def test_get_upload_progress_returns_status(self) -> None:
        """验证返回上传进度状态。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.value_objects import (
            UploadPart,
            UploadSession,
            UploadStatus,
        )

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        # Mock upload session with completed parts
        now = datetime.now()
        mock_session = UploadSession(
            upload_id="upload-123",
            dataset_id=10,
            bucket="test-bucket",
            key="datasets/10/data.tar",
            filename="data.tar",
            content_type="application/x-tar",
            total_size=500_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=100,
            completed_parts={
                1: UploadPart(1, '"e1"', 100_000_000, "m1", now),
                2: UploadPart(2, '"e2"', 100_000_000, "m2", now),
            },
        )
        mock_upload_repo.get_by_upload_id.return_value = mock_session

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        progress = await service.get_upload_progress(upload_id="upload-123")

        assert progress["upload_id"] == "upload-123"
        assert progress["status"] == "IN_PROGRESS"
        assert progress["progress_percentage"] == 40.0
        assert progress["missing_parts"] == [3, 4, 5]


class TestDatasetUploadServiceCompleteUpload:
    """测试 complete_multipart_upload 方法。"""

    @pytest.mark.asyncio
    async def test_complete_multipart_upload_success(self) -> None:
        """验证成功完成分片上传。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
            UploadPart,
            UploadSession,
            UploadStatus,
        )

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        # Mock upload session with all parts completed
        now = datetime.now()
        mock_session = UploadSession(
            upload_id="upload-123",
            dataset_id=10,
            bucket="test-bucket",
            key="datasets/10/data.tar",
            filename="data.tar",
            content_type="application/x-tar",
            total_size=200_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=100,
            completed_parts={
                1: UploadPart(1, '"etag1"', 100_000_000, "m1", now),
                2: UploadPart(2, '"etag2"', 100_000_000, "m2", now),
            },
        )
        mock_upload_repo.get_by_upload_id.return_value = mock_session

        # Mock S3 complete
        mock_s3_client.complete_multipart_upload.return_value = {
            "ETag": '"abc123-2"',
            "Location": "https://bucket.s3.amazonaws.com/datasets/10/data.tar",
        }

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
            status=DatasetStatus.PREPARING,
            owner_id=100,
        )
        mock_dataset_repo.get_by_id.return_value = mock_dataset

        # Mock updates
        async def mock_upload_update(session):
            return session

        async def mock_dataset_update(dataset):
            return dataset

        mock_upload_repo.update.side_effect = mock_upload_update
        mock_dataset_repo.update.side_effect = mock_dataset_update

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        result = await service.complete_multipart_upload(upload_id="upload-123")

        assert result["etag"] == '"abc123-2"'
        mock_s3_client.complete_multipart_upload.assert_called_once()


class TestDatasetUploadServiceAbortUpload:
    """测试 abort_multipart_upload 方法。"""

    @pytest.mark.asyncio
    async def test_abort_multipart_upload_success(self) -> None:
        """验证成功取消分片上传。"""
        from src.modules.datasets.application.services import DatasetUploadService
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )

        mock_upload_repo = AsyncMock()
        mock_dataset_repo = AsyncMock()
        mock_s3_client = AsyncMock()

        # Mock upload session
        mock_session = UploadSession(
            upload_id="upload-123",
            dataset_id=10,
            bucket="test-bucket",
            key="datasets/10/data.tar",
            filename="data.tar",
            content_type="application/x-tar",
            total_size=200_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=100,
        )
        mock_upload_repo.get_by_upload_id.return_value = mock_session

        # Mock updates
        async def mock_update(session):
            return session

        mock_upload_repo.update.side_effect = mock_update

        service = DatasetUploadService(
            upload_session_repository=mock_upload_repo,
            dataset_repository=mock_dataset_repo,
            s3_client=mock_s3_client,
        )

        await service.abort_multipart_upload(upload_id="upload-123")

        mock_s3_client.abort_multipart_upload.assert_called_once()
        mock_upload_repo.update.assert_called_once()
