"""Dataset API schema tests."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.modules.datasets.api.schemas import (
    CreateDatasetRequest,
    DatasetDetail,
    DatasetListResponse,
    DatasetStatusEnum,
    DatasetStorageTypeEnum,
    DatasetSummary,
    DatasetTypeEnum,
    DatasetVisibilityEnum,
    UpdateDatasetRequest,
)
from src.modules.datasets.domain.entities import Dataset
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)


class TestDatasetEnums:
    """Test API enum definitions."""

    def test_storage_type_enum_values(self) -> None:
        """Storage type enum should have correct values (lowercase)."""
        assert DatasetStorageTypeEnum.FSX.value == "fsx"
        assert DatasetStorageTypeEnum.S3.value == "s3"
        assert DatasetStorageTypeEnum.EFS.value == "efs"

    def test_dataset_type_enum_values(self) -> None:
        """Dataset type enum should have correct values (lowercase)."""
        assert DatasetTypeEnum.IMAGE.value == "image"
        assert DatasetTypeEnum.TEXT.value == "text"
        assert DatasetTypeEnum.AUDIO.value == "audio"
        assert DatasetTypeEnum.VIDEO.value == "video"
        assert DatasetTypeEnum.TABULAR.value == "tabular"
        assert DatasetTypeEnum.CUSTOM.value == "custom"

    def test_visibility_enum_values(self) -> None:
        """Visibility enum should have correct values (lowercase)."""
        assert DatasetVisibilityEnum.PUBLIC.value == "public"
        assert DatasetVisibilityEnum.PRIVATE.value == "private"
        assert DatasetVisibilityEnum.RESTRICTED.value == "restricted"

    def test_status_enum_values(self) -> None:
        """Status enum should have correct values (lowercase)."""
        assert DatasetStatusEnum.AVAILABLE.value == "available"
        assert DatasetStatusEnum.PREPARING.value == "preparing"
        assert DatasetStatusEnum.ARCHIVED.value == "archived"
        assert DatasetStatusEnum.ERROR.value == "error"


class TestCreateDatasetRequest:
    """Test CreateDatasetRequest schema."""

    def test_create_request_with_required_fields(self) -> None:
        """Should create request with required fields."""
        request = CreateDatasetRequest(
            name="test-dataset",
            storage_type=DatasetStorageTypeEnum.S3,
            storage_uri="s3://my-bucket/datasets/test",
            dataset_type=DatasetTypeEnum.IMAGE,
        )
        assert request.name == "test-dataset"
        assert request.storage_type == DatasetStorageTypeEnum.S3
        assert request.storage_uri == "s3://my-bucket/datasets/test"
        assert request.dataset_type == DatasetTypeEnum.IMAGE
        # Default values
        assert request.version == "v1"
        assert request.visibility == DatasetVisibilityEnum.PRIVATE

    def test_create_request_with_all_fields(self) -> None:
        """Should create request with all fields."""
        request = CreateDatasetRequest(
            name="full-dataset",
            version="v2",
            description="Full dataset with all fields",
            storage_type=DatasetStorageTypeEnum.FSX,
            storage_uri="/fsx/datasets/full",
            dataset_type=DatasetTypeEnum.TEXT,
            data_format="jsonl",
            tags=["nlp", "training"],
            visibility=DatasetVisibilityEnum.PUBLIC,
        )
        assert request.name == "full-dataset"
        assert request.version == "v2"
        assert request.description == "Full dataset with all fields"
        assert request.data_format == "jsonl"
        assert request.tags == ["nlp", "training"]
        assert request.visibility == DatasetVisibilityEnum.PUBLIC

    def test_create_request_name_validation_min_length(self) -> None:
        """Should reject name shorter than 3 characters."""
        with pytest.raises(ValidationError) as exc_info:
            CreateDatasetRequest(
                name="ab",  # Too short
                storage_type=DatasetStorageTypeEnum.S3,
                storage_uri="s3://bucket/path",
                dataset_type=DatasetTypeEnum.IMAGE,
            )
        assert "name" in str(exc_info.value)

    def test_create_request_name_validation_max_length(self) -> None:
        """Should reject name longer than 128 characters."""
        with pytest.raises(ValidationError) as exc_info:
            CreateDatasetRequest(
                name="a" * 129,  # Too long
                storage_type=DatasetStorageTypeEnum.S3,
                storage_uri="s3://bucket/path",
                dataset_type=DatasetTypeEnum.IMAGE,
            )
        assert "name" in str(exc_info.value)

    def test_create_request_missing_required_fields(self) -> None:
        """Should fail with missing required fields."""
        with pytest.raises(ValidationError):
            CreateDatasetRequest(
                name="test-dataset",
                # Missing storage_type, storage_uri, dataset_type
            )


class TestUpdateDatasetRequest:
    """Test UpdateDatasetRequest schema."""

    def test_update_request_empty(self) -> None:
        """Should allow empty update request."""
        request = UpdateDatasetRequest()
        assert request.description is None
        assert request.tags is None
        assert request.visibility is None

    def test_update_request_with_description(self) -> None:
        """Should update description."""
        request = UpdateDatasetRequest(description="Updated description")
        assert request.description == "Updated description"

    def test_update_request_with_tags(self) -> None:
        """Should update tags."""
        request = UpdateDatasetRequest(tags=["new", "tags"])
        assert request.tags == ["new", "tags"]

    def test_update_request_with_visibility(self) -> None:
        """Should update visibility."""
        request = UpdateDatasetRequest(visibility=DatasetVisibilityEnum.PUBLIC)
        assert request.visibility == DatasetVisibilityEnum.PUBLIC


class TestDatasetSummary:
    """Test DatasetSummary response schema."""

    @pytest.fixture
    def sample_dataset(self) -> Dataset:
        """Create sample dataset entity."""
        return Dataset(
            id=1,
            name="test-dataset",
            version="v1",
            description="Test dataset",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/path",
            dataset_type=DatasetType.IMAGE,
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.AVAILABLE,
            owner_id=100,
            total_size_bytes=1024000,
            file_count=100,
            created_at=datetime(2025, 1, 1, 0, 0, 0),
        )

    def test_summary_from_entity(self, sample_dataset: Dataset) -> None:
        """Should create summary from entity."""
        summary = DatasetSummary.from_entity(sample_dataset)
        assert summary.id == 1
        assert summary.name == "test-dataset"
        assert summary.version == "v1"
        assert summary.description == "Test dataset"
        assert summary.storage_type == DatasetStorageTypeEnum.S3
        assert summary.dataset_type == DatasetTypeEnum.IMAGE
        assert summary.visibility == DatasetVisibilityEnum.PRIVATE
        assert summary.status == DatasetStatusEnum.AVAILABLE
        assert summary.total_size_bytes == 1024000
        assert summary.file_count == 100
        assert summary.created_at == datetime(2025, 1, 1, 0, 0, 0)

    def test_summary_enum_mapping(self, sample_dataset: Dataset) -> None:
        """Should correctly map domain enums to API enums."""
        # Test different enum values
        sample_dataset.storage_type = DatasetStorageType.FSX
        sample_dataset.dataset_type = DatasetType.TEXT
        sample_dataset.visibility = DatasetVisibility.PUBLIC
        sample_dataset.status = DatasetStatus.PREPARING

        summary = DatasetSummary.from_entity(sample_dataset)
        assert summary.storage_type == DatasetStorageTypeEnum.FSX
        assert summary.dataset_type == DatasetTypeEnum.TEXT
        assert summary.visibility == DatasetVisibilityEnum.PUBLIC
        assert summary.status == DatasetStatusEnum.PREPARING


class TestDatasetDetail:
    """Test DatasetDetail response schema."""

    @pytest.fixture
    def sample_dataset(self) -> Dataset:
        """Create sample dataset entity."""
        return Dataset(
            id=1,
            name="detailed-dataset",
            version="v1",
            description="Detailed dataset",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/datasets/detailed",
            dataset_type=DatasetType.IMAGE,
            data_format="imagenet",
            tags=["cv", "classification"],
            visibility=DatasetVisibility.PRIVATE,
            status=DatasetStatus.AVAILABLE,
            owner_id=100,
            total_size_bytes=2048000,
            file_count=200,
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 2, 0, 0, 0),
            last_accessed_at=datetime(2025, 1, 3, 0, 0, 0),
        )

    def test_detail_from_entity(self, sample_dataset: Dataset) -> None:
        """Should create detail from entity."""
        detail = DatasetDetail.from_entity(sample_dataset)
        # Summary fields (inherited)
        assert detail.id == 1
        assert detail.name == "detailed-dataset"
        assert detail.storage_type == DatasetStorageTypeEnum.S3
        assert detail.status == DatasetStatusEnum.AVAILABLE
        # Detail-specific fields
        assert detail.storage_uri == "s3://bucket/datasets/detailed"
        assert detail.data_format == "imagenet"
        assert detail.tags == ["cv", "classification"]
        assert detail.owner_id == 100
        assert detail.updated_at == datetime(2025, 1, 2, 0, 0, 0)
        assert detail.last_accessed_at == datetime(2025, 1, 3, 0, 0, 0)

    def test_detail_inherits_summary_fields(self, sample_dataset: Dataset) -> None:
        """Detail should inherit all summary fields."""
        detail = DatasetDetail.from_entity(sample_dataset)
        # All summary fields should be present
        assert hasattr(detail, "id")
        assert hasattr(detail, "name")
        assert hasattr(detail, "version")
        assert hasattr(detail, "description")
        assert hasattr(detail, "storage_type")
        assert hasattr(detail, "dataset_type")
        assert hasattr(detail, "total_size_bytes")
        assert hasattr(detail, "file_count")
        assert hasattr(detail, "visibility")
        assert hasattr(detail, "status")
        assert hasattr(detail, "created_at")


class TestDatasetListResponse:
    """Test DatasetListResponse schema."""

    def test_list_response_structure(self) -> None:
        """Should have correct structure."""
        response = DatasetListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
        assert response.items == []
        assert response.total == 0
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 0

    def test_list_response_with_items(self) -> None:
        """Should contain DatasetSummary items."""
        dataset = Dataset(
            id=1,
            name="list-dataset",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://bucket/path",
            dataset_type=DatasetType.IMAGE,
            owner_id=100,
        )
        summary = DatasetSummary.from_entity(dataset)
        response = DatasetListResponse(
            items=[summary],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )
        assert len(response.items) == 1
        assert response.items[0].name == "list-dataset"
        assert response.total == 1
