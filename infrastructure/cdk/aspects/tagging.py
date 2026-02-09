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

# 项目级标签常量（与 config/constants.py 中的资源级标签区分）
_PROJECT_NAME = "ai-training-platform"
_MANAGED_BY = "cdk"


def _build_standard_tags(env_config: "EnvironmentConfig") -> dict[str, str]:
    """构建标准标签字典（内部辅助函数）。

    Args:
        env_config: 环境配置

    Returns:
        标准标签键值对字典
    """
    return {
        "Project": _PROJECT_NAME,
        "Environment": env_config.name.value,
        "ManagedBy": _MANAGED_BY,
        "CostCenter": f"ai-platform-{env_config.name.value}",
    }


def apply_standard_tags(
    scope: IConstruct,
    env_config: "EnvironmentConfig",
) -> None:
    """Apply standard tags to all resources in a CDK scope.

    Tags applied: Project, Environment, ManagedBy, CostCenter

    Args:
        scope: CDK scope to apply tags to (usually the App)
        env_config: Environment configuration
    """
    for key, value in _build_standard_tags(env_config).items():
        cdk.Tags.of(scope).add(key, value)


def get_standard_tags(env_config: "EnvironmentConfig") -> dict[str, str]:
    """Get standard tags as a dictionary.

    Useful when you need to pass tags to resources that don't
    inherit from the CDK tagging system.

    Args:
        env_config: Environment configuration

    Returns:
        Dictionary of standard tag key-value pairs
    """
    return _build_standard_tags(env_config)


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
