"""资源级别标签工具函数。

为单个 AWS 资源添加 Name、Environment、Component 等标签。
与 aspects/tagging.py（App 级别全局标签）配合使用。
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
    tags: dict[str, str] = {
        TAG_KEYS.NAME: f"{env_config.resource_prefix}-{resource_name}",
        TAG_KEYS.MANAGED_BY: "cdk",
    }

    if component:
        tags[TAG_KEYS.COMPONENT] = component

    if additional_tags:
        tags.update(additional_tags)

    return tags


def apply_resource_tags(
    resource: Construct,
    env_config: EnvironmentConfig,
    resource_name: str,
    additional_tags: dict[str, str] | None = None,
) -> None:
    """为单个资源添加 Name + Environment + ManagedBy 标签。"""
    tags = _build_tags_dict(env_config, resource_name, additional_tags=additional_tags)
    tags[TAG_KEYS.ENVIRONMENT] = env_config.name.value

    for key, value in tags.items():
        cdk.Tags.of(resource).add(key, value)


# 向后兼容别名
apply_standard_tags = apply_resource_tags


def apply_component_tag(
    resource: Construct,
    component: str,
) -> None:
    """为资源添加 Component 标签。"""
    cdk.Tags.of(resource).add(TAG_KEYS.COMPONENT, component)


def _dict_to_cfn_tags(tags: dict[str, str]) -> list[cdk.CfnTag]:
    return [cdk.CfnTag(key=key, value=value) for key, value in tags.items()]


def create_cfn_tags(
    env_config: EnvironmentConfig,
    resource_name: str,
    additional_tags: dict[str, str] | None = None,
) -> list[cdk.CfnTag]:
    """为 L1 Construct (CfnCluster 等) 创建 CfnTag 列表。"""
    tags = _build_tags_dict(env_config, resource_name, additional_tags=additional_tags)
    tags[TAG_KEYS.ENVIRONMENT] = env_config.name.value
    return _dict_to_cfn_tags(tags)


def create_addon_tags(
    env_config: EnvironmentConfig,
    addon_name: str,
    component: str,
) -> list[cdk.CfnTag]:
    """为 EKS Add-on 创建 CfnTag 列表。"""
    tags = _build_tags_dict(env_config, addon_name, component=component)
    return _dict_to_cfn_tags(tags)
