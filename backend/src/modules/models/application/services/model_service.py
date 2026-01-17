"""Model Service - Business logic for ML model management."""

from typing import Any

from src.modules.models.domain.entities import Model
from src.modules.models.domain.repositories import IModelRepository
from src.modules.models.domain.value_objects import ModelFramework, ModelStatus
from src.shared.application import BaseService
from src.shared.domain.exceptions import (
    EntityNotFoundError,
    InvalidStateTransitionError,
)
from src.shared.utils import EnumMapper, utc_now


class ModelService(BaseService[Model, int]):
    """Service for managing ML models."""

    def __init__(
        self,
        model_repository: IModelRepository,
        training_job_repository: Any | None = None,
        checkpoint_repository: Any | None = None,
    ):
        super().__init__(model_repository, "Model")
        self._model_repository = model_repository
        self._training_job_repository = training_job_repository
        self._checkpoint_repository = checkpoint_repository

    async def create_model(self, owner_id: int, data: dict) -> Model:
        """Create a new model."""
        training_job_id = data["training_job_id"]
        checkpoint_id = data["checkpoint_id"]
        model_name = data["model_name"]

        # Validate training job exists
        if self._training_job_repository:
            training_job = await self._training_job_repository.get_by_id(
                training_job_id
            )
            if training_job is None:
                raise EntityNotFoundError("Training job", str(training_job_id))

        # Validate checkpoint exists
        if self._checkpoint_repository:
            checkpoint = await self._checkpoint_repository.get_by_id(checkpoint_id)
            if checkpoint is None:
                raise EntityNotFoundError("Checkpoint", str(checkpoint_id))

        # Determine version
        version = "v1"
        latest_model = await self._model_repository.get_latest_version(model_name)
        if latest_model:
            version = Model.increment_version(latest_model.version)

        # Map framework from string
        framework = EnumMapper.from_string(
            data.get("framework"),
            ModelFramework,
            default=ModelFramework.PYTORCH,
        )

        # Create domain entity
        model = Model(
            id=0,  # Will be set by database
            model_name=model_name,
            owner_id=owner_id,
            version=version,
            display_name=data.get("display_name"),
            description=data.get("description"),
            training_job_id=training_job_id,
            checkpoint_id=checkpoint_id,
            framework=framework,
            framework_version=data.get("framework_version"),
            metrics=data.get("metrics"),
            hyperparameters=data.get("hyperparameters"),
            tags=data.get("tags"),
            status=ModelStatus.REGISTERED,
            registered_at=utc_now(),
        )

        # Save to database
        return await self._model_repository.create(model)

    async def get_model(self, model_id: int) -> Model:
        """Get model by ID."""
        return await self._get_or_raise(model_id)

    async def list_models(
        self,
        owner_id: int | None = None,
        training_job_id: int | None = None,
        status: str | None = None,
        framework: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Model], int]:
        """List models with filters and pagination."""
        return await self._model_repository.list_models(
            owner_id=owner_id,
            training_job_id=training_job_id,
            status=status,
            framework=framework,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_model_versions(
        self, model_id: int, compare_with: int | None = None
    ) -> dict[str, Any]:
        """Get all versions of a model with optional comparison.

        Args:
            model_id: ID of the model to get versions for
            compare_with: Optional ID of another model version to compare with

        Returns:
            Dictionary with versions list and optional comparison
        """
        # Get the base model
        model = await self._get_or_raise(model_id)

        # Get all versions
        versions = await self._model_repository.list_versions(model.model_name)

        result: dict[str, Any] = {
            "versions": [
                {
                    "id": v.id,
                    "version": v.version,
                    "status": v.status,
                    "metrics": v.metrics,
                    "hyperparameters": v.hyperparameters,
                    "created_at": v.created_at,
                    "registered_at": v.registered_at,
                }
                for v in versions
            ]
        }

        # Add comparison if requested
        if compare_with is not None:
            compare_model = await self._model_repository.get_by_id(compare_with)
            if compare_model is not None:
                comparison = await self.compare_versions(model_id, compare_with)
                result["comparison"] = comparison

        return result

    async def compare_versions(
        self, model_id_1: int, model_id_2: int
    ) -> dict[str, Any]:
        """Compare two model versions.

        Args:
            model_id_1: First model ID (v1)
            model_id_2: Second model ID (v2)

        Returns:
            Comparison result with metrics diff and hyperparameter changes
        """
        model_1 = await self._get_or_raise(model_id_1)
        model_2 = await self._get_or_raise(model_id_2)

        # Calculate metrics diff
        metrics_diff: dict[str, Any] = {}
        metrics_1 = model_1.metrics or {}
        metrics_2 = model_2.metrics or {}
        all_metrics = set(metrics_1.keys()) | set(metrics_2.keys())

        for metric in all_metrics:
            v1 = metrics_1.get(metric)
            v2 = metrics_2.get(metric)
            diff = None
            diff_percent = None
            if v1 is not None and v2 is not None:
                diff = v2 - v1
                if v1 != 0:
                    diff_percent = ((v2 - v1) / v1) * 100
            metrics_diff[metric] = {
                "v1": v1,
                "v2": v2,
                "diff": diff,
                "diff_percent": diff_percent,
            }

        # Find changed hyperparameters
        hyperparams_changed: list[str] = []
        hp_1 = model_1.hyperparameters or {}
        hp_2 = model_2.hyperparameters or {}
        all_hp = set(hp_1.keys()) | set(hp_2.keys())

        for hp in all_hp:
            if hp_1.get(hp) != hp_2.get(hp):
                hyperparams_changed.append(hp)

        # Check framework change
        framework_changed = model_1.framework != model_2.framework

        # Check tags changes
        tags_1 = set(model_1.tags or [])
        tags_2 = set(model_2.tags or [])
        tags_added = list(tags_2 - tags_1)
        tags_removed = list(tags_1 - tags_2)

        return {
            "metrics_diff": metrics_diff,
            "hyperparams_changed": hyperparams_changed,
            "framework_changed": framework_changed,
            "tags_added": tags_added,
            "tags_removed": tags_removed,
        }

    async def register_model(self, model_id: int) -> Model:
        """Register a model (transition from TRAINING to REGISTERED)."""
        model = await self._get_or_raise(model_id)

        if model.status != ModelStatus.TRAINING:
            raise InvalidStateTransitionError(
                "Model", model.status.value, ModelStatus.REGISTERED.value
            )

        model.register()
        return await self._model_repository.update(model)

    async def archive_model(self, model_id: int) -> Model:
        """Archive a model."""
        model = await self._get_or_raise(model_id)

        if not model.can_transition_to(ModelStatus.ARCHIVED):
            raise InvalidStateTransitionError(
                "Model", model.status.value, ModelStatus.ARCHIVED.value
            )

        model.archive()
        return await self._model_repository.update(model)

    async def delete_model(self, model_id: int) -> None:
        """Delete a model (soft delete)."""
        await self._get_or_raise(model_id)  # Verify model exists
        # Soft delete (archive)
        await self._model_repository.soft_delete(model_id)
