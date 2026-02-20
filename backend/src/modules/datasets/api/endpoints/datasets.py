"""数据集 CRUD 操作端点。"""

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.auth.api.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.modules.datasets.api.dependencies import (
    get_dataset_service,
    get_owned_dataset,
)
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
from src.modules.datasets.domain.entities import Dataset
from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
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


@router.post("", response_model=DatasetDetail, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    data: CreateDatasetRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetail:
    """创建新数据集。

    注册一个新的数据集，包含指定的存储位置和元数据。
    """
    dataset_data = data.model_dump(mode="json")
    dataset = await service.create_dataset(
        owner_id=current_user.user_id,
        data=dataset_data,
    )
    return DatasetDetail.from_entity(dataset)


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    search: str | None = Query(default=None, description="全文搜索（搜索名称和描述）"),
    dataset_type: DatasetTypeEnum | None = Query(default=None, description="按数据集类型过滤"),
    storage_type: DatasetStorageTypeEnum | None = Query(default=None, description="按存储类型过滤"),
    visibility: DatasetVisibilityEnum | None = Query(default=None, description="按可见性过滤"),
    status_filter: DatasetStatusEnum | None = Query(default=None, alias="status", description="按状态过滤"),
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetListResponse:
    """列出数据集（支持分页、过滤和全文搜索）。

    返回当前用户拥有的数据集，管理员可查看所有数据集。
    """
    owner_id = get_owner_filter(current_user)

    datasets, total = await service.list_datasets(
        owner_id=owner_id,
        status=EnumMapper.to_domain(status_filter, DatasetStatus),
        dataset_type=EnumMapper.to_domain(dataset_type, DatasetType),
        storage_type=EnumMapper.to_domain(storage_type, DatasetStorageType),
        visibility=EnumMapper.to_domain(visibility, DatasetVisibility),
        search=search,
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


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(
    dataset_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetail:
    """根据 ID 获取数据集详情。

    返回特定数据集的详细信息。
    """
    dataset = await service.get_dataset(dataset_id)

    # 检查访问权限 - 所有者、管理员或公开数据集
    if not dataset.is_accessible_by(current_user.user_id) and not current_user.is_admin:
        check_resource_owner_or_privileged(dataset.owner_id, current_user, "dataset", "view")

    # 更新访问时间
    dataset.update_access_time()

    return DatasetDetail.from_entity(dataset)


@router.patch("/{dataset_id}", response_model=DatasetDetail)
async def update_dataset(
    data: UpdateDatasetRequest,
    dataset: Dataset = Depends(get_owned_dataset),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetail:
    """更新数据集元数据。"""
    assert dataset.id is not None, "Dataset must have ID"
    updated = await service.update_dataset(
        dataset_id=dataset.id,
        data=data.model_dump(exclude_unset=True, mode="json"),
    )
    return DatasetDetail.from_entity(updated)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset: Dataset = Depends(get_owned_dataset),
    service: DatasetService = Depends(get_dataset_service),
) -> None:
    """删除（归档）数据集。"""
    assert dataset.id is not None, "Dataset must have ID"
    await service.delete_dataset(dataset.id)
    return None


@router.post("/{dataset_id}/versions", response_model=DatasetDetail, status_code=status.HTTP_201_CREATED)
async def create_dataset_version(
    data: CreateDatasetVersionRequest,
    dataset: Dataset = Depends(get_owned_dataset),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetail:
    """创建数据集的新版本。"""
    assert dataset.id is not None, "Dataset must have ID"
    new_dataset = await service.create_version(
        dataset_id=dataset.id,
        version=data.version,
        storage_uri=data.storage_uri,
        description=data.description,
    )
    return DatasetDetail.from_entity(new_dataset)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查端点。"""
    return {"status": "ok"}
