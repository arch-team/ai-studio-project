"""CloudFormation 输出创建辅助工具。"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

import aws_cdk as cdk

from config import EnvironmentConfig


@runtime_checkable
class HasEnvConfig(Protocol):
    """拥有 env_config 属性的 Stack 协议。"""

    env_config: EnvironmentConfig


def to_kebab_case(name: str) -> str:
    """将 PascalCase/camelCase 转换为 kebab-case。

    正确处理连续大写字母缩写词（EKS, ARN）和混合大小写缩写词（GiB, MBps）。
    """
    # 混合大小写缩写词映射：将其统一为全大写，使正则能正确处理
    _ABBREVIATION_MAP: dict[str, str] = {
        "GiB": "GIB",
        "MBps": "MBPS",
        "MiB": "MIB",
        "KBps": "KBPS",
        "GBps": "GBPS",
        "TiB": "TIB",
    }
    result = name
    for abbr, replacement in _ABBREVIATION_MAP.items():
        result = result.replace(abbr, replacement)

    # 在连续大写字母与小写字母之间插入分隔符 (EKSCluster -> EKS-Cluster)
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", result)
    # 在小写字母/数字与大写字母之间插入分隔符 (clusterEndpoint -> cluster-Endpoint)
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", result)
    return result.lower()


def create_output(
    stack: cdk.Stack,
    output_id: str,
    value: str,
    description: str,
    export_name: str | None = None,
) -> cdk.CfnOutput:
    """创建单个 CloudFormation 输出。

    当未提供 export_name 时，自动从 stack.env_config.resource_prefix
    和 output_id 生成。要求 stack 实现 HasEnvConfig 协议。
    """
    if export_name is None and isinstance(stack, HasEnvConfig):
        suffix = to_kebab_case(output_id)
        export_name = f"{stack.env_config.resource_prefix}-{suffix}"

    return cdk.CfnOutput(
        stack,
        output_id,
        value=value,
        description=description,
        export_name=export_name,
    )
