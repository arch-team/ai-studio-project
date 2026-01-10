"""
CloudFormation 输出创建辅助工具。

此模块提供便捷的方法来创建 CloudFormation 输出。
"""

import aws_cdk as cdk


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
            # 将 output_id 转换为 kebab-case
            suffix = "".join(
                ["-" + c.lower() if c.isupper() else c for c in output_id]
            ).lstrip("-")
            export_name = f"{resource_prefix}-{suffix}"

    return cdk.CfnOutput(
        stack,
        output_id,
        value=value,
        description=description,
        export_name=export_name,
    )


def create_outputs_batch(
    stack: cdk.Stack,
    outputs: list[tuple[str, str, str]],
    export_prefix: str | None = None,
) -> list[cdk.CfnOutput]:
    """批量创建 CloudFormation 输出。

    Args:
        stack: CDK Stack 实例
        outputs: 输出列表，每项为 (output_id, value, description)
        export_prefix: 导出名称前缀（可选，默认使用 stack.env_config.resource_prefix）

    Returns:
        创建的 CfnOutput 实例列表

    Example:
        ```python
        create_outputs_batch(
            self,
            [
                ("ClusterName", self._cluster.cluster_name, "EKS cluster name"),
                ("ClusterArn", self._cluster.cluster_arn, "EKS cluster ARN"),
            ]
        )
        ```
    """
    # 获取 resource_prefix
    if export_prefix is None:
        env_config = getattr(stack, "env_config", None)
        if env_config:
            export_prefix = env_config.resource_prefix

    created_outputs = []
    for output_id, value, description in outputs:
        # 将 output_id 转换为 kebab-case 作为 export 后缀
        suffix = "".join(
            ["-" + c.lower() if c.isupper() else c for c in output_id]
        ).lstrip("-")

        export_name = f"{export_prefix}-{suffix}" if export_prefix else None

        output = cdk.CfnOutput(
            stack,
            output_id,
            value=value,
            description=description,
            export_name=export_name,
        )
        created_outputs.append(output)

    return created_outputs
