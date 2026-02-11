"""IAM 辅助函数 — 角色、策略和信任关系的统一创建。"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from config.constants import TAG_KEYS
from constructs import Construct


def _apply_role_configuration(
    role: iam.Role,
    env_config: EnvironmentConfig,
    role_name_suffix: str,
    managed_policies: list[str] | None = None,
    additional_tags: dict[str, str] | None = None,
) -> None:
    """为 IAM 角色应用通用配置 (托管策略 + 标签)。"""
    if managed_policies:
        for policy_name in managed_policies:
            role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(policy_name)
            )

    cdk.Tags.of(role).add(
        TAG_KEYS.NAME, f"{env_config.resource_prefix}-{role_name_suffix}"
    )

    if additional_tags:
        for key, value in additional_tags.items():
            cdk.Tags.of(role).add(key, value)


def create_tagged_role(
    scope: Construct,
    construct_id: str,
    env_config: EnvironmentConfig,
    role_name_suffix: str,
    description: str,
    assumed_by: iam.IPrincipal,
    managed_policies: list[str] | None = None,
    additional_tags: dict[str, str] | None = None,
) -> iam.Role:
    """创建带标准标签的 IAM 角色。"""
    role = iam.Role(
        scope,
        construct_id,
        role_name=f"{env_config.resource_prefix}-{role_name_suffix}",
        description=description,
        assumed_by=assumed_by,
    )

    _apply_role_configuration(
        role, env_config, role_name_suffix, managed_policies, additional_tags
    )

    return role


def create_pod_identity_trust_policy() -> iam.PolicyDocument:
    """创建 EKS Pod Identity 信任策略 (sts:AssumeRole + sts:TagSession)。"""
    return iam.PolicyDocument(
        statements=[
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("pods.eks.amazonaws.com")],
                actions=["sts:AssumeRole", "sts:TagSession"],
            )
        ]
    )


def create_pod_identity_role(
    scope: Construct,
    construct_id: str,
    env_config: EnvironmentConfig,
    role_name_suffix: str,
    description: str,
    managed_policies: list[str] | None = None,
    additional_tags: dict[str, str] | None = None,
) -> iam.Role:
    """创建 EKS Pod Identity IAM 角色。"""
    # 先用占位 principal 创建角色，后续覆盖为完整信任策略
    role = iam.Role(
        scope,
        construct_id,
        role_name=f"{env_config.resource_prefix}-{role_name_suffix}",
        description=description,
        assumed_by=iam.ServicePrincipal("pods.eks.amazonaws.com"),
    )

    # 覆盖为包含 sts:TagSession 的完整信任策略
    cfn_role = role.node.default_child
    if cfn_role is not None:
        cfn_role.assume_role_policy_document = (  # type: ignore[attr-defined]
            create_pod_identity_trust_policy().to_json()
        )

    _apply_role_configuration(
        role, env_config, role_name_suffix, managed_policies, additional_tags
    )

    return role


def add_policy_statement(
    role: iam.Role,
    sid: str,
    actions: list[str],
    resources: list[str],
    conditions: dict[str, Any] | None = None,
    effect: iam.Effect = iam.Effect.ALLOW,
) -> None:
    """为 IAM 角色添加策略声明。"""
    role.add_to_policy(
        iam.PolicyStatement(
            sid=sid,
            effect=effect,
            actions=actions,
            resources=resources,
            conditions=conditions,
        )
    )


def add_policy_statements(
    role: iam.Role,
    statements: list[tuple[str, list[str], list[str]]],
    effect: iam.Effect = iam.Effect.ALLOW,
) -> None:
    """批量添加策略声明 (sid, actions, resources)。"""
    for sid, actions, resources in statements:
        add_policy_statement(role, sid, actions, resources, effect=effect)


def create_irsa_conditions(
    scope: Construct,
    construct_id: str,
    oidc_issuer: str,
    namespace: str,
    service_account: str,
) -> cdk.CfnJson:
    """创建 IRSA 条件 (OIDC audience + subject)。"""
    return cdk.CfnJson(
        scope,
        construct_id,
        value={
            f"{oidc_issuer}:aud": "sts.amazonaws.com",
            f"{oidc_issuer}:sub": f"system:serviceaccount:{namespace}:{service_account}",
        },
    )


def create_irsa_role(
    scope: Construct,
    construct_id: str,
    env_config: EnvironmentConfig,
    oidc_provider_arn: str,
    oidc_issuer: str,
    role_name_suffix: str,
    service_account: str,
    namespace: str = "kube-system",
    description: str = "",
    managed_policies: list[str] | None = None,
) -> iam.Role:
    """创建 IRSA（IAM Roles for Service Accounts）角色。

    统一的 IRSA 角色创建函数，替代 EksStack 中的内联 _create_irsa_role 方法。
    使用 OIDC 联合信任策略，允许 K8s ServiceAccount 承担此角色。

    Args:
        scope: CDK construct scope
        construct_id: Unique identifier for the construct
        env_config: Environment configuration
        oidc_provider_arn: EKS cluster OIDC provider ARN
        oidc_issuer: OIDC issuer URL (without https://)
        role_name_suffix: Suffix for the role name
        service_account: Kubernetes ServiceAccount name
        namespace: Kubernetes namespace (default: kube-system)
        description: Role description
        managed_policies: List of AWS managed policy names to attach

    Returns:
        配置好的 IAM Role
    """
    # 创建 IRSA 条件
    conditions = create_irsa_conditions(
        scope=scope,
        construct_id=f"{construct_id}Conditions",
        oidc_issuer=oidc_issuer,
        namespace=namespace,
        service_account=service_account,
    )

    # 创建角色
    role = iam.Role(
        scope,
        construct_id,
        role_name=f"{env_config.resource_prefix}-{role_name_suffix}",
        assumed_by=iam.FederatedPrincipal(
            oidc_provider_arn,
            conditions={
                "StringEquals": conditions,
            },
            assume_role_action="sts:AssumeRoleWithWebIdentity",
        ),
        description=description,
    )

    # 附加托管策略
    _apply_role_configuration(role, env_config, role_name_suffix, managed_policies)

    return role
