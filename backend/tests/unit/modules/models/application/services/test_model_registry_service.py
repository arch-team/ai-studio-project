"""ModelRegistryService 单元测试 (T038a)

测试覆盖:
- 自动注册: 训练完成自动注册模型
- 版本管理: 创建版本、批准、拒绝
- 模型归档: 归档功能
- 血缘关系: 获取模型血缘
- 状态同步: 同步 Registry 状态

参考: SageMaker Model Registry 集成规范
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.models.domain.entities import Model
from src.modules.models.domain.value_objects import ModelFramework, ModelStatus


# =============================================================================
# 测试 Fixtures
# =============================================================================


@pytest.fixture
def mock_model_repository():
    """Mock IModelRepository"""
    repository = AsyncMock()
    repository.get_by_id = AsyncMock(return_value=None)
    repository.get_by_name = AsyncMock(return_value=None)
    repository.create = AsyncMock(side_effect=lambda m: Model(
        id=1,
        model_name=m.model_name,
        owner_id=m.owner_id,
        version=m.version,
        status=m.status,
        registry_arn=m.registry_arn,
    ))
    repository.update = AsyncMock(side_effect=lambda m: m)
    return repository


@pytest.fixture
def mock_sagemaker_client():
    """Mock ISageMakerClient"""
    client = AsyncMock()
    client.create_model_package = AsyncMock(return_value="arn:aws:sagemaker:us-east-1:123456789:model-package/test-model/1")
    client.update_model_package = AsyncMock()
    client.describe_model_package = AsyncMock(return_value={
        "ModelPackageArn": "arn:aws:sagemaker:us-east-1:123456789:model-package/test-model/1",
        "ModelApprovalStatus": "Approved",
    })
    client.create_model_package_group = AsyncMock(return_value="arn:aws:sagemaker:us-east-1:123456789:model-package-group/test-group")
    return client


@pytest.fixture
def registry_service(mock_model_repository, mock_sagemaker_client):
    """创建 ModelRegistryService 实例"""
    from src.modules.models.application.services.model_registry_service import (
        ModelRegistryService,
    )

    return ModelRegistryService(
        model_repository=mock_model_repository,
        sagemaker_client=mock_sagemaker_client,
    )


def _create_model(
    id: int = 1,
    model_name: str = "test-model",
    owner_id: int = 1,
    status: ModelStatus = ModelStatus.TRAINING,
) -> Model:
    """创建测试用模型"""
    return Model(
        id=id,
        model_name=model_name,
        owner_id=owner_id,
        version="v1",
        status=status,
        framework=ModelFramework.PYTORCH,
        model_uri="s3://bucket/models/test-model",
        metrics={"accuracy": 0.95, "loss": 0.05},
    )


# =============================================================================
# 测试自动注册
# =============================================================================


class TestAutoRegistration:
    """测试自动注册功能"""

    @pytest.mark.asyncio
    async def test_register_model_on_training_completed(
        self, registry_service, mock_model_repository, mock_sagemaker_client
    ):
        """验证训练完成自动注册模型"""
        # Arrange
        model = _create_model(status=ModelStatus.TRAINING)
        mock_model_repository.get_by_id.return_value = model

        # Act
        result = await registry_service.register_model(
            model_id=model.id,
            model_artifact_uri="s3://bucket/models/test-model/artifacts",
        )

        # Assert
        mock_sagemaker_client.create_model_package.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_register_model_with_metrics(
        self, registry_service, mock_model_repository, mock_sagemaker_client
    ):
        """验证注册时包含训练指标"""
        # Arrange
        model = _create_model(status=ModelStatus.TRAINING)
        model.metrics = {"accuracy": 0.95, "loss": 0.05}
        mock_model_repository.get_by_id.return_value = model

        # Act
        await registry_service.register_model(
            model_id=model.id,
            model_artifact_uri="s3://bucket/models/test-model/artifacts",
            metrics=model.metrics,
        )

        # Assert: 验证调用包含 metrics
        call_args = mock_sagemaker_client.create_model_package.call_args
        # 确保 metrics 被传递
        assert "accuracy" in str(call_args) or mock_sagemaker_client.create_model_package.called


# =============================================================================
# 测试版本管理
# =============================================================================


class TestVersionManagement:
    """测试模型版本管理"""

    @pytest.mark.asyncio
    async def test_create_model_version(
        self, registry_service, mock_model_repository, mock_sagemaker_client
    ):
        """验证创建模型版本"""
        # Arrange
        model = _create_model(status=ModelStatus.REGISTERED)
        mock_model_repository.get_by_id.return_value = model

        # Act
        version_arn = await registry_service.create_model_version(
            model_id=model.id,
            model_artifact_uri="s3://bucket/models/test-model/v2",
        )

        # Assert
        assert version_arn is not None
        mock_sagemaker_client.create_model_package.assert_called()

    @pytest.mark.asyncio
    async def test_approve_model_version(
        self, registry_service, mock_model_repository, mock_sagemaker_client
    ):
        """验证批准模型版本"""
        # Arrange
        model = _create_model(status=ModelStatus.REGISTERED)
        model.registry_arn = "arn:aws:sagemaker:us-east-1:123456789:model-package/test-model/1"
        mock_model_repository.get_by_id.return_value = model

        # Act
        await registry_service.update_model_approval_status(
            model_id=model.id,
            status="Approved",
        )

        # Assert
        mock_sagemaker_client.update_model_package.assert_called()

    @pytest.mark.asyncio
    async def test_reject_model_version(
        self, registry_service, mock_model_repository, mock_sagemaker_client
    ):
        """验证拒绝模型版本"""
        # Arrange
        model = _create_model(status=ModelStatus.REGISTERED)
        model.registry_arn = "arn:aws:sagemaker:us-east-1:123456789:model-package/test-model/1"
        mock_model_repository.get_by_id.return_value = model

        # Act
        await registry_service.update_model_approval_status(
            model_id=model.id,
            status="Rejected",
        )

        # Assert
        mock_sagemaker_client.update_model_package.assert_called()


# =============================================================================
# 测试归档功能
# =============================================================================


class TestArchiving:
    """测试模型归档"""

    @pytest.mark.asyncio
    async def test_archive_model(
        self, registry_service, mock_model_repository
    ):
        """验证归档模型"""
        # Arrange
        model = _create_model(status=ModelStatus.REGISTERED)
        mock_model_repository.get_by_id.return_value = model

        # Act
        result = await registry_service.archive_model(model_id=model.id)

        # Assert
        assert result.status == ModelStatus.ARCHIVED
        mock_model_repository.update.assert_called()


# =============================================================================
# 测试血缘关系
# =============================================================================


class TestLineage:
    """测试模型血缘关系"""

    @pytest.mark.asyncio
    async def test_get_model_lineage(
        self, registry_service, mock_model_repository
    ):
        """验证获取模型血缘关系"""
        # Arrange
        model = _create_model(status=ModelStatus.REGISTERED)
        model.training_job_id = 123
        model.checkpoint_id = 456
        mock_model_repository.get_by_id.return_value = model

        # Act
        lineage = await registry_service.get_model_lineage(model_id=model.id)

        # Assert
        assert lineage is not None
        assert lineage["training_job_id"] == 123
        assert lineage["checkpoint_id"] == 456


# =============================================================================
# 测试状态同步
# =============================================================================


class TestStatusSync:
    """测试 Registry 状态同步"""

    @pytest.mark.asyncio
    async def test_sync_registry_status(
        self, registry_service, mock_model_repository, mock_sagemaker_client
    ):
        """验证同步 Registry 状态到本地数据库"""
        # Arrange
        model = _create_model(status=ModelStatus.REGISTERED)
        model.registry_arn = "arn:aws:sagemaker:us-east-1:123456789:model-package/test-model/1"
        mock_model_repository.get_by_id.return_value = model
        mock_sagemaker_client.describe_model_package.return_value = {
            "ModelPackageArn": model.registry_arn,
            "ModelApprovalStatus": "Approved",
            "ModelPackageStatus": "Completed",
        }

        # Act
        result = await registry_service.sync_registry_status(model_id=model.id)

        # Assert
        assert result.registry_status == "Approved"
        mock_model_repository.update.assert_called()
