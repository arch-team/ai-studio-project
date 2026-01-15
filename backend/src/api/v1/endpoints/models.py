"""Models Endpoints - CRUD operations for ML models (T031a-c)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import CurrentUser
from src.api.v1.dependencies.auth import get_current_active_user, require_engineer
from src.api.v1.schemas.model import (
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
from src.application.services.model_service import ModelService
from src.core.database import get_db
from src.domain.exceptions import (
    EntityNotFoundError,
    InvalidStateTransitionError,
)
from src.infrastructure.persistence.repositories.model_repository_impl import (
    ModelRepository,
)
from src.infrastructure.persistence.repositories.training_job_repository_impl import (
    TrainingJobRepository,
)

router = APIRouter(prefix="/models", tags=["Models"])


# Valid sort fields for validation
VALID_SORT_FIELDS = {"created_at", "version", "model_name", "status", "updated_at"}


async def get_model_service(
    session: AsyncSession = Depends(get_db),
) -> ModelService:
    """Dependency for ModelService."""
    model_repository = ModelRepository(session)
    training_job_repository = TrainingJobRepository(session)
    # Note: checkpoint_repository would be added when checkpoint service is implemented
    return ModelService(
        model_repository=model_repository,
        training_job_repository=training_job_repository,
        checkpoint_repository=None,
    )


def _model_to_summary(model) -> ModelSummary:
    """Convert domain entity to summary response."""
    return ModelSummary(
        id=model.id,
        model_name=model.model_name,
        version=model.version,
        display_name=model.display_name,
        owner_id=model.owner_id,
        training_job_id=model.training_job_id,
        status=ModelStatusEnum(model.status.value.lower()),
        framework=ModelFrameworkEnum(model.framework.value.lower()),
        metrics=model.metrics,
        tags=model.tags,
        created_at=model.created_at,
        registered_at=model.registered_at,
    )


def _model_to_detail(model) -> ModelDetail:
    """Convert domain entity to detail response."""
    return ModelDetail(
        id=model.id,
        model_name=model.model_name,
        version=model.version,
        display_name=model.display_name,
        description=model.description,
        owner_id=model.owner_id,
        training_job_id=model.training_job_id,
        checkpoint_id=model.checkpoint_id,
        model_uri=model.model_uri,
        registry_arn=model.registry_arn,
        registry_status=model.registry_status,
        metrics=model.metrics,
        hyperparameters=model.hyperparameters,
        framework=ModelFrameworkEnum(model.framework.value.lower()),
        framework_version=model.framework_version,
        status=ModelStatusEnum(model.status.value.lower()),
        size_bytes=model.size_bytes,
        model_format=model.model_format,
        tags=model.tags,
        created_at=model.created_at,
        updated_at=model.updated_at,
        registered_at=model.registered_at,
        archived_at=model.archived_at,
    )


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
):
    """Create/register a new model (T031a)."""
    try:
        model_data = {
            "training_job_id": data.training_job_id,
            "checkpoint_id": data.checkpoint_id,
            "model_name": data.model_name,
            "display_name": data.display_name,
            "description": data.description,
            "framework": data.framework.value if data.framework else "pytorch",
            "framework_version": data.framework_version,
            "metrics": data.metrics,
            "hyperparameters": data.hyperparameters,
            "tags": data.tags,
        }

        model = await service.create_model(owner_id=current_user.user_id, data=model_data)
        return _model_to_detail(model)

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "",
    response_model=ModelListResponse,
    responses={401: {"model": ModelErrorResponse, "description": "Unauthorized"}},
)
async def list_models(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    training_job_id: int | None = Query(default=None, description="Filter by training job"),
    status_filter: ModelStatusEnum | None = Query(default=None, alias="status", description="Filter by status"),
    framework: ModelFrameworkEnum | None = Query(default=None, description="Filter by framework"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: ModelService = Depends(get_model_service),
):
    """List models with pagination and filters (T031b)."""
    # Validate sort_by field
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid sort field: {sort_by}. Valid fields: {', '.join(VALID_SORT_FIELDS)}",
        )

    # Non-admin users only see their own models
    owner_id = None
    if current_user.role not in ["admin", "manager"]:
        owner_id = current_user.user_id

    models, total = await service.list_models(
        owner_id=owner_id,
        training_job_id=training_job_id,
        status=status_filter.value if status_filter else None,
        framework=framework.value if framework else None,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ModelListResponse(
        items=[_model_to_summary(model) for model in models],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
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
):
    """Get model details by ID."""
    try:
        model = await service.get_model(model_id)

        # Check ownership for non-admin users
        if current_user.role not in ["admin", "manager"]:
            if model.owner_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this model",
                )

        return _model_to_detail(model)

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )


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
):
    """Get all versions of a model with optional comparison (T031c)."""
    try:
        # First check if base model exists
        model = await service.get_model(model_id)

        # Check ownership for non-admin users
        if current_user.role not in ["admin", "manager"]:
            if model.owner_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this model's versions",
                )

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

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
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
):
    """Delete/archive a model."""
    try:
        # First check if model exists and user has permission
        model = await service.get_model(model_id)
        if current_user.role not in ["admin", "manager"]:
            if model.owner_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this model",
                )

        await service.delete_model(model_id)
        return None

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )


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
):
    """Archive a model."""
    try:
        # First check if model exists and user has permission
        model = await service.get_model(model_id)
        if current_user.role not in ["admin", "manager"]:
            if model.owner_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to archive this model",
                )

        model = await service.archive_model(model_id)
        return _model_to_detail(model)

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
