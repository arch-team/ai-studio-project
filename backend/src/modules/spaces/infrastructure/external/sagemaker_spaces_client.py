"""SageMaker Spaces 客户端实现 (T085).

优先使用 sagemaker-hyperpod SDK Space 模块进行 Space 管理操作。
若 SDK 不支持特定配置 (如自定义存储大小、生命周期脚本) 则使用 aioboto3 调用 SageMaker API。
"""

from functools import lru_cache
from typing import Any

import aioboto3
import structlog

from src.modules.spaces.application.interfaces import ISageMakerSpacesClient
from src.modules.spaces.domain.exceptions import SpaceError
from src.shared.infrastructure import get_settings

logger = structlog.get_logger(__name__)


class SageMakerSpacesClient(ISageMakerSpacesClient):
    """SageMaker Spaces 客户端异步实现.

    使用 aioboto3 进行异步 SageMaker API 调用，管理 Studio Space 的生命周期。
    """

    def __init__(self) -> None:
        """初始化 SageMaker Spaces 客户端."""
        settings = get_settings()
        self._region = settings.aws_region
        self._session = aioboto3.Session()

    async def create_space(
        self,
        name: str,
        instance_type: str,
        ide_type: str = "jupyterlab",
        lifecycle_config_arn: str | None = None,
        storage_size_gb: int = 10,
    ) -> dict[str, Any]:
        """创建 SageMaker Studio Space."""
        logger.info(
            "sagemaker_space_creating",
            space_name=name,
            instance_type=instance_type,
            ide_type=ide_type,
            storage_size_gb=storage_size_gb,
        )

        # 构建 Space 应用设置
        app_type = "JupyterLab" if ide_type == "jupyterlab" else "CodeEditor"
        space_settings: dict[str, Any] = {
            "AppType": app_type,
        }

        # JupyterLab 和 CodeEditor 使用不同的设置键
        app_settings_key = "JupyterLabAppSettings" if app_type == "JupyterLab" else "CodeEditorAppSettings"
        app_settings: dict[str, Any] = {
            "DefaultResourceSpec": {
                "InstanceType": instance_type,
            },
        }

        # 添加生命周期配置
        if lifecycle_config_arn:
            app_settings["DefaultResourceSpec"]["LifecycleConfigArn"] = lifecycle_config_arn

        space_settings[app_settings_key] = app_settings

        # 添加 EFS 存储配置
        space_settings["SpaceStorageSettings"] = {
            "EbsStorageSettings": {
                "EbsVolumeSizeInGb": storage_size_gb,
            }
        }

        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                # 获取 SageMaker Domain ID (从环境配置或自动发现)
                domain_id = await self._get_domain_id(sm)

                response: dict[str, Any] = await sm.create_space(
                    DomainId=domain_id,
                    SpaceName=name,
                    SpaceSettings=space_settings,
                    OwnershipSettings={"OwnerUserProfileName": "default"},
                    SpaceDisplayName=name,
                )

                logger.info(
                    "sagemaker_space_created",
                    space_name=name,
                    space_arn=response.get("SpaceArn"),
                )

                return {
                    "name": name,
                    "arn": response.get("SpaceArn", ""),
                    "status": "Pending",
                }

        except Exception as e:
            logger.error("sagemaker_space_create_failed", space_name=name, error=str(e))
            raise SpaceError(message=f"创建 SageMaker Space 失败: {e}") from e

    async def get_space(self, name: str) -> dict[str, Any] | None:
        """查询 SageMaker Studio Space."""
        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                domain_id = await self._get_domain_id(sm)

                response: dict[str, Any] = await sm.describe_space(
                    DomainId=domain_id,
                    SpaceName=name,
                )

                return {
                    "name": name,
                    "arn": response.get("SpaceArn", ""),
                    "status": response.get("Status", "Unknown"),
                    "instance_type": self._extract_instance_type(response),
                    "studio_url": response.get("Url", ""),
                }

        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFound":
                return None
            logger.error("sagemaker_space_get_failed", space_name=name, error=str(e))
            raise SpaceError(message=f"查询 SageMaker Space 失败: {e}") from e

    async def delete_space(self, name: str) -> None:
        """删除 SageMaker Studio Space."""
        logger.info("sagemaker_space_deleting", space_name=name)

        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                domain_id = await self._get_domain_id(sm)

                await sm.delete_space(
                    DomainId=domain_id,
                    SpaceName=name,
                )

                logger.info("sagemaker_space_deleted", space_name=name)

        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFound":
                logger.warning("sagemaker_space_already_deleted", space_name=name)
                return
            logger.error("sagemaker_space_delete_failed", space_name=name, error=str(e))
            raise SpaceError(message=f"删除 SageMaker Space 失败: {e}") from e

    async def describe_space(self, name: str) -> dict[str, Any] | None:
        """查询 SageMaker Studio Space 的详细状态."""
        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                domain_id = await self._get_domain_id(sm)

                response: dict[str, Any] = await sm.describe_space(
                    DomainId=domain_id,
                    SpaceName=name,
                )

                return {
                    "name": name,
                    "arn": response.get("SpaceArn", ""),
                    "status": response.get("Status", "Unknown"),
                    "instance_type": self._extract_instance_type(response),
                    "studio_url": response.get("Url", ""),
                    "failure_reason": response.get("FailureReason"),
                    "creation_time": response.get("CreationTime"),
                    "last_modified_time": response.get("LastModifiedTime"),
                }

        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFound":
                return None
            logger.error("sagemaker_space_describe_failed", space_name=name, error=str(e))
            raise SpaceError(message=f"查询 SageMaker Space 状态失败: {e}") from e

    async def _get_domain_id(self, sm_client: Any) -> str:
        """获取 SageMaker Studio Domain ID.

        从环境配置获取，若未配置则自动发现第一个可用的 Domain。

        Raises:
            SpaceError: 未找到可用的 SageMaker Domain
        """
        settings = get_settings()
        domain_id = getattr(settings, "sagemaker_domain_id", None)
        if domain_id:
            return domain_id

        # 自动发现 Domain
        response = await sm_client.list_domains(MaxResults=1)
        domains = response.get("Domains", [])
        if not domains:
            raise SpaceError(message="未找到可用的 SageMaker Studio Domain")

        return domains[0]["DomainId"]

    def _extract_instance_type(self, response: dict[str, Any]) -> str:
        """从 Space 响应中提取实例类型."""
        space_settings = response.get("SpaceSettings", {})

        # 尝试 JupyterLab 设置
        jupyter_settings = space_settings.get("JupyterLabAppSettings", {})
        resource_spec = jupyter_settings.get("DefaultResourceSpec", {})
        instance_type = resource_spec.get("InstanceType", "")
        if instance_type:
            return instance_type

        # 尝试 CodeEditor 设置
        code_editor_settings = space_settings.get("CodeEditorAppSettings", {})
        resource_spec = code_editor_settings.get("DefaultResourceSpec", {})
        return resource_spec.get("InstanceType", "Unknown")


@lru_cache(maxsize=1)
def get_sagemaker_spaces_client() -> SageMakerSpacesClient:
    """获取 SageMaker Spaces 客户端单例.

    使用 lru_cache 实现单例模式，避免重复创建 AWS 客户端。
    """
    return SageMakerSpacesClient()
