"""Models 模块应用层接口定义

包含:
- ISageMakerClient: SageMaker Model Registry 操作契约 (T038a)
"""

from abc import ABC, abstractmethod
from typing import Any


class ISageMakerClient(ABC):
    """SageMaker API 客户端接口 (T038a)

    封装 SageMaker Model Registry 操作，支持模型包创建、更新和查询。
    """

    @abstractmethod
    async def create_model_package_group(
        self,
        model_package_group_name: str,
        model_package_group_description: str | None = None,
        tags: list[dict[str, str]] | None = None,
    ) -> str:
        """创建模型包组

        Args:
            model_package_group_name: 模型包组名称
            model_package_group_description: 描述
            tags: 标签

        Returns:
            str: 模型包组 ARN
        """
        pass

    @abstractmethod
    async def create_model_package(
        self,
        model_package_group_name: str,
        model_url: str,
        inference_specification: dict[str, Any] | None = None,
        model_metrics: dict[str, Any] | None = None,
        model_approval_status: str = "PendingManualApproval",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """创建模型包

        Args:
            model_package_group_name: 模型包组名称
            model_url: 模型 S3 URI
            inference_specification: 推理规格
            model_metrics: 模型指标
            model_approval_status: 审批状态 (PendingManualApproval, Approved, Rejected)
            metadata: 元数据

        Returns:
            str: 模型包 ARN
        """
        pass

    @abstractmethod
    async def update_model_package(
        self,
        model_package_arn: str,
        model_approval_status: str | None = None,
        approval_description: str | None = None,
    ) -> None:
        """更新模型包状态

        Args:
            model_package_arn: 模型包 ARN
            model_approval_status: 新的审批状态
            approval_description: 审批说明
        """
        pass

    @abstractmethod
    async def describe_model_package(
        self,
        model_package_arn: str,
    ) -> dict[str, Any]:
        """获取模型包详情

        Args:
            model_package_arn: 模型包 ARN

        Returns:
            dict: 模型包详情
        """
        pass

    @abstractmethod
    async def list_model_packages(
        self,
        model_package_group_name: str,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """列出模型包

        Args:
            model_package_group_name: 模型包组名称
            max_results: 最大返回数量

        Returns:
            list: 模型包列表
        """
        pass

    @abstractmethod
    async def delete_model_package(
        self,
        model_package_arn: str,
    ) -> None:
        """删除模型包

        Args:
            model_package_arn: 模型包 ARN
        """
        pass
