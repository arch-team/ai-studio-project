"""
Tagging helper functions for AI Training Platform CDK.

This module provides reusable functions for applying standard tags
to AWS resources to ensure consistency across the infrastructure.
"""

import aws_cdk as cdk
from constructs import Construct

from config import EnvironmentConfig
from config.constants import TAG_KEYS


def apply_standard_tags(
    resource: Construct,
    env_config: EnvironmentConfig,
    resource_name: str,
    additional_tags: dict[str, str] | None = None,
) -> None:
    """Apply standard tags to a CDK resource.

    Standard tags include:
    - Name: {resource_prefix}-{resource_name}
    - Environment: dev/staging/prod
    - ManagedBy: cdk

    Args:
        resource: The CDK construct to tag
        env_config: Environment configuration
        resource_name: Name suffix for the resource
        additional_tags: Additional tags to apply
    """
    tags = {
        TAG_KEYS.NAME: f"{env_config.resource_prefix}-{resource_name}",
        TAG_KEYS.ENVIRONMENT: env_config.name.value,
        TAG_KEYS.MANAGED_BY: "cdk",
    }

    if additional_tags:
        tags.update(additional_tags)

    for key, value in tags.items():
        cdk.Tags.of(resource).add(key, value)


def apply_component_tag(
    resource: Construct,
    component: str,
) -> None:
    """Apply component tag to a CDK resource.

    Args:
        resource: The CDK construct to tag
        component: Component name (e.g., 'training-operator', 'observability')
    """
    cdk.Tags.of(resource).add(TAG_KEYS.COMPONENT, component)


def create_cfn_tags(
    env_config: EnvironmentConfig,
    resource_name: str,
    additional_tags: dict[str, str] | None = None,
) -> list[cdk.CfnTag]:
    """Create a list of CfnTags for L1 constructs.

    Useful for resources like CfnCluster that require CfnTag objects.

    Args:
        env_config: Environment configuration
        resource_name: Name suffix for the resource
        additional_tags: Additional tags to apply

    Returns:
        List of CfnTag objects
    """
    tags = [
        cdk.CfnTag(key=TAG_KEYS.NAME, value=f"{env_config.resource_prefix}-{resource_name}"),
        cdk.CfnTag(key=TAG_KEYS.ENVIRONMENT, value=env_config.name.value),
        cdk.CfnTag(key=TAG_KEYS.MANAGED_BY, value="cdk"),
    ]

    if additional_tags:
        for key, value in additional_tags.items():
            tags.append(cdk.CfnTag(key=key, value=value))

    return tags


def create_addon_tags(
    env_config: EnvironmentConfig,
    addon_name: str,
    component: str,
) -> list[cdk.CfnTag]:
    """Create tags for EKS Add-on resources.

    Args:
        env_config: Environment configuration
        addon_name: Short name for the add-on (e.g., 'training-operator')
        component: Component name for categorization

    Returns:
        List of CfnTag objects for the add-on
    """
    return [
        cdk.CfnTag(key=TAG_KEYS.NAME, value=f"{env_config.resource_prefix}-{addon_name}"),
        cdk.CfnTag(key=TAG_KEYS.COMPONENT, value=component),
        cdk.CfnTag(key=TAG_KEYS.MANAGED_BY, value="cdk"),
    ]
