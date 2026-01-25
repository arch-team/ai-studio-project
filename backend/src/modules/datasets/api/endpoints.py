"""Datasets API endpoints - CRUD operations for datasets."""

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.auth.api.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.modules.datasets.api.dependencies import get_dataset_service
from src.modules.datasets.api.schemas import (
    CreateDatasetRequest,
    CreateDatasetVersionRequest,
    DatasetDetail,
    DatasetListResponse,
    DatasetStatusEnum,
    DatasetStorageTypeEnum,
    DatasetSummary,
    DatasetTypeEnum,
    DatasetVisibilityEnum,
    UpdateDatasetRequest,
)
from src.modules.datasets.application.services import DatasetService
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetType,
    DatasetVisibility,
)
from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)
from src.shared.utils import EnumMapper

router = APIRouter()


@router.post(
    "",
    response_model=DatasetDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset(
    data: CreateDatasetRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Create a new dataset.

    Registers a new dataset with the specified storage location and metadata.
    """
    dataset_data = data.model_dump(mode="json")
    dataset = await service.create_dataset(
        owner_id=current_user.user_id,
        data=dataset_data,
    )
    return DatasetDetail.from_entity(dataset)


@router.get(
    "",
    response_model=DatasetListResponse,
)
async def list_datasets(
    page: PageParam,
    page_size: PageSizeParam,
    dataset_type: DatasetTypeEnum | None = Query(
        default=None, description="Filter by dataset type"
    ),
    storage_type: DatasetStorageTypeEnum | None = Query(
        default=None, description="Filter by storage type"
    ),
    visibility: DatasetVisibilityEnum | None = Query(
        default=None, description="Filter by visibility"
    ),
    status_filter: DatasetStatusEnum | None = Query(
        default=None, alias="status", description="Filter by status"
    ),
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """List datasets with pagination and filters.

    Returns datasets owned by the current user, or all datasets if admin.
    """
    owner_id = get_owner_filter(current_user)

    datasets, total = await service.list_datasets(
        owner_id=owner_id,
        status=EnumMapper.to_domain(status_filter, DatasetStatus),
        dataset_type=EnumMapper.to_domain(dataset_type, DatasetType),
        visibility=EnumMapper.to_domain(visibility, DatasetVisibility),
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )

    return DatasetListResponse(
        **build_paginated_response(
            items=[DatasetSummary.from_entity(ds) for ds in datasets],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetDetail,
)
async def get_dataset(
    dataset_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """Get dataset details by ID.

    Returns detailed information about a specific dataset.
    """
    dataset = await service.get_dataset(dataset_id)

    # Check access - owner, admin, or public dataset
    if not dataset.is_accessible_by(current_user.user_id) and not current_user.is_admin:
        check_resource_owner_or_privileged(
            dataset.owner_id, current_user, "dataset", "view"
        )

    # Update access time
    dataset.update_access_time()

    return DatasetDetail.from_entity(dataset)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetDetail,
)
async def update_dataset(
    dataset_id: int,
    data: UpdateDatasetRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Update dataset metadata.

    Only description, tags, and visibility can be updated.
    """
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "update"
    )

    dataset = await service.update_dataset(
        dataset_id=dataset_id,
        data=data.model_dump(exclude_unset=True, mode="json"),
    )
    return DatasetDetail.from_entity(dataset)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset(
    dataset_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Delete (archive) a dataset.

    Soft-deletes the dataset by setting its status to ARCHIVED.
    """
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "delete"
    )

    await service.delete_dataset(dataset_id)
    return None


@router.post(
    "/{dataset_id}/versions",
    response_model=DatasetDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset_version(
    dataset_id: int,
    data: CreateDatasetVersionRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
):
    """Create a new version of a dataset.

    Creates a new dataset entry with the same name but different version.
    """
    dataset = await service.get_dataset(dataset_id)
    check_resource_owner_or_privileged(
        dataset.owner_id, current_user, "dataset", "create version of"
    )

    new_dataset = await service.create_version(
        dataset_id=dataset_id,
        version=data.version,
        storage_uri=data.storage_uri,
        description=data.description,
    )
    return DatasetDetail.from_entity(new_dataset)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
