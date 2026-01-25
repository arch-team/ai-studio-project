"""Dataset Service - Business logic for dataset management."""

from src.modules.datasets.domain.entities import Dataset
from src.modules.datasets.domain.exceptions import DatasetNotFoundError
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)
from src.shared.application.enhanced_base_service import EnhancedBaseService
from src.shared.domain.exceptions import DuplicateEntityError
from src.shared.utils import EnumMapper, utc_now


class DatasetService(EnhancedBaseService[Dataset, int]):
    """Service for managing datasets."""

    def __init__(self, repository: IDatasetRepository):
        """Initialize dataset service.

        Args:
            repository: Dataset repository instance
        """
        super().__init__(repository, "Dataset")
        self._not_found_error_factory = lambda id_: DatasetNotFoundError(dataset_id=id_)

    async def create_dataset(self, owner_id: int, data: dict) -> Dataset:
        """Create a new dataset.

        Args:
            owner_id: Owner user ID
            data: Dataset configuration data

        Returns:
            Created dataset entity

        Raises:
            DuplicateEntityError: If name+version already exists
        """
        name = data["name"]
        version = data.get("version", "v1")

        # Validate unique name+version
        if await self._repository.exists_by_name_and_version(name, version):
            raise DuplicateEntityError("Dataset", f"{name}/{version}")

        # Convert enums from string
        storage_type = EnumMapper.from_string(
            data["storage_type"], DatasetStorageType, DatasetStorageType.S3
        )
        dataset_type = EnumMapper.from_string(
            data["dataset_type"], DatasetType, DatasetType.CUSTOM
        )
        visibility = EnumMapper.from_string(
            data.get("visibility", "PRIVATE"),
            DatasetVisibility,
            DatasetVisibility.PRIVATE,
        )

        # Create dataset entity
        dataset = Dataset(
            id=0,  # Will be assigned by database
            name=name,
            version=version,
            description=data.get("description"),
            storage_type=storage_type,
            storage_uri=data["storage_uri"],
            dataset_type=dataset_type,
            data_format=data.get("data_format"),
            tags=data.get("tags"),
            visibility=visibility,
            status=DatasetStatus.PREPARING,
            owner_id=owner_id,
        )

        return await self._repository.add(dataset)

    async def get_dataset(self, dataset_id: int) -> Dataset:
        """Get dataset by ID.

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset entity

        Raises:
            DatasetNotFoundError: If dataset not found
        """
        return await self._get_or_raise(dataset_id)

    async def list_datasets(
        self,
        owner_id: int,
        status: DatasetStatus | None = None,
        dataset_type: DatasetType | None = None,
        visibility: DatasetVisibility | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Dataset], int]:
        """List datasets with filters and pagination.

        Args:
            owner_id: Owner user ID
            status: Filter by status
            dataset_type: Filter by dataset type
            visibility: Filter by visibility
            page: Page number (1-based)
            page_size: Items per page
            sort_by: Sort column
            sort_order: Sort direction

        Returns:
            Tuple of (datasets, total_count)
        """
        return await self._repository.list_by_owner(
            owner_id=owner_id,
            status=status,
            dataset_type=dataset_type,
            visibility=visibility,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update_dataset(self, dataset_id: int, data: dict) -> Dataset:
        """Update dataset metadata.

        Args:
            dataset_id: Dataset ID
            data: Update data (description, tags, visibility)

        Returns:
            Updated dataset entity

        Raises:
            DatasetNotFoundError: If dataset not found
        """
        dataset = await self._get_or_raise(dataset_id)

        # Update allowed fields
        if "description" in data:
            dataset.description = data["description"]

        if "tags" in data:
            dataset.tags = data["tags"]

        if "visibility" in data and data["visibility"] is not None:
            dataset.visibility = EnumMapper.from_string(
                data["visibility"], DatasetVisibility, dataset.visibility
            )

        dataset.updated_at = utc_now()

        return await self._repository.update(dataset)

    async def delete_dataset(self, dataset_id: int) -> None:
        """Delete (archive) a dataset.

        Args:
            dataset_id: Dataset ID

        Raises:
            DatasetNotFoundError: If dataset not found
        """
        dataset = await self._get_or_raise(dataset_id)

        # Soft delete by archiving
        if dataset.can_transition_to(DatasetStatus.ARCHIVED):
            dataset.archive()
        else:
            # Already archived or in error state - just update timestamp
            dataset.updated_at = utc_now()

        await self._repository.update(dataset)

    async def create_version(
        self,
        dataset_id: int,
        version: str,
        storage_uri: str | None = None,
        description: str | None = None,
    ) -> Dataset:
        """Create a new version of a dataset.

        Args:
            dataset_id: Source dataset ID
            version: New version identifier
            storage_uri: Storage URI for new version (optional)
            description: Version description

        Returns:
            New dataset version entity

        Raises:
            DatasetNotFoundError: If source dataset not found
            DuplicateEntityError: If version already exists
        """
        # Get source dataset
        source = await self._get_or_raise(dataset_id)

        # Validate unique name+version
        if await self._repository.exists_by_name_and_version(source.name, version):
            raise DuplicateEntityError("Dataset", f"{source.name}/{version}")

        # Create new version from source
        new_dataset = Dataset(
            id=0,
            name=source.name,
            version=version,
            description=description or source.description,
            storage_type=source.storage_type,
            storage_uri=storage_uri or source.storage_uri,
            dataset_type=source.dataset_type,
            data_format=source.data_format,
            tags=source.tags.copy() if source.tags else None,
            visibility=source.visibility,
            status=DatasetStatus.PREPARING,
            owner_id=source.owner_id,
        )

        return await self._repository.add(new_dataset)

    async def mark_available(self, dataset_id: int) -> Dataset:
        """Mark dataset as available.

        Args:
            dataset_id: Dataset ID

        Returns:
            Updated dataset entity

        Raises:
            DatasetNotFoundError: If dataset not found
            InvalidStateTransitionError: If transition not allowed
        """
        dataset = await self._get_or_raise(dataset_id)
        dataset.mark_available()
        return await self._repository.update(dataset)

    async def mark_error(self, dataset_id: int) -> Dataset:
        """Mark dataset as error.

        Args:
            dataset_id: Dataset ID

        Returns:
            Updated dataset entity

        Raises:
            DatasetNotFoundError: If dataset not found
            InvalidStateTransitionError: If transition not allowed
        """
        dataset = await self._get_or_raise(dataset_id)
        dataset.mark_error()
        return await self._repository.update(dataset)
