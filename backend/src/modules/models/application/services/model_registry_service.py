"""Model Registry Service - SageMaker Model Registry 集成服务 (T038a).

功能:
- 训练完成自动注册模型
- 创建和管理模型版本
- 模型审批流程 (批准/拒绝)
- 同步 Registry 状态
- 获取模型血缘关系
"""

import logging
from typing import Any

from src.modules.models.application.interfaces import ISageMakerClient
from src.modules.models.domain.entities import Model
from src.modules.models.domain.exceptions import ModelNotFoundError
from src.modules.models.domain.repositories import IModelRepository
from src.shared.utils import utc_now

logger = logging.getLogger(__name__)


class ModelRegistryService:
    """SageMaker Model Registry 集成服务"""

    def __init__(
        self,
        model_repository: IModelRepository,
        sagemaker_client: ISageMakerClient,
    ):
        self._model_repo = model_repository
        self._sagemaker = sagemaker_client

    # =========================================================================
    # 模型注册
    # =========================================================================

    async def register_model(
        self,
        model_id: int,
        model_artifact_uri: str,
        metrics: dict[str, Any] | None = None,
        inference_specification: dict[str, Any] | None = None,
    ) -> Model:
        """注册模型到 SageMaker Model Registry

        Args:
            model_id: 模型 ID
            model_artifact_uri: 模型 S3 URI
            metrics: 训练指标
            inference_specification: 推理规格

        Returns:
            Model: 更新后的模型实体
        """
        model = await self._get_model_or_raise(model_id)

        # 创建模型包组（如果不存在）
        group_name = self._generate_model_package_group_name(model.model_name)

        try:
            await self._sagemaker.create_model_package_group(
                model_package_group_name=group_name,
                model_package_group_description=f"Model group for {model.model_name}",
            )
        except Exception as e:
            # 组已存在或其他错误，记录并继续
            logger.debug(f"Model package group '{group_name}' creation skipped: {type(e).__name__}: {e}")

        # 创建模型包
        model_package_arn = await self._sagemaker.create_model_package(
            model_package_group_name=group_name,
            model_url=model_artifact_uri,
            inference_specification=inference_specification,
            model_metrics=self._format_metrics(metrics) if metrics else None,
            model_approval_status="PendingManualApproval",
            metadata={
                "model_id": str(model_id),
                "model_name": model.model_name,
                "version": model.version,
            },
        )

        # 更新模型记录
        model.registry_arn = model_package_arn
        model.registry_status = "PendingManualApproval"
        model.register()  # 状态转换: TRAINING -> REGISTERED

        return await self._model_repo.update(model)

    # =========================================================================
    # 版本管理
    # =========================================================================

    async def create_model_version(
        self,
        model_id: int,
        model_artifact_uri: str,
        metrics: dict[str, Any] | None = None,
    ) -> str:
        """创建新的模型版本

        Args:
            model_id: 模型 ID
            model_artifact_uri: 模型 S3 URI
            metrics: 训练指标

        Returns:
            str: 新版本的模型包 ARN
        """
        model = await self._get_model_or_raise(model_id)
        group_name = self._generate_model_package_group_name(model.model_name)

        model_package_arn = await self._sagemaker.create_model_package(
            model_package_group_name=group_name,
            model_url=model_artifact_uri,
            model_metrics=self._format_metrics(metrics) if metrics else None,
            model_approval_status="PendingManualApproval",
        )

        logger.info(f"Created new model version: {model_package_arn}")
        return model_package_arn

    async def update_model_approval_status(
        self,
        model_id: int,
        status: str,
        description: str | None = None,
    ) -> None:
        """更新模型审批状态

        Args:
            model_id: 模型 ID
            status: 审批状态 (Approved, Rejected, PendingManualApproval)
            description: 审批说明
        """
        model = await self._get_model_or_raise(model_id)

        if model.registry_arn is None:
            raise ValueError(f"Model {model_id} is not registered in Model Registry")

        await self._sagemaker.update_model_package(
            model_package_arn=model.registry_arn,
            model_approval_status=status,
            approval_description=description,
        )

        # 更新本地记录
        model.registry_status = status
        model.updated_at = utc_now()
        await self._model_repo.update(model)

        logger.info(f"Model {model_id} approval status updated to {status}")

    # =========================================================================
    # 归档功能
    # =========================================================================

    async def archive_model(self, model_id: int) -> Model:
        """归档模型

        Args:
            model_id: 模型 ID

        Returns:
            Model: 更新后的模型实体
        """
        model = await self._get_model_or_raise(model_id)
        model.archive()
        return await self._model_repo.update(model)

    # =========================================================================
    # 血缘关系
    # =========================================================================

    async def get_model_lineage(self, model_id: int) -> dict[str, Any]:
        """获取模型血缘关系

        Args:
            model_id: 模型 ID

        Returns:
            dict: 血缘信息 (训练任务、检查点等)
        """
        model = await self._get_model_or_raise(model_id)

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "version": model.version,
            "training_job_id": model.training_job_id,
            "checkpoint_id": model.checkpoint_id,
            "model_uri": model.model_uri,
            "registry_arn": model.registry_arn,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "registered_at": model.registered_at.isoformat() if model.registered_at else None,
        }

    # =========================================================================
    # 状态同步
    # =========================================================================

    async def sync_registry_status(self, model_id: int) -> Model:
        """同步 Registry 状态到本地数据库

        Args:
            model_id: 模型 ID

        Returns:
            Model: 更新后的模型实体
        """
        model = await self._get_model_or_raise(model_id)

        if model.registry_arn is None:
            return model

        # 从 SageMaker 获取最新状态
        package_info = await self._sagemaker.describe_model_package(model.registry_arn)

        # 更新本地记录
        model.registry_status = package_info.get("ModelApprovalStatus")
        model.updated_at = utc_now()

        return await self._model_repo.update(model)

    # =========================================================================
    # 私有方法
    # =========================================================================

    async def _get_model_or_raise(self, model_id: int) -> Model:
        """获取模型或抛出异常"""
        model = await self._model_repo.get_by_id(model_id)
        if model is None:
            raise ModelNotFoundError(str(model_id))
        return model

    def _generate_model_package_group_name(self, model_name: str) -> str:
        """生成模型包组名称"""
        # 清理名称，符合 SageMaker 命名规范
        clean_name = model_name.replace("_", "-").lower()
        return f"ai-training-platform-{clean_name}"

    def _format_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """格式化指标为 SageMaker 格式"""
        return {
            "ModelQuality": {
                "Statistics": {
                    "ContentType": "application/json",
                    "S3Uri": None,  # 可以指向指标文件
                },
                "Constraints": None,
            },
            "CustomMetrics": metrics,
        }
