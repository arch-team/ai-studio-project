"""Model Service Unit Tests - TDD Red-Green-Refactor.

Tests for T031a (register model), T031b (list models), T031c (model versions).
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.modules.models.domain.entities.model import (
    Model,
    ModelFramework,
    ModelStatus,
)
from src.shared.domain.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
)

# === Fixtures ===


@pytest.fixture
def mock_model_repository() -> AsyncMock:
    """Mock model repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_name_and_version = AsyncMock(return_value=None)
    repo.get_latest_version = AsyncMock(return_value=None)
    repo.list_models = AsyncMock(return_value=([], 0))
    repo.list_versions = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_training_job_repository() -> AsyncMock:
    """Mock training job repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_checkpoint_repository() -> AsyncMock:
    """Mock checkpoint repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def sample_model() -> Model:
    """Sample model entity."""
    return Model(
        id=1,
        model_name="bert-base-classifier",
        owner_id=100,
        version="v1",
        display_name="BERT Base Classifier",
        description="Fine-tuned BERT model for text classification",
        training_job_id=1,
        checkpoint_id=1,
        model_uri="s3://ai-training-platform/models/bert-base-classifier/v1",
        framework=ModelFramework.PYTORCH,
        framework_version="2.1.0",
        status=ModelStatus.REGISTERED,
        metrics={"accuracy": 0.92, "f1_score": 0.89, "loss": 0.15},
        hyperparameters={"learning_rate": 0.0001, "batch_size": 32, "epochs": 10},
        tags=["nlp", "classification", "bert"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def training_model(sample_model: Model) -> Model:
    """Model in training status."""
    sample_model.status = ModelStatus.TRAINING
    sample_model.registered_at = None
    return sample_model


@pytest.fixture
def deployed_model(sample_model: Model) -> Model:
    """Deployed model."""
    sample_model.status = ModelStatus.DEPLOYED
    return sample_model


@pytest.fixture
def archived_model(sample_model: Model) -> Model:
    """Archived model."""
    sample_model.status = ModelStatus.ARCHIVED
    sample_model.archived_at = datetime.utcnow()
    return sample_model


@pytest.fixture
def model_v2(sample_model: Model) -> Model:
    """Version 2 of sample model."""
    model = Model(
        id=2,
        model_name="bert-base-classifier",
        owner_id=100,
        version="v2",
        display_name="BERT Base Classifier v2",
        training_job_id=2,
        checkpoint_id=2,
        model_uri="s3://ai-training-platform/models/bert-base-classifier/v2",
        framework=ModelFramework.PYTORCH,
        framework_version="2.1.0",
        status=ModelStatus.REGISTERED,
        metrics={"accuracy": 0.95, "f1_score": 0.92, "loss": 0.12},
        hyperparameters={"learning_rate": 0.00005, "batch_size": 64, "epochs": 15},
        tags=["nlp", "classification", "bert", "improved"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return model


@pytest.fixture
def create_model_data() -> dict[str, Any]:
    """Data for creating a model."""
    return {
        "training_job_id": 1,
        "checkpoint_id": 1,
        "model_name": "new-model",
        "display_name": "New Model",
        "description": "A new trained model",
        "framework": "pytorch",
        "framework_version": "2.1.0",
        "metrics": {"accuracy": 0.90},
        "hyperparameters": {"learning_rate": 0.001},
        "tags": ["test"],
    }


# === Service Factory ===


def get_service(
    mock_model_repository: AsyncMock,
    mock_training_job_repository: AsyncMock | None = None,
    mock_checkpoint_repository: AsyncMock | None = None,
):
    """Create ModelService with mocked dependencies."""
    from src.modules.models.application.services.model_service import ModelService

    return ModelService(
        model_repository=mock_model_repository,
        training_job_repository=mock_training_job_repository,
        checkpoint_repository=mock_checkpoint_repository,
    )


# === Test Classes ===


class TestCreateModel:
    """Tests for create_model method (T031a)."""

    @pytest.mark.asyncio
    async def test_create_model_success(
        self,
        mock_model_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_checkpoint_repository: AsyncMock,
        create_model_data: dict[str, Any],
        sample_model: Model,
    ):
        """Test successful model creation."""
        # Arrange
        mock_training_job_repository.get_by_id.return_value = AsyncMock(id=1)
        mock_checkpoint_repository.get_by_id.return_value = AsyncMock(id=1)
        mock_model_repository.get_latest_version.return_value = None
        mock_model_repository.create.return_value = sample_model
        service = get_service(
            mock_model_repository,
            mock_training_job_repository,
            mock_checkpoint_repository,
        )

        # Act
        result = await service.create_model(owner_id=100, data=create_model_data)

        # Assert
        assert result is not None
        assert result.model_name == sample_model.model_name
        mock_training_job_repository.get_by_id.assert_called_once_with(1)
        mock_checkpoint_repository.get_by_id.assert_called_once_with(1)
        mock_model_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_model_increments_version(
        self,
        mock_model_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_checkpoint_repository: AsyncMock,
        create_model_data: dict[str, Any],
        sample_model: Model,
        model_v2: Model,
    ):
        """Test model creation auto-increments version when model name exists."""
        # Arrange
        mock_training_job_repository.get_by_id.return_value = AsyncMock(id=1)
        mock_checkpoint_repository.get_by_id.return_value = AsyncMock(id=1)
        create_model_data["model_name"] = "bert-base-classifier"
        mock_model_repository.get_latest_version.return_value = sample_model  # v1 exists
        mock_model_repository.create.return_value = model_v2
        service = get_service(
            mock_model_repository,
            mock_training_job_repository,
            mock_checkpoint_repository,
        )

        # Act
        result = await service.create_model(owner_id=100, data=create_model_data)

        # Assert
        assert result.version == "v2"
        mock_model_repository.get_latest_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_model_training_job_not_found(
        self,
        mock_model_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_checkpoint_repository: AsyncMock,
        create_model_data: dict[str, Any],
    ):
        """Test create fails when training job does not exist."""
        # Arrange
        mock_training_job_repository.get_by_id.return_value = None
        service = get_service(
            mock_model_repository,
            mock_training_job_repository,
            mock_checkpoint_repository,
        )

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await service.create_model(owner_id=100, data=create_model_data)

        assert "training job" in str(exc_info.value).lower()
        mock_model_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_model_checkpoint_not_found(
        self,
        mock_model_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_checkpoint_repository: AsyncMock,
        create_model_data: dict[str, Any],
    ):
        """Test create fails when checkpoint does not exist."""
        # Arrange
        mock_training_job_repository.get_by_id.return_value = AsyncMock(id=1)
        mock_checkpoint_repository.get_by_id.return_value = None
        service = get_service(
            mock_model_repository,
            mock_training_job_repository,
            mock_checkpoint_repository,
        )

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await service.create_model(owner_id=100, data=create_model_data)

        assert "checkpoint" in str(exc_info.value).lower()
        mock_model_repository.create.assert_not_called()


class TestGetModel:
    """Tests for get_model method."""

    @pytest.mark.asyncio
    async def test_get_model_success(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test get model by ID."""
        # Arrange
        mock_model_repository.get_by_id.return_value = sample_model
        service = get_service(mock_model_repository)

        # Act
        result = await service.get_model(model_id=1)

        # Assert
        assert result is not None
        assert result.id == sample_model.id
        assert result.model_name == sample_model.model_name
        mock_model_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_model_not_found(
        self,
        mock_model_repository: AsyncMock,
    ):
        """Test get model raises error when not found."""
        # Arrange
        mock_model_repository.get_by_id.return_value = None
        service = get_service(mock_model_repository)

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await service.get_model(model_id=999)

        assert "not found" in str(exc_info.value).lower()


class TestListModels:
    """Tests for list_models method (T031b)."""

    @pytest.mark.asyncio
    async def test_list_models_with_pagination(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test list models with pagination."""
        # Arrange
        mock_model_repository.list_models.return_value = ([sample_model], 1)
        service = get_service(mock_model_repository)

        # Act
        models, total = await service.list_models(page=1, page_size=20)

        # Assert
        assert len(models) == 1
        assert total == 1
        mock_model_repository.list_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_models_filter_by_training_job(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test list models filtered by training job ID."""
        # Arrange
        mock_model_repository.list_models.return_value = ([sample_model], 1)
        service = get_service(mock_model_repository)

        # Act
        models, total = await service.list_models(training_job_id=1)

        # Assert
        mock_model_repository.list_models.assert_called_once()
        call_kwargs = mock_model_repository.list_models.call_args.kwargs
        assert call_kwargs.get("training_job_id") == 1

    @pytest.mark.asyncio
    async def test_list_models_filter_by_status(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test list models filtered by status."""
        # Arrange
        mock_model_repository.list_models.return_value = ([sample_model], 1)
        service = get_service(mock_model_repository)

        # Act
        models, total = await service.list_models(status="registered")

        # Assert
        call_kwargs = mock_model_repository.list_models.call_args.kwargs
        assert call_kwargs.get("status") == "registered"

    @pytest.mark.asyncio
    async def test_list_models_filter_by_framework(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test list models filtered by framework."""
        # Arrange
        mock_model_repository.list_models.return_value = ([sample_model], 1)
        service = get_service(mock_model_repository)

        # Act
        models, total = await service.list_models(framework="pytorch")

        # Assert
        call_kwargs = mock_model_repository.list_models.call_args.kwargs
        assert call_kwargs.get("framework") == "pytorch"

    @pytest.mark.asyncio
    async def test_list_models_sort_by_created_at(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test list models sorted by created_at."""
        # Arrange
        mock_model_repository.list_models.return_value = ([sample_model], 1)
        service = get_service(mock_model_repository)

        # Act
        models, total = await service.list_models(sort_by="created_at", sort_order="desc")

        # Assert
        call_kwargs = mock_model_repository.list_models.call_args.kwargs
        assert call_kwargs.get("sort_by") == "created_at"
        assert call_kwargs.get("sort_order") == "desc"

    @pytest.mark.asyncio
    async def test_list_models_sort_by_version(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test list models sorted by version."""
        # Arrange
        mock_model_repository.list_models.return_value = ([sample_model], 1)
        service = get_service(mock_model_repository)

        # Act
        models, total = await service.list_models(sort_by="version", sort_order="asc")

        # Assert
        call_kwargs = mock_model_repository.list_models.call_args.kwargs
        assert call_kwargs.get("sort_by") == "version"


class TestGetModelVersions:
    """Tests for get_model_versions method (T031c)."""

    @pytest.mark.asyncio
    async def test_get_versions_success(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
        model_v2: Model,
    ):
        """Test get model versions returns list."""
        # Arrange
        mock_model_repository.get_by_id.return_value = sample_model
        mock_model_repository.list_versions.return_value = [sample_model, model_v2]
        service = get_service(mock_model_repository)

        # Act
        result = await service.get_model_versions(model_id=1)

        # Assert
        assert "versions" in result
        assert len(result["versions"]) == 2
        mock_model_repository.list_versions.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_versions_model_not_found(
        self,
        mock_model_repository: AsyncMock,
    ):
        """Test get versions raises error when model not found."""
        # Arrange
        mock_model_repository.get_by_id.return_value = None
        service = get_service(mock_model_repository)

        # Act & Assert
        with pytest.raises(EntityNotFoundError):
            await service.get_model_versions(model_id=999)

    @pytest.mark.asyncio
    async def test_get_versions_with_comparison(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
        model_v2: Model,
    ):
        """Test get versions with comparison between versions."""
        # Arrange
        # get_model_versions calls: get_by_id(1), get_by_id(2), then compare_versions calls: get_by_id(1), get_by_id(2)
        mock_model_repository.get_by_id.side_effect = [sample_model, model_v2, sample_model, model_v2]
        mock_model_repository.list_versions.return_value = [sample_model, model_v2]
        service = get_service(mock_model_repository)

        # Act
        result = await service.get_model_versions(model_id=1, compare_with=2)

        # Assert
        assert "versions" in result
        assert "comparison" in result
        assert "metrics_diff" in result["comparison"]
        assert "hyperparams_changed" in result["comparison"]


class TestCompareModelVersions:
    """Tests for compare_versions method."""

    @pytest.mark.asyncio
    async def test_compare_versions_metrics_diff(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
        model_v2: Model,
    ):
        """Test metrics diff between versions."""
        # Arrange
        mock_model_repository.get_by_id.side_effect = [sample_model, model_v2]
        service = get_service(mock_model_repository)

        # Act
        result = await service.compare_versions(model_id_1=1, model_id_2=2)

        # Assert
        assert "metrics_diff" in result
        # v2 has better accuracy (0.95 vs 0.92)
        assert result["metrics_diff"]["accuracy"]["v1"] == 0.92
        assert result["metrics_diff"]["accuracy"]["v2"] == 0.95

    @pytest.mark.asyncio
    async def test_compare_versions_hyperparams_changed(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
        model_v2: Model,
    ):
        """Test hyperparameter changes between versions."""
        # Arrange
        mock_model_repository.get_by_id.side_effect = [sample_model, model_v2]
        service = get_service(mock_model_repository)

        # Act
        result = await service.compare_versions(model_id_1=1, model_id_2=2)

        # Assert
        assert "hyperparams_changed" in result
        # batch_size changed from 32 to 64
        assert "batch_size" in result["hyperparams_changed"]

    @pytest.mark.asyncio
    async def test_compare_versions_model_not_found(
        self,
        mock_model_repository: AsyncMock,
    ):
        """Test compare fails when model not found."""
        # Arrange
        mock_model_repository.get_by_id.return_value = None
        service = get_service(mock_model_repository)

        # Act & Assert
        with pytest.raises(EntityNotFoundError):
            await service.compare_versions(model_id_1=999, model_id_2=1)


class TestRegisterModel:
    """Tests for register_model method."""

    @pytest.mark.asyncio
    async def test_register_training_model_success(
        self,
        mock_model_repository: AsyncMock,
        training_model: Model,
    ):
        """Test registering a training model."""
        # Arrange
        mock_model_repository.get_by_id.return_value = training_model
        registered_model = Model(**vars(training_model))
        registered_model.status = ModelStatus.REGISTERED
        registered_model.registered_at = datetime.utcnow()
        mock_model_repository.update.return_value = registered_model
        service = get_service(mock_model_repository)

        # Act
        result = await service.register_model(model_id=1)

        # Assert
        assert result.status == ModelStatus.REGISTERED
        assert result.registered_at is not None
        mock_model_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_already_registered_fails(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,  # Already REGISTERED status
    ):
        """Test register fails when model is already registered."""
        # Arrange
        mock_model_repository.get_by_id.return_value = sample_model
        service = get_service(mock_model_repository)

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.register_model(model_id=1)


class TestArchiveModel:
    """Tests for archive_model method."""

    @pytest.mark.asyncio
    async def test_archive_registered_model_success(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,  # REGISTERED status
    ):
        """Test archiving a registered model."""
        # Arrange
        mock_model_repository.get_by_id.return_value = sample_model
        archived_result = Model(**vars(sample_model))
        archived_result.status = ModelStatus.ARCHIVED
        archived_result.archived_at = datetime.utcnow()
        mock_model_repository.update.return_value = archived_result
        service = get_service(mock_model_repository)

        # Act
        result = await service.archive_model(model_id=1)

        # Assert
        assert result.status == ModelStatus.ARCHIVED
        assert result.archived_at is not None
        mock_model_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_deployed_model_success(
        self,
        mock_model_repository: AsyncMock,
        deployed_model: Model,
    ):
        """Test archiving a deployed model."""
        # Arrange
        mock_model_repository.get_by_id.return_value = deployed_model
        archived_result = Model(**vars(deployed_model))
        archived_result.status = ModelStatus.ARCHIVED
        mock_model_repository.update.return_value = archived_result
        service = get_service(mock_model_repository)

        # Act
        result = await service.archive_model(model_id=1)

        # Assert
        assert result.status == ModelStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_archive_training_model_fails(
        self,
        mock_model_repository: AsyncMock,
        training_model: Model,
    ):
        """Test archive fails when model is in training status."""
        # Arrange
        mock_model_repository.get_by_id.return_value = training_model
        service = get_service(mock_model_repository)

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.archive_model(model_id=1)


class TestDeleteModel:
    """Tests for delete_model method."""

    @pytest.mark.asyncio
    async def test_delete_model_success(
        self,
        mock_model_repository: AsyncMock,
        sample_model: Model,
    ):
        """Test soft delete model."""
        # Arrange
        mock_model_repository.get_by_id.return_value = sample_model
        mock_model_repository.soft_delete.return_value = True
        service = get_service(mock_model_repository)

        # Act
        await service.delete_model(model_id=1)

        # Assert
        mock_model_repository.soft_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_model_not_found(
        self,
        mock_model_repository: AsyncMock,
    ):
        """Test delete non-existent model raises error."""
        # Arrange
        mock_model_repository.get_by_id.return_value = None
        service = get_service(mock_model_repository)

        # Act & Assert
        with pytest.raises(EntityNotFoundError):
            await service.delete_model(model_id=999)
