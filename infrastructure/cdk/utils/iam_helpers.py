"""
IAM helper functions for AI Training Platform CDK.

This module provides reusable functions for creating IAM roles,
policies, and trust relationships to reduce code duplication.
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct


def _apply_role_configuration(
    role: iam.Role,
    env_config: EnvironmentConfig,
    role_name_suffix: str,
    managed_policies: list[str] | None = None,
    additional_tags: dict[str, str] | None = None,
) -> None:
    """Apply common configuration to an IAM role (internal helper).

    Args:
        role: The IAM role to configure
        env_config: Environment configuration
        role_name_suffix: Suffix for the role name (used in tags)
        managed_policies: List of AWS managed policy names to attach
        additional_tags: Additional tags to apply
    """
    # Attach managed policies
    if managed_policies:
        for policy_name in managed_policies:
            role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(policy_name)
            )

    # Apply standard tags
    cdk.Tags.of(role).add("Name", f"{env_config.resource_prefix}-{role_name_suffix}")

    # Apply additional tags
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
    """Create an IAM role with standard tags.

    Args:
        scope: CDK construct scope
        construct_id: Unique identifier for the construct
        env_config: Environment configuration
        role_name_suffix: Suffix for the role name (will be prefixed with resource_prefix)
        description: Role description
        assumed_by: Principal that can assume this role
        managed_policies: List of AWS managed policy names to attach
        additional_tags: Additional tags to apply

    Returns:
        The created IAM Role
    """
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
    """Create trust policy for EKS Pod Identity.

    EKS Pod Identity requires both sts:AssumeRole and sts:TagSession actions.

    Returns:
        PolicyDocument suitable for EKS Pod Identity
    """
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
    """Create an IAM role for EKS Pod Identity.

    This creates a role with the proper trust policy for EKS Pod Identity,
    including both sts:AssumeRole and sts:TagSession actions.

    Args:
        scope: CDK construct scope
        construct_id: Unique identifier for the construct
        env_config: Environment configuration
        role_name_suffix: Suffix for the role name
        description: Role description
        managed_policies: List of AWS managed policy names to attach
        additional_tags: Additional tags to apply

    Returns:
        The created IAM Role configured for Pod Identity
    """
    # Create role with placeholder principal (will be overridden)
    role = iam.Role(
        scope,
        construct_id,
        role_name=f"{env_config.resource_prefix}-{role_name_suffix}",
        description=description,
        assumed_by=iam.ServicePrincipal("pods.eks.amazonaws.com"),
    )

    # Override with proper trust policy including sts:TagSession
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
    """Add a policy statement to an IAM role.

    Args:
        role: The IAM role to add the statement to
        sid: Statement identifier
        actions: List of IAM actions
        resources: List of resource ARNs
        conditions: Optional conditions for the statement
        effect: Allow or Deny (default: Allow)
    """
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
    """Add multiple policy statements to an IAM role.

    Args:
        role: The IAM role to add the statements to
        statements: List of tuples (sid, actions, resources)
        effect: Allow or Deny for all statements (default: Allow)
    """
    for sid, actions, resources in statements:
        add_policy_statement(role, sid, actions, resources, effect=effect)


def create_irsa_conditions(
    scope: Construct,
    construct_id: str,
    oidc_issuer: str,
    namespace: str,
    service_account: str,
) -> cdk.CfnJson:
    """Create IRSA (IAM Roles for Service Accounts) conditions.

    Args:
        scope: CDK construct scope
        construct_id: Unique identifier for the construct
        oidc_issuer: OIDC issuer URL (without https://)
        namespace: Kubernetes namespace
        service_account: Kubernetes ServiceAccount name

    Returns:
        CfnJson containing the IRSA conditions
    """
    return cdk.CfnJson(
        scope,
        construct_id,
        value={
            f"{oidc_issuer}:aud": "sts.amazonaws.com",
            f"{oidc_issuer}:sub": f"system:serviceaccount:{namespace}:{service_account}",
        },
    )
