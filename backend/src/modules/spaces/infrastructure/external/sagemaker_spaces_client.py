"""SageMaker Spaces 客户端实现 (T085).

优先使用 sagemaker-hyperpod SDK Space 模块进行 Space 管理操作。
若 SDK 不支持特定配置 (如自定义存储大小、生命周期脚本) 则使用 aioboto3 调用 SageMaker API。
"""

import asyncio
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
                owner_profile = await self._get_owner_user_profile(sm, domain_id)

                # SageMaker API 要求 OwnershipSettings 与 SpaceSharingSettings 必须成对提供
                response: dict[str, Any] = await sm.create_space(
                    DomainId=domain_id,
                    SpaceName=name,
                    SpaceSettings=space_settings,
                    OwnershipSettings={"OwnerUserProfileName": owner_profile},
                    SpaceSharingSettings={"SharingType": "Private"},
                    SpaceDisplayName=name,
                )

                logger.info(
                    "sagemaker_space_created",
                    space_name=name,
                    space_arn=response.get("SpaceArn"),
                )

                # CreateSpace 异步生效，Space 短暂处于 Creating；
                # 后续 CreateApp 要求 InService，此处等待就绪（通常数秒）
                await self._wait_space_in_service(sm, domain_id, name)

                return {
                    "name": name,
                    "arn": response.get("SpaceArn", ""),
                    "status": "Pending",
                }

        except Exception as e:
            logger.error("sagemaker_space_create_failed", space_name=name, error=str(e))
            raise SpaceError(message=f"创建 SageMaker Space 失败: {e}") from e

    async def _wait_space_in_service(
        self,
        sm_client: Any,
        domain_id: str,
        name: str,
        timeout_seconds: float = 120.0,
        interval_seconds: float = 3.0,
    ) -> None:
        """轮询等待 Space 进入 InService.

        Raises:
            SpaceError: 等待超时或 Space 进入失败状态
        """
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while True:
            response = await sm_client.describe_space(DomainId=domain_id, SpaceName=name)
            status = response.get("Status", "Unknown")
            if status == "InService":
                return
            if status in ("Delete_Failed", "Update_Failed", "Failed"):
                raise SpaceError(message=f"Space {name} 创建失败: {status}")
            if asyncio.get_event_loop().time() >= deadline:
                raise SpaceError(message=f"等待 Space {name} 就绪超时 (当前状态 {status})")
            await asyncio.sleep(interval_seconds)

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

    # Space 内 App 统一命名（SageMaker Studio 约定每个 Space 单 App）
    _APP_NAME = "default"

    # SageMaker Distribution 公共镜像所属账户（us-east-1）。
    # CreateApp 对 JupyterLab/CodeEditor 必须显式提供 SageMakerImageArn。
    _DISTRIBUTION_IMAGE_ACCOUNT = "885854791233"

    @staticmethod
    def _to_app_type(ide_type: str) -> str:
        return "JupyterLab" if ide_type == "jupyterlab" else "CodeEditor"

    def _default_image_arn(self, instance_type: str) -> str:
        """按实例类型选择 SageMaker Distribution CPU/GPU 镜像."""
        is_gpu = instance_type.startswith(("ml.g", "ml.p"))
        variant = "gpu" if is_gpu else "cpu"
        return f"arn:aws:sagemaker:{self._region}:{self._DISTRIBUTION_IMAGE_ACCOUNT}:image/sagemaker-distribution-{variant}"

    async def create_app(
        self,
        space_name: str,
        ide_type: str,
        instance_type: str,
        lifecycle_config_arn: str | None = None,
    ) -> dict[str, Any]:
        """在 Space 内创建 App（真实拉起计算实例）."""
        app_type = self._to_app_type(ide_type)
        resource_spec: dict[str, Any] = {
            "InstanceType": instance_type,
            "SageMakerImageArn": self._default_image_arn(instance_type),
        }
        if lifecycle_config_arn:
            resource_spec["LifecycleConfigArn"] = lifecycle_config_arn

        logger.info(
            "sagemaker_app_creating",
            space_name=space_name,
            app_type=app_type,
            instance_type=instance_type,
        )

        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                domain_id = await self._get_domain_id(sm)
                response: dict[str, Any] = await sm.create_app(
                    DomainId=domain_id,
                    SpaceName=space_name,
                    AppType=app_type,
                    AppName=self._APP_NAME,
                    ResourceSpec=resource_spec,
                )
                logger.info("sagemaker_app_created", space_name=space_name, app_arn=response.get("AppArn"))
                return {"arn": response.get("AppArn", ""), "status": "Pending"}
        except Exception as e:
            logger.error("sagemaker_app_create_failed", space_name=space_name, error=str(e))
            raise SpaceError(message=f"启动 SageMaker App 失败: {e}") from e

    async def delete_app(self, space_name: str, ide_type: str) -> None:
        """删除 Space 内的 App（停止并释放计算实例，EBS 文件保留）."""
        app_type = self._to_app_type(ide_type)
        logger.info("sagemaker_app_deleting", space_name=space_name, app_type=app_type)

        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                domain_id = await self._get_domain_id(sm)
                await sm.delete_app(
                    DomainId=domain_id,
                    SpaceName=space_name,
                    AppType=app_type,
                    AppName=self._APP_NAME,
                )
                logger.info("sagemaker_app_deleted", space_name=space_name)
        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code in ("ResourceNotFound", "ResourceNotFoundException"):
                logger.warning("sagemaker_app_already_deleted", space_name=space_name)
                return
            logger.error("sagemaker_app_delete_failed", space_name=space_name, error=str(e))
            raise SpaceError(message=f"停止 SageMaker App 失败: {e}") from e

    async def describe_app(self, space_name: str, ide_type: str) -> dict[str, Any] | None:
        """查询 Space 内 App（计算实例）的状态."""
        app_type = self._to_app_type(ide_type)

        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                domain_id = await self._get_domain_id(sm)
                response: dict[str, Any] = await sm.describe_app(
                    DomainId=domain_id,
                    SpaceName=space_name,
                    AppType=app_type,
                    AppName=self._APP_NAME,
                )
                return {
                    "arn": response.get("AppArn", ""),
                    "status": response.get("Status", "Unknown"),
                    "failure_reason": response.get("FailureReason"),
                }
        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code in ("ResourceNotFound", "ResourceNotFoundException"):
                return None
            logger.error("sagemaker_app_describe_failed", space_name=space_name, error=str(e))
            raise SpaceError(message=f"查询 SageMaker App 状态失败: {e}") from e

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

    async def _get_owner_user_profile(self, sm_client: Any, domain_id: str) -> str:
        """获取 Space 所属的 User Profile 名称.

        从环境配置获取，若未配置则自动发现 Domain 下第一个 User Profile。

        Raises:
            SpaceError: Domain 下无可用 User Profile
        """
        settings = get_settings()
        profile_name = getattr(settings, "sagemaker_user_profile", None)
        if profile_name:
            return str(profile_name)

        response = await sm_client.list_user_profiles(DomainIdEquals=domain_id, MaxResults=1)
        profiles = response.get("UserProfiles", [])
        if not profiles:
            raise SpaceError(message=f"SageMaker Domain {domain_id} 下未找到可用的 User Profile")

        return str(profiles[0]["UserProfileName"])

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
