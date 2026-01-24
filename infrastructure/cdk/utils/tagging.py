"""
Tagging helper functions for AI Training Platform CDK.

This module provides reusable functions for applying standard tags
to AWS resources to ensure consistency across the infrastructure.
"""

import aws_cdk as cdk

from config import EnvironmentConfig
from config.constants import TAG_KEYS
from constructs import Construct


def _build_tags_dict(
    env_config: EnvironmentConfig,
    resource_name: str,
    component: str | None = None,
    additional_tags: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build a dictionary of tags for AWS resources (internal helper).

    Args:
        env_config: Environment configuration
        resource_name: Name suffix for the resource
        component: Optional component name for categorization
        additional_tags: Additional tags to apply

    Returns:
        Dictionary of tag key-value pairs
    """
    tags = {
        TAG_KEYS.NAME: f"{env_config.resource_prefix}-{resource_name}",
        TAG_KEYS.MANAGED_BY: "cdk",
    }

    if component:
        tags[TAG_KEYS.COMPONENT] = component

    if additional_tags:
        tags.update(additional_tags)

    return tags


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
    tags = _build_tags_dict(env_config, resource_name, additional_tags=additional_tags)
    tags[TAG_KEYS.ENVIRONMENT] = env_config.name.value

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


def _dict_to_cfn_tags(tags: dict[str, str]) -> list[cdk.CfnTag]:
    """Convert a dictionary of tags to a list of CfnTag objects.

    Args:
        tags: Dictionary of tag key-value pairs

    Returns:
        List of CfnTag objects
    """
    return [cdk.CfnTag(key=key, value=value) for key, value in tags.items()]


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
    tags = _build_tags_dict(env_config, resource_name, additional_tags=additional_tags)
    tags[TAG_KEYS.ENVIRONMENT] = env_config.name.value
    return _dict_to_cfn_tags(tags)


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
    tags = _build_tags_dict(env_config, addon_name, component=component)
    return _dict_to_cfn_tags(tags)
