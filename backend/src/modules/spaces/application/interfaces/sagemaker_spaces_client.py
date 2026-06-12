"""SageMaker Spaces 客户端接口定义 (T085)."""

from abc import ABC, abstractmethod
from typing import Any


class ISageMakerSpacesClient(ABC):
    """SageMaker Spaces 客户端接口.

    提供 SageMaker Studio Space 的创建、查询、删除和状态管理能力。
    实现类应优先使用 sagemaker-hyperpod SDK Space 模块，
    若 SDK 不支持特定配置则使用 aioboto3 调用 SageMaker API。
    """

    @abstractmethod
    async def create_space(
        self,
        name: str,
        instance_type: str,
        ide_type: str = "jupyterlab",
        lifecycle_config_arn: str | None = None,
        storage_size_gb: int = 10,
    ) -> dict[str, Any]:
        """创建 SageMaker Studio Space.

        Args:
            name: Space 名称 (全局唯一)
            instance_type: 实例类型 (如 ml.g5.xlarge)
            ide_type: IDE 类型 (jupyterlab/vscode)
            lifecycle_config_arn: 生命周期配置 ARN
            storage_size_gb: EFS 存储大小 (GB)

        Returns:
            包含 Space 信息的字典 (name, arn, status 等)

        Raises:
            SpaceError: SageMaker API 调用失败
        """

    @abstractmethod
    async def get_space(self, name: str) -> dict[str, Any] | None:
        """查询 SageMaker Studio Space.

        Args:
            name: Space 名称

        Returns:
            Space 信息字典，不存在时返回 None
        """

    @abstractmethod
    async def delete_space(self, name: str) -> None:
        """删除 SageMaker Studio Space.

        Args:
            name: Space 名称

        Raises:
            SpaceError: SageMaker API 调用失败
        """

    @abstractmethod
    async def describe_space(self, name: str) -> dict[str, Any] | None:
        """查询 SageMaker Studio Space 的详细状态.

        Args:
            name: Space 名称

        Returns:
            包含 Space 状态详情的字典，不存在时返回 None
        """

    @abstractmethod
    async def create_app(
        self,
        space_name: str,
        ide_type: str,
        instance_type: str,
        lifecycle_config_arn: str | None = None,
    ) -> dict[str, Any]:
        """在 Space 内创建 App（真实拉起计算实例）.

        Args:
            space_name: Space 名称
            ide_type: IDE 类型 (jupyterlab/vscode)
            instance_type: 实例类型 (如 ml.g5.xlarge)
            lifecycle_config_arn: 生命周期配置 ARN

        Returns:
            包含 App 信息的字典 (arn, status 等)

        Raises:
            SpaceError: SageMaker API 调用失败
        """

    @abstractmethod
    async def delete_app(self, space_name: str, ide_type: str) -> None:
        """删除 Space 内的 App（停止并释放计算实例，EBS 文件保留）.

        App 不存在时幂等返回，不抛异常。

        Args:
            space_name: Space 名称
            ide_type: IDE 类型 (jupyterlab/vscode)

        Raises:
            SpaceError: SageMaker API 调用失败
        """

    @abstractmethod
    async def describe_app(self, space_name: str, ide_type: str) -> dict[str, Any] | None:
        """查询 Space 内 App（计算实例）的状态.

        Args:
            space_name: Space 名称
            ide_type: IDE 类型 (jupyterlab/vscode)

        Returns:
            包含 App 状态的字典 (status: Pending/InService/Deleting/Deleted/Failed)，
            App 不存在时返回 None
        """
