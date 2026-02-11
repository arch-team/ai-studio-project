"""EKS 相关工具函数。"""

import aws_cdk as cdk
from aws_cdk import aws_eks as eks

from constructs import Construct


def create_eks_addon(
    scope: Construct,
    construct_id: str,
    *,
    addon_name: str,
    cluster_name: str,
    addon_version: str | None = None,
    service_account_role_arn: str | None = None,
    configuration_values: str | None = None,
    tags: list[cdk.CfnTag] | None = None,
) -> eks.CfnAddon:
    """创建 EKS Add-on 的统一工具函数。

    同时支持核心 EKS 插件（EBS CSI, VPC CNI 等）和 HyperPod 插件
    （Training Operator, Task Governance 等）的创建。
    """
    return eks.CfnAddon(
        scope,
        construct_id,
        addon_name=addon_name,
        cluster_name=cluster_name,
        addon_version=addon_version,
        service_account_role_arn=service_account_role_arn,
        configuration_values=configuration_values,
        resolve_conflicts="OVERWRITE",
        tags=tags,
    )
