"""
集中 KMS Key Construct for AI Training Platform.

提供统一的 KMS Key 创建逻辑:
- 自动密钥轮换 (enable_key_rotation)
- 环境标签 + 标准别名命名
- 删除策略与环境保护配置对齐
"""

from dataclasses import dataclass

import aws_cdk as cdk
from aws_cdk import aws_kms as kms

from config import EnvironmentConfig
from constructs import Construct


@dataclass(frozen=True)
class KmsKeyConfig:
    """KMS Key 配置.

    Attributes:
        alias_suffix: Key 别名后缀 (如 "s3", "rds", "ebs")
        description: Key 描述
        enable_key_rotation: 是否启用自动轮换 (默认 True)
    """

    alias_suffix: str
    description: str
    enable_key_rotation: bool = True


class PlatformKmsKey(Construct):
    """统一的 KMS Key Construct.

    自动配置:
    - 密钥轮换 (默认启用)
    - 环境标签 (Name, Environment)
    - 标准别名命名: alias/{resource_prefix}-{suffix}-key
    - RemovalPolicy 与 ProtectionConfig 对齐

    Attributes:
        key: KMS Key 实例
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        config: KmsKeyConfig,
    ) -> None:
        """Initialize PlatformKmsKey.

        Args:
            scope: CDK construct scope
            construct_id: Construct identifier
            env_config: Environment configuration
            config: KMS Key configuration
        """
        super().__init__(scope, construct_id)

        alias_name = f"alias/{env_config.resource_prefix}-{config.alias_suffix}-key"

        self._key = kms.Key(
            self,
            "Key",
            alias=alias_name,
            description=config.description,
            enable_key_rotation=config.enable_key_rotation,
            removal_policy=env_config.protection.removal_policy,
        )

        cdk.Tags.of(self._key).add("Name", alias_name)
        cdk.Tags.of(self._key).add("Environment", env_config.name.value)
        cdk.Tags.of(self._key).add("ManagedBy", "CDK")

    @property
    def key(self) -> kms.IKey:
        """Get the KMS Key."""
        return self._key
