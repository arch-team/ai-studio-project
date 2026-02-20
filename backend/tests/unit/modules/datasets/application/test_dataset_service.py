"""Dataset Service unit tests."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.datasets.application.services import DatasetService
from src.modules.datasets.domain.entities import Dataset
from src.modules.datasets.domain.exceptions import DatasetNotFoundError
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)
from src.shared.domain.exceptions import DuplicateEntityError


class TestDatasetService:
    """Test DatasetService."""

    @pytest.fixture
    def mock_repository(self) -> IDatasetRepository:
        """Create mock repository."""
        repo = MagicMock(spec=IDatasetRepository)
        repo.get_by_id = AsyncMock()
        repo.get_by_name_and_version = AsyncMock()
        repo.list_by_owner = AsyncMock()
        repo.list_public = AsyncMock()
        repo.add = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        repo.exists = AsyncMock()
        repo.exists_by_name_and_version = AsyncMock()
        return repo

    @pytest.fixture
    def service(self, mock_repository: IDatasetRepository) -> DatasetService:
        """Create service with mock repository."""
        return DatasetService(repository=mock_repository)

    @pytest.fixture
    def sample_dataset(self) -> Dataset:
        """Create sample dataset."""
        return Dataset(
            id=1,
            name="test-dataset",
            version="v1",
            description="Test dataset",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/path",
            dataset_type=DatasetType.IMAGE,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.PREPARING,
            owner_id=100,
            created_at=datetime(2025, 1, 1, 0, 0, 0),
        )


class TestCreateDataset(TestDatasetService):
    """Test create_dataset method."""

    async def test_create_dataset_success(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
    ) -> None:
        """Should create dataset successfully."""
        mock_repository.exists_by_name_and_version.return_value = False
        created_dataset = Dataset(
            id=1,
            name="new-dataset",
            version="v1",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/path",
            dataset_type=DatasetType.IMAGE,
            owner_id=100,
        )
        mock_repository.add.return_value = created_dataset

        result = await service.create_dataset(
            owner_id=100,
            data={
                "name": "new-dataset",
                "version": "v1",
                "storage_type": "S3",
                "storage_uri": "s3://bucket/path",
                "dataset_type": "IMAGE",
                "visibility": "PRIVATE",
            },
        )

        assert result.name == "new-dataset"
        assert result.owner_id == 100
        mock_repository.exists_by_name_and_version.assert_called_once_with("new-dataset", "v1")
        mock_repository.add.assert_called_once()

    async def test_create_dataset_duplicate_name_version(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
    ) -> None:
        """Should raise error for duplicate name+version."""
        mock_repository.exists_by_name_and_version.return_value = True

        with pytest.raises(DuplicateEntityError):
            await service.create_dataset(
                owner_id=100,
                data={
                    "name": "existing-dataset",
                    "version": "v1",
                    "storage_type": "S3",
                    "storage_uri": "s3://bucket/path",
                    "dataset_type": "IMAGE",
                },
            )

    async def test_create_dataset_with_default_version(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
    ) -> None:
        """Should use default version v1 if not provided."""
        mock_repository.exists_by_name_and_version.return_value = False
        mock_repository.add.return_value = Dataset(
            id=1,
            name="dataset-no-version",
            version="v1",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/path",
            dataset_type=DatasetType.IMAGE,
            owner_id=100,
        )

        result = await service.create_dataset(
            owner_id=100,
            data={
                "name": "dataset-no-version",
                "storage_type": "S3",
                "storage_uri": "s3://bucket/path",
                "dataset_type": "IMAGE",
            },
        )

        assert result.version == "v1"


class TestGetDataset(TestDatasetService):
    """Test get_dataset method."""

    async def test_get_dataset_success(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should return dataset by ID."""
        mock_repository.get_by_id.return_value = sample_dataset

        result = await service.get_dataset(1)

        assert result.id == 1
        assert result.name == "test-dataset"
        mock_repository.get_by_id.assert_called_once_with(1)

    async def test_get_dataset_not_found(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
    ) -> None:
        """Should raise error if dataset not found."""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(DatasetNotFoundError):
            await service.get_dataset(999)


class TestListDatasets(TestDatasetService):
    """Test list_datasets method."""

    async def test_list_datasets_by_owner(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should list datasets by owner."""
        mock_repository.list_by_owner.return_value = ([sample_dataset], 1)

        datasets, total = await service.list_datasets(owner_id=100)

        assert len(datasets) == 1
        assert total == 1
        mock_repository.list_by_owner.assert_called_once()

    async def test_list_datasets_with_filters(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should list datasets with filters."""
        mock_repository.list_by_owner.return_value = ([sample_dataset], 1)

        datasets, total = await service.list_datasets(
            owner_id=100,
            status=DatasetStatus.PREPARING,
            dataset_type=DatasetType.IMAGE,
            page=1,
            page_size=10,
        )

        assert len(datasets) == 1
        mock_repository.list_by_owner.assert_called_once_with(
            owner_id=100,
            status=DatasetStatus.PREPARING,
            dataset_type=DatasetType.IMAGE,
            storage_type=None,
            visibility=None,
            search=None,
            page=1,
            page_size=10,
            sort_by="created_at",
            sort_order="desc",
        )


class TestUpdateDataset(TestDatasetService):
    """Test update_dataset method."""

    async def test_update_dataset_description(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should update dataset description."""
        mock_repository.get_by_id.return_value = sample_dataset
        mock_repository.update.return_value = sample_dataset

        result = await service.update_dataset(
            dataset_id=1,
            data={"description": "Updated description"},
        )

        assert result.description == "Updated description"
        mock_repository.update.assert_called_once()

    async def test_update_dataset_tags(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should update dataset tags."""
        mock_repository.get_by_id.return_value = sample_dataset
        mock_repository.update.return_value = sample_dataset

        result = await service.update_dataset(
            dataset_id=1,
            data={"tags": ["new", "tags"]},
        )

        assert result.tags == ["new", "tags"]
        mock_repository.update.assert_called_once()

    async def test_update_dataset_visibility(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should update dataset visibility."""
        mock_repository.get_by_id.return_value = sample_dataset
        mock_repository.update.return_value = sample_dataset

        result = await service.update_dataset(
            dataset_id=1,
            data={"visibility": "PUBLIC"},
        )

        assert result.visibility == DatasetVisibility.PUBLIC
        mock_repository.update.assert_called_once()

    async def test_update_dataset_not_found(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
    ) -> None:
        """Should raise error if dataset not found."""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(DatasetNotFoundError):
            await service.update_dataset(dataset_id=999, data={"description": "test"})


class TestDeleteDataset(TestDatasetService):
    """Test delete_dataset method."""

    async def test_delete_dataset_success(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should delete (archive) dataset."""
        sample_dataset.status = DatasetStatus.AVAILABLE
        mock_repository.get_by_id.return_value = sample_dataset
        mock_repository.update.return_value = sample_dataset

        await service.delete_dataset(1)

        # Should transition to ARCHIVED status
        mock_repository.update.assert_called_once()

    async def test_delete_dataset_not_found(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
    ) -> None:
        """Should raise error if dataset not found."""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(DatasetNotFoundError):
            await service.delete_dataset(999)


class TestCreateVersion(TestDatasetService):
    """Test create_version method."""

    async def test_create_version_success(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should create new dataset version."""
        sample_dataset.status = DatasetStatus.AVAILABLE
        mock_repository.get_by_id.return_value = sample_dataset
        mock_repository.exists_by_name_and_version.return_value = False
        new_version = Dataset(
            id=2,
            name="test-dataset",
            version="v2",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/path/v2",
            dataset_type=DatasetType.IMAGE,
            owner_id=100,
        )
        mock_repository.add.return_value = new_version

        result = await service.create_version(
            dataset_id=1,
            version="v2",
            storage_uri="s3://bucket/path/v2",
        )

        assert result.version == "v2"
        assert result.name == "test-dataset"
        mock_repository.add.assert_called_once()

    async def test_create_version_duplicate(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
        sample_dataset: Dataset,
    ) -> None:
        """Should raise error for duplicate version."""
        sample_dataset.status = DatasetStatus.AVAILABLE
        mock_repository.get_by_id.return_value = sample_dataset
        mock_repository.exists_by_name_and_version.return_value = True

        with pytest.raises(DuplicateEntityError):
            await service.create_version(dataset_id=1, version="v1")

    async def test_create_version_dataset_not_found(
        self,
        service: DatasetService,
        mock_repository: IDatasetRepository,
    ) -> None:
        """Should raise error if source dataset not found."""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(DatasetNotFoundError):
            await service.create_version(dataset_id=999, version="v2")
