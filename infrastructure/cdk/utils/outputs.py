"""
CloudFormation 输出创建辅助工具。

此模块提供便捷的方法来创建 CloudFormation 输出。
"""

import re

import aws_cdk as cdk


def to_kebab_case(name: str) -> str:
    """将 PascalCase/camelCase 转换为 kebab-case。

    正确处理连续大写字母（缩写词），例如 "EKS" 保持为 "eks"。
    混合大小写缩写词（如 GiB, MBps）通过预处理映射表统一为全大写后再转换。

    Args:
        name: 输入名称 (如 "ClusterEndpoint", "vpcId")

    Returns:
        转换后的 kebab-case 字符串

    Example:
        ```python
        to_kebab_case("ClusterEndpoint")    # "cluster-endpoint"
        to_kebab_case("vpcId")              # "vpc-id"
        to_kebab_case("EKSClusterARN")      # "eks-cluster-arn"
        to_kebab_case("StorageCapacityGiB") # "storage-capacity-gib"
        to_kebab_case("TotalThroughputMBps") # "total-throughput-mbps"
        ```
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

    Args:
        stack: CDK Stack 实例
        output_id: 输出 ID
        value: 输出值
        description: 输出描述
        export_name: 导出名称（可选，默认根据 output_id 生成）

    Returns:
        创建的 CfnOutput 实例

    Example:
        ```python
        create_output(
            self,
            "ClusterEndpoint",
            cluster.cluster_endpoint.hostname,
            "Aurora cluster writer endpoint",
        )
        ```
    """
    # 如果没有提供 export_name，根据 output_id 生成
    if export_name is None:
        # 从 Stack 获取 resource_prefix
        env_config = getattr(stack, "env_config", None)
        if env_config:
            resource_prefix = env_config.resource_prefix
            suffix = to_kebab_case(output_id)
            export_name = f"{resource_prefix}-{suffix}"

    return cdk.CfnOutput(
        stack,
        output_id,
        value=value,
        description=description,
        export_name=export_name,
    )
