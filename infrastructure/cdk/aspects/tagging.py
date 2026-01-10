"""
Tagging utilities for AI Training Platform CDK Stacks.

This module provides centralized tag management for all CDK resources.
Tags are essential for:
- Cost allocation and tracking
- Resource organization and filtering
- Compliance and governance
- Operational management

Reference: https://docs.aws.amazon.com/cdk/v2/guide/tagging.html
"""

from typing import TYPE_CHECKING

import aws_cdk as cdk

from constructs import IConstruct

if TYPE_CHECKING:
    from config import EnvironmentConfig


def apply_standard_tags(
    scope: IConstruct,
    env_config: "EnvironmentConfig",
) -> None:
    """Apply standard tags to all resources in a CDK scope.

    This function applies mandatory tags that should be present on all
    resources for cost tracking, compliance, and operational management.

    Tags applied:
    - Project: ai-training-platform
    - Environment: dev/staging/prod
    - ManagedBy: cdk
    - CostCenter: ai-platform-{environment}

    Args:
        scope: CDK scope to apply tags to (usually the App)
        env_config: Environment configuration

    Example:
        ```python
        app = cdk.App()
        apply_standard_tags(app, env_config)
        ```
    """
    # Standard tags for all resources
    standard_tags = {
        "Project": "ai-training-platform",
        "Environment": env_config.name.value,
        "ManagedBy": "cdk",
        "CostCenter": f"ai-platform-{env_config.name.value}",
    }

    # Apply tags to all resources in scope
    for key, value in standard_tags.items():
        cdk.Tags.of(scope).add(key, value)


def get_standard_tags(env_config: "EnvironmentConfig") -> dict[str, str]:
    """Get standard tags as a dictionary.

    Useful when you need to pass tags to resources that don't
    inherit from the CDK tagging system.

    Args:
        env_config: Environment configuration

    Returns:
        Dictionary of standard tag key-value pairs

    Example:
        ```python
        tags = get_standard_tags(env_config)
        # Use with CloudFormation native resources
        cfn_resource.tags = [CfnTag(key=k, value=v) for k, v in tags.items()]
        ```
    """
    return {
        "Project": "ai-training-platform",
        "Environment": env_config.name.value,
        "ManagedBy": "cdk",
        "CostCenter": f"ai-platform-{env_config.name.value}",
    }


def get_data_classification_tag(
    classification: str = "internal",
) -> dict[str, str]:
    """Get data classification tag.

    Args:
        classification: Data classification level
            Options: 'public', 'internal', 'confidential', 'restricted'

    Returns:
        Dictionary with DataClassification tag
    """
    return {"DataClassification": classification}
