"""App 级别全局标签管理。

通过 CDK Tags API 为整个 App Scope 下的所有资源
添加 Project、Environment、ManagedBy、CostCenter 标签。
与 utils/tagging.py（资源级别标签）配合使用。

Reference: https://docs.aws.amazon.com/cdk/v2/guide/tagging.html
"""

from typing import TYPE_CHECKING

import aws_cdk as cdk

from constructs import IConstruct

if TYPE_CHECKING:
    from config import EnvironmentConfig

_PROJECT_NAME = "ai-training-platform"
_MANAGED_BY = "cdk"


def _build_app_tags(env_config: "EnvironmentConfig") -> dict[str, str]:
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
    """为 CDK Scope（通常是 App）下所有资源添加全局标签。"""
    for key, value in _build_app_tags(env_config).items():
        cdk.Tags.of(scope).add(key, value)


def get_standard_tags(env_config: "EnvironmentConfig") -> dict[str, str]:
    """获取全局标签字典（用于不继承 CDK 标签系统的资源）。"""
    return _build_app_tags(env_config)


def get_data_classification_tag(
    classification: str = "internal",
) -> dict[str, str]:
    """获取数据分类标签。"""
    return {"DataClassification": classification}
