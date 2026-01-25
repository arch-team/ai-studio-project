"""Model Service - Business logic for ML model management."""

from typing import Any

from src.modules.models.domain.entities import Model
from src.modules.models.domain.repositories import IModelRepository
from src.modules.models.domain.value_objects import ModelFramework, ModelStatus
from src.shared.application.enhanced_base_service import EnhancedBaseService
from src.shared.domain.exceptions import (
    InvalidStateTransitionError,
)
from src.shared.domain.interfaces import IEntityExistenceChecker
from src.shared.utils import EnumMapper, utc_now


class ModelService(EnhancedBaseService[Model, int]):
    """Service for managing ML models."""

    def __init__(
        self,
        model_repository: IModelRepository,
        training_job_checker: IEntityExistenceChecker | None = None,
        checkpoint_checker: IEntityExistenceChecker | None = None,
    ):
        super().__init__(model_repository, "Model")
        self._model_repository = model_repository
        self._training_job_checker = training_job_checker
        self._checkpoint_checker = checkpoint_checker

    async def _determine_model_version(self, model_name: str) -> str:
        """确定模型版本号."""
        latest_model = await self._model_repository.get_latest_version(model_name)
        return Model.increment_version(latest_model.version) if latest_model else "v1"

    async def create_model(self, owner_id: int, data: dict) -> Model:
        """Create a new model."""
        # 提取关键字段
        training_job_id = data["training_job_id"]
        checkpoint_id = data["checkpoint_id"]
        model_name = data["model_name"]

        # 验证关联实体
        await self._validate_entity_exists(self._training_job_checker, "TrainingJob", training_job_id)
        await self._validate_entity_exists(self._checkpoint_checker, "Checkpoint", checkpoint_id)

        # 确定版本号
        version = await self._determine_model_version(model_name)

        # 映射框架枚举
        framework = EnumMapper.from_string(
            data.get("framework"),
            ModelFramework,
            default=ModelFramework.PYTORCH,
        )

        # 创建领域实体
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

    async def get_model_versions(self, model_id: int, compare_with: int | None = None) -> dict[str, Any]:
        """Get all versions of a model with optional comparison."""
        model = await self._get_or_raise(model_id)
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

        # 添加版本比较（如果请求）
        if compare_with is not None:
            compare_model = await self._model_repository.get_by_id(compare_with)
            if compare_model is not None:
                comparison = await self.compare_versions(model_id, compare_with)
                result["comparison"] = comparison

        return result

    def _calculate_metric_diff(self, metrics_1: dict, metrics_2: dict) -> dict[str, Any]:
        """计算指标差异."""
        metrics_diff = {}
        all_metrics = set(metrics_1.keys()) | set(metrics_2.keys())

        for metric in all_metrics:
            v1 = metrics_1.get(metric)
            v2 = metrics_2.get(metric)

            diff = None
            diff_percent = None

            if v1 is not None and v2 is not None:
                diff = v2 - v1
                diff_percent = ((v2 - v1) / v1 * 100) if v1 != 0 else None

            metrics_diff[metric] = {
                "v1": v1,
                "v2": v2,
                "diff": diff,
                "diff_percent": diff_percent,
            }

        return metrics_diff

    def _find_changed_hyperparams(self, hyperparams_1: dict, hyperparams_2: dict) -> list[str]:
        """查找变更的超参数."""
        all_hp = set(hyperparams_1.keys()) | set(hyperparams_2.keys())
        return [hp for hp in all_hp if hyperparams_1.get(hp) != hyperparams_2.get(hp)]

    def _analyze_tag_changes(self, tags_1: list[str] | None, tags_2: list[str] | None) -> tuple[list[str], list[str]]:
        """分析标签变化."""
        tags_set_1 = set(tags_1 or [])
        tags_set_2 = set(tags_2 or [])
        return list(tags_set_2 - tags_set_1), list(tags_set_1 - tags_set_2)

    async def compare_versions(self, model_id_1: int, model_id_2: int) -> dict[str, Any]:
        """Compare two model versions and return metrics/hyperparameter diff."""
        model_1 = await self._get_or_raise(model_id_1)
        model_2 = await self._get_or_raise(model_id_2)

        # 计算各维度差异
        metrics_diff = self._calculate_metric_diff(model_1.metrics or {}, model_2.metrics or {})

        hyperparams_changed = self._find_changed_hyperparams(
            model_1.hyperparameters or {}, model_2.hyperparameters or {}
        )

        tags_added, tags_removed = self._analyze_tag_changes(model_1.tags, model_2.tags)

        return {
            "metrics_diff": metrics_diff,
            "hyperparams_changed": hyperparams_changed,
            "framework_changed": model_1.framework != model_2.framework,
            "tags_added": tags_added,
            "tags_removed": tags_removed,
        }

    async def register_model(self, model_id: int) -> Model:
        """Register a model (transition from TRAINING to REGISTERED)."""
        model = await self._get_or_raise(model_id)

        if model.status != ModelStatus.TRAINING:
            raise InvalidStateTransitionError("Model", model.status.value, ModelStatus.REGISTERED.value)

        model.register()
        return await self._model_repository.update(model)

    async def archive_model(self, model_id: int) -> Model:
        """Archive a model."""
        model = await self._get_or_raise(model_id)

        # Use base class method for state transition validation
        self._validate_state_transition(
            model, ModelStatus.ARCHIVED, [ModelStatus.REGISTERED, ModelStatus.TRAINING]  # Allowed from states
        )

        model.archive()
        return await self._model_repository.update(model)

    async def delete_model(self, model_id: int) -> None:
        """Delete a model (soft delete)."""
        await self._get_or_raise(model_id)  # Verify model exists
        await self._model_repository.soft_delete(model_id)
