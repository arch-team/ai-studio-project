"""Models Endpoints - CRUD operations for ML models."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.auth.api.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.modules.models.api.dependencies import get_model_service
from src.modules.models.api.schemas import (
    CreateModelRequest,
    ModelDetail,
    ModelErrorResponse,
    ModelFrameworkEnum,
    ModelListResponse,
    ModelStatusEnum,
    ModelSummary,
    ModelVersionsResponse,
    ModelVersionSummary,
    VersionComparison,
)
from src.modules.models.application.services import ModelService
from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)

router = APIRouter()


# Valid sort fields for validation
VALID_SORT_FIELDS = {"created_at", "version", "model_name", "status", "updated_at"}


@router.post(
    "",
    response_model=ModelDetail,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ModelErrorResponse, "description": "Training job or checkpoint not found"},
        422: {"model": ModelErrorResponse, "description": "Validation error"},
    },
)
async def create_model(
    data: CreateModelRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: ModelService = Depends(get_model_service),
) -> ModelDetail:
    """Create/register a new model."""
    model_data = data.model_dump(mode="json")
    model = await service.create_model(owner_id=current_user.user_id, data=model_data)
    return ModelDetail.from_entity(model)


@router.get(
    "",
    response_model=ModelListResponse,
    responses={401: {"model": ModelErrorResponse, "description": "Unauthorized"}},
)
async def list_models(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    training_job_id: int | None = Query(default=None, description="Filter by training job"),
    status_filter: ModelStatusEnum | None = Query(default=None, alias="status", description="Filter by status"),
    framework: ModelFrameworkEnum | None = Query(default=None, description="Filter by framework"),
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: ModelService = Depends(get_model_service),
) -> ModelListResponse:
    """List models with pagination and filters."""
    # Validate sort_by field
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid sort field: {sort_by}. Valid fields: {', '.join(VALID_SORT_FIELDS)}",
        )

    models, total = await service.list_models(
        owner_id=get_owner_filter(current_user),
        training_job_id=training_job_id,
        status=status_filter.value if status_filter else None,
        framework=framework.value if framework else None,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )

    return ModelListResponse(
        **build_paginated_response(
            items=[ModelSummary.from_entity(model) for model in models],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/{model_id}",
    response_model=ModelDetail,
    responses={
        404: {"model": ModelErrorResponse, "description": "Model not found"},
        422: {"model": ModelErrorResponse, "description": "Invalid ID format"},
    },
)
async def get_model(
    model_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: ModelService = Depends(get_model_service),
) -> ModelDetail:
    """Get model details by ID."""
    model = await service.get_model(model_id)
    check_resource_owner_or_privileged(model.owner_id, current_user, "model", "view")
    return ModelDetail.from_entity(model)


@router.get(
    "/{model_id}/versions",
    response_model=ModelVersionsResponse,
    responses={
        404: {"model": ModelErrorResponse, "description": "Model not found"},
    },
)
async def get_model_versions(
    model_id: int,
    compare_with: int | None = Query(default=None, description="Version ID to compare with"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: ModelService = Depends(get_model_service),
) -> ModelVersionsResponse:
    """Get all versions of a model with optional comparison."""
    model = await service.get_model(model_id)
    check_resource_owner_or_privileged(model.owner_id, current_user, "model", "view versions of")
    result = await service.get_model_versions(model_id, compare_with)

    # Convert to response format
    versions = [
        ModelVersionSummary(
            id=v["id"],
            version=v["version"],
            status=ModelStatusEnum(v["status"].value.lower()),
            metrics=v["metrics"],
            hyperparameters=v["hyperparameters"],
            created_at=v["created_at"],
            registered_at=v["registered_at"],
        )
        for v in result["versions"]
    ]

    comparison = None
    if "comparison" in result and result["comparison"]:
        comp_data = result["comparison"]
        comparison = VersionComparison(
            metrics_diff=comp_data.get("metrics_diff", {}),
            hyperparams_changed=comp_data.get("hyperparams_changed", []),
            framework_changed=comp_data.get("framework_changed", False),
            tags_added=comp_data.get("tags_added", []),
            tags_removed=comp_data.get("tags_removed", []),
        )

    return ModelVersionsResponse(
        model_name=model.model_name,
        versions=versions,
        comparison=comparison,
    )


@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ModelErrorResponse, "description": "Model not found"},
    },
)
async def delete_model(
    model_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: ModelService = Depends(get_model_service),
) -> None:
    """Delete/archive a model."""
    model = await service.get_model(model_id)
    check_resource_owner_or_privileged(model.owner_id, current_user, "model", "delete")
    await service.delete_model(model_id)
    return None


@router.post(
    "/{model_id}/archive",
    response_model=ModelDetail,
    responses={
        404: {"model": ModelErrorResponse, "description": "Model not found"},
        409: {"model": ModelErrorResponse, "description": "Invalid state transition"},
    },
)
async def archive_model(
    model_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: ModelService = Depends(get_model_service),
) -> ModelDetail:
    """Archive a model."""
    model = await service.get_model(model_id)
    check_resource_owner_or_privileged(model.owner_id, current_user, "model", "archive")
    model = await service.archive_model(model_id)
    return ModelDetail.from_entity(model)
