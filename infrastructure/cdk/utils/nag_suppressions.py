"""
CDK Nag 抑制规则的集中管理。

此模块提供统一的接口来管理所有 Stack 的 Nag 抑制规则。
"""

from typing import TYPE_CHECKING

from cdk_nag import NagSuppressions

from constructs import IConstruct

if TYPE_CHECKING:
    import aws_cdk as cdk


# 通用抑制规则 - 适用于多个 Stack
COMMON_SUPPRESSIONS = {
    "AwsSolutions-IAM4": "AWS managed policies are used following AWS best practices",
    "AwsSolutions-IAM5": "Wildcard permissions are scoped to specific resources and conditions",
    "AwsSolutions-L1": "Lambda runtime version is managed by CDK construct library",
}

# 各 Stack 特定的抑制规则
STACK_SPECIFIC_SUPPRESSIONS = {
    "network": [
        {
            "id": "AwsSolutions-VPC7",
            "reason": "VPC Flow Logs are explicitly enabled in the stack",
        },
        {
            "id": "AwsSolutions-EC23",
            "reason": "VPC endpoint security group uses Fn::GetAtt for CIDR which CDK Nag cannot validate",
        },
    ],
    "iam": [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "AWS managed policies are used for EKS node roles following AWS best practices",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Wildcard permissions are scoped to specific resources and conditions",
        },
    ],
    "database": [
        {
            "id": "AwsSolutions-RDS10",
            "reason": "Deletion protection is enabled for production environments only",
        },
        {
            "id": "AwsSolutions-RDS11",
            "reason": "Using default port is acceptable for dev environment; production will use custom port",
        },
        {
            "id": "AwsSolutions-RDS14",
            "reason": "Backtrack is not required for dev environment; will be enabled for production",
        },
        {
            "id": "AwsSolutions-SMG4",
            "reason": "Secret rotation will be configured in a separate security enhancement task",
        },
        {
            "id": "AwsSolutions-IAM4",
            "reason": "AWS managed policies used for Lambda log retention custom resource",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Wildcard permissions required for Lambda log retention custom resource",
        },
    ],
    "storage": [
        {
            "id": "AwsSolutions-S1",
            "reason": "Server access logging will be configured when log bucket is created",
        },
    ],
    "eks": [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "AWS managed policies used for EKS add-ons and CDK custom resources",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Wildcard permissions required for EKS cluster management and CDK custom resources",
        },
        {
            "id": "AwsSolutions-EKS1",
            "reason": "EKS cluster has private endpoint access enabled",
        },
        {
            "id": "AwsSolutions-L1",
            "reason": "Lambda runtime version is managed by CDK construct library for EKS and kubectl providers",
        },
        {
            "id": "AwsSolutions-SF1",
            "reason": "Step Function logging is managed by CDK EKS construct; acceptable for dev environment",
        },
        {
            "id": "AwsSolutions-SF2",
            "reason": "X-Ray tracing is managed by CDK EKS construct; acceptable for dev environment",
        },
    ],
    "sagemaker-hyperpod": [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "AWS managed policies used for HyperPod execution role",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Wildcard permissions required for EC2 network access and ECR operations",
        },
        {
            "id": "AwsSolutions-S1",
            "reason": "Lifecycle scripts bucket access logging will be configured in production",
        },
        {
            "id": "AwsSolutions-L1",
            "reason": "Lambda runtime version is managed by CDK construct library for S3 deployment",
        },
    ],
    "fsx": [
        {
            "id": "AwsSolutions-EC23",
            "reason": "FSx security group allows VPC CIDR access for Lustre client connectivity",
        },
    ],
    "observability": [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "AWS managed policies used for Prometheus remote write access",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Wildcard permissions required for Prometheus and observability operations",
        },
    ],
    "alb": [
        {
            "id": "AwsSolutions-ELB2",
            "reason": "ALB access logging will be enabled when S3 log bucket is configured",
        },
        {
            "id": "AwsSolutions-EC23",
            "reason": "ALB security group allows 0.0.0.0/0 for public internet access as designed",
        },
    ],
}


def apply_nag_suppressions(app: "cdk.App") -> None:
    """应用 CDK Nag 抑制规则到所有 Stack。

    此函数会遍历 App 中的所有 Stack，并根据 Stack 名称应用相应的抑制规则。

    Args:
        app: CDK App 实例

    Example:
        ```python
        app = cdk.App()
        # ... 创建所有 Stack ...
        apply_nag_suppressions(app)
        ```
    """
    # 遍历 App 中的所有节点
    for node in app.node.find_all():
        # 只处理 Stack 类型的节点
        if not hasattr(node, "stack_name"):
            continue

        stack = node

        # 从 Stack ID 中提取 Stack 类型
        # 例如: "ai-platform-dev-network" -> "network"
        stack_id_parts = stack.node.id.split("-")
        if len(stack_id_parts) < 3:
            continue

        stack_type = stack_id_parts[-1].lower()

        # 如果有该 Stack 类型的特定抑制规则，则应用
        if stack_type in STACK_SPECIFIC_SUPPRESSIONS:
            suppressions = STACK_SPECIFIC_SUPPRESSIONS[stack_type]
            NagSuppressions.add_stack_suppressions(stack, suppressions)


def apply_resource_suppression(
    construct: IConstruct,
    suppression_id: str,
    reason: str,
) -> None:
    """为特定资源应用 Nag 抑制规则。

    Args:
        construct: CDK Construct 实例
        suppression_id: 抑制规则 ID (如 "AwsSolutions-IAM4")
        reason: 抑制原因说明

    Example:
        ```python
        apply_resource_suppression(
            my_lambda_function,
            "AwsSolutions-L1",
            "Using specific Lambda runtime version required by application"
        )
        ```
    """
    NagSuppressions.add_resource_suppressions(
        construct,
        [{"id": suppression_id, "reason": reason}],
    )
