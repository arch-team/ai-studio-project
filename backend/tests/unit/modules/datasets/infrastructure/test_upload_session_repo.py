"""测试 UploadSession 仓库接口和实现。"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.datasets.infrastructure.models import (
    UploadSessionModel,
    UploadSessionStatus,
)


class TestIUploadSessionRepository:
    """测试 IUploadSessionRepository 接口定义。"""

    def test_interface_has_required_methods(self) -> None:
        """验证接口定义了所有必要方法。"""
        from src.modules.datasets.domain.repositories import IUploadSessionRepository

        required_methods = [
            "get_by_id",
            "get_by_upload_id",
            "get_active_by_dataset",
            "list_by_owner",
            "add",
            "update",
            "delete",
            "exists",
        ]

        for method in required_methods:
            assert hasattr(IUploadSessionRepository, method), f"缺少方法: {method}"

    def test_interface_is_abstract(self) -> None:
        """验证接口是抽象类。"""
        from abc import ABC

        from src.modules.datasets.domain.repositories import IUploadSessionRepository

        assert issubclass(IUploadSessionRepository, ABC)


class TestUploadSessionRepositoryImplInit:
    """测试 UploadSessionRepositoryImpl 初始化。"""

    def test_init_with_session(self) -> None:
        """验证使用 session 初始化。"""
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = MagicMock()
        repo = UploadSessionRepositoryImpl(mock_session)

        assert repo._session == mock_session


class TestUploadSessionRepositoryImplToEntity:
    """测试 _to_entity 转换方法。"""

    def test_to_entity_converts_model_correctly(self) -> None:
        """验证 ORM 模型正确转换为领域对象。"""
        from src.modules.datasets.domain.value_objects import UploadSession
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = MagicMock()
        repo = UploadSessionRepositoryImpl(mock_session)

        # 创建 mock 模型
        now = datetime.now()
        model = MagicMock(spec=UploadSessionModel)
        model.id = 1
        model.upload_id = "upload-123"
        model.dataset_id = 10
        model.bucket = "test-bucket"
        model.s3_key = "datasets/10/data.tar"
        model.filename = "data.tar"
        model.content_type = "application/x-tar"
        model.total_size = 500_000_000
        model.part_size = 100_000_000
        model.status = UploadSessionStatus.INITIATED
        model.owner_id = 100
        model.completed_parts = None
        model.uploaded_bytes = 0
        model.completed_part_count = 0
        model.created_at = now
        model.updated_at = now
        model.expires_at = now + timedelta(days=7)

        entity = repo._to_entity(model)

        assert isinstance(entity, UploadSession)
        assert entity.upload_id == "upload-123"
        assert entity.dataset_id == 10
        assert entity.bucket == "test-bucket"
        assert entity.key == "datasets/10/data.tar"
        assert entity.total_size == 500_000_000

    def test_to_entity_with_completed_parts(self) -> None:
        """验证带已完成分片的模型转换。"""
        from src.modules.datasets.domain.value_objects import UploadPart, UploadSession
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = MagicMock()
        repo = UploadSessionRepositoryImpl(mock_session)

        now = datetime.now()
        model = MagicMock(spec=UploadSessionModel)
        model.id = 1
        model.upload_id = "upload-123"
        model.dataset_id = 10
        model.bucket = "test-bucket"
        model.s3_key = "datasets/10/data.tar"
        model.filename = "data.tar"
        model.content_type = "application/x-tar"
        model.total_size = 200_000_000
        model.part_size = 100_000_000
        model.status = UploadSessionStatus.IN_PROGRESS
        model.owner_id = 100
        # JSON 格式的已完成分片
        model.completed_parts = [
            {
                "part_number": 1,
                "etag": '"etag1"',
                "size_bytes": 100_000_000,
                "md5_checksum": "md51",
                "uploaded_at": now.isoformat(),
            }
        ]
        model.uploaded_bytes = 100_000_000
        model.completed_part_count = 1
        model.created_at = now
        model.updated_at = now
        model.expires_at = now + timedelta(days=7)

        entity = repo._to_entity(model)

        assert len(entity.completed_parts) == 1
        assert 1 in entity.completed_parts
        part = entity.completed_parts[1]
        assert isinstance(part, UploadPart)
        assert part.part_number == 1
        assert part.etag == '"etag1"'


class TestUploadSessionRepositoryImplToModel:
    """测试 _to_model 转换方法。"""

    def test_to_model_converts_entity_correctly(self) -> None:
        """验证领域对象正确转换为 ORM 模型。"""
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = MagicMock()
        repo = UploadSessionRepositoryImpl(mock_session)

        entity = UploadSession(
            upload_id="upload-123",
            dataset_id=10,
            bucket="test-bucket",
            key="datasets/10/data.tar",
            filename="data.tar",
            content_type="application/x-tar",
            total_size=500_000_000,
            part_size=100_000_000,
            status=UploadStatus.INITIATED,
            owner_id=100,
        )

        model = repo._to_model(entity)

        assert isinstance(model, UploadSessionModel)
        assert model.upload_id == "upload-123"
        assert model.dataset_id == 10
        assert model.bucket == "test-bucket"
        assert model.s3_key == "datasets/10/data.tar"
        assert model.total_size == 500_000_000


class TestUploadSessionRepositoryImplGetByUploadId:
    """测试 get_by_upload_id 方法。"""

    @pytest.mark.asyncio
    async def test_get_by_upload_id_found(self) -> None:
        """验证根据 upload_id 获取会话成功。"""
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_model = MagicMock(spec=UploadSessionModel)
        mock_model.id = 1
        mock_model.upload_id = "upload-123"
        mock_model.dataset_id = 10
        mock_model.bucket = "bucket"
        mock_model.s3_key = "key"
        mock_model.filename = "file.tar"
        mock_model.content_type = "application/octet-stream"
        mock_model.total_size = 100
        mock_model.part_size = 50
        mock_model.status = UploadSessionStatus.INITIATED
        mock_model.owner_id = 1
        mock_model.completed_parts = None
        mock_model.uploaded_bytes = 0
        mock_model.completed_part_count = 0
        mock_model.created_at = datetime.now()
        mock_model.updated_at = datetime.now()
        mock_model.expires_at = None

        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        repo = UploadSessionRepositoryImpl(mock_session)
        result = await repo.get_by_upload_id("upload-123")

        assert result is not None
        assert result.upload_id == "upload-123"

    @pytest.mark.asyncio
    async def test_get_by_upload_id_not_found(self) -> None:
        """验证根据 upload_id 获取会话失败返回 None。"""
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = UploadSessionRepositoryImpl(mock_session)
        result = await repo.get_by_upload_id("nonexistent")

        assert result is None


class TestUploadSessionRepositoryImplGetActiveByDataset:
    """测试 get_active_by_dataset 方法。"""

    @pytest.mark.asyncio
    async def test_get_active_by_dataset_found(self) -> None:
        """验证获取数据集的活跃上传会话。"""
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_model = MagicMock(spec=UploadSessionModel)
        mock_model.id = 1
        mock_model.upload_id = "upload-123"
        mock_model.dataset_id = 10
        mock_model.bucket = "bucket"
        mock_model.s3_key = "key"
        mock_model.filename = "file.tar"
        mock_model.content_type = "application/octet-stream"
        mock_model.total_size = 100
        mock_model.part_size = 50
        mock_model.status = UploadSessionStatus.IN_PROGRESS
        mock_model.owner_id = 1
        mock_model.completed_parts = None
        mock_model.uploaded_bytes = 0
        mock_model.completed_part_count = 0
        mock_model.created_at = datetime.now()
        mock_model.updated_at = datetime.now()
        mock_model.expires_at = None

        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        repo = UploadSessionRepositoryImpl(mock_session)
        result = await repo.get_active_by_dataset(10)

        assert result is not None
        assert result.dataset_id == 10

    @pytest.mark.asyncio
    async def test_get_active_by_dataset_not_found(self) -> None:
        """验证无活跃会话返回 None。"""
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = UploadSessionRepositoryImpl(mock_session)
        result = await repo.get_active_by_dataset(999)

        assert result is None


class TestUploadSessionRepositoryImplListByOwner:
    """测试 list_by_owner 方法。"""

    @pytest.mark.asyncio
    async def test_list_by_owner_returns_sessions(self) -> None:
        """验证列出用户的上传会话。"""
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = AsyncMock()

        # Mock for count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        # Mock for list query
        mock_list_result = MagicMock()
        mock_model1 = MagicMock(spec=UploadSessionModel)
        mock_model1.id = 1
        mock_model1.upload_id = "upload-1"
        mock_model1.dataset_id = 10
        mock_model1.bucket = "bucket"
        mock_model1.s3_key = "key1"
        mock_model1.filename = "file1.tar"
        mock_model1.content_type = "application/octet-stream"
        mock_model1.total_size = 100
        mock_model1.part_size = 50
        mock_model1.status = UploadSessionStatus.INITIATED
        mock_model1.owner_id = 1
        mock_model1.completed_parts = None
        mock_model1.uploaded_bytes = 0
        mock_model1.completed_part_count = 0
        mock_model1.created_at = datetime.now()
        mock_model1.updated_at = datetime.now()
        mock_model1.expires_at = None

        mock_model2 = MagicMock(spec=UploadSessionModel)
        mock_model2.id = 2
        mock_model2.upload_id = "upload-2"
        mock_model2.dataset_id = 20
        mock_model2.bucket = "bucket"
        mock_model2.s3_key = "key2"
        mock_model2.filename = "file2.tar"
        mock_model2.content_type = "application/octet-stream"
        mock_model2.total_size = 200
        mock_model2.part_size = 50
        mock_model2.status = UploadSessionStatus.IN_PROGRESS
        mock_model2.owner_id = 1
        mock_model2.completed_parts = None
        mock_model2.uploaded_bytes = 0
        mock_model2.completed_part_count = 0
        mock_model2.created_at = datetime.now()
        mock_model2.updated_at = datetime.now()
        mock_model2.expires_at = None

        mock_list_result.scalars.return_value.all.return_value = [
            mock_model1,
            mock_model2,
        ]

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        repo = UploadSessionRepositoryImpl(mock_session)
        sessions, total = await repo.list_by_owner(owner_id=1)

        assert total == 2
        assert len(sessions) == 2
        assert sessions[0].upload_id == "upload-1"
        assert sessions[1].upload_id == "upload-2"


class TestUploadSessionRepositoryImplAdd:
    """测试 add 方法。"""

    @pytest.mark.asyncio
    async def test_add_creates_session(self) -> None:
        """验证添加上传会话。"""
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )
        from src.modules.datasets.infrastructure.repositories import (
            UploadSessionRepositoryImpl,
        )

        mock_session = AsyncMock()

        entity = UploadSession(
            upload_id="upload-new",
            dataset_id=10,
            bucket="bucket",
            key="key",
            filename="file.tar",
            content_type="application/octet-stream",
            total_size=100,
            part_size=50,
            status=UploadStatus.INITIATED,
            owner_id=1,
        )

        repo = UploadSessionRepositoryImpl(mock_session)

        # Mock the model after refresh
        async def mock_refresh(model):
            model.id = 1
            model.created_at = datetime.now()
            model.updated_at = datetime.now()

        mock_session.refresh = mock_refresh

        result = await repo.add(entity)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
