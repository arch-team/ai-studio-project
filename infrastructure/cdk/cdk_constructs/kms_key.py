"""KMS Key Construct — 统一密钥创建 (自动轮换、标准标签、环境保护对齐)。"""

from dataclasses import dataclass

import aws_cdk as cdk
from aws_cdk import aws_kms as kms

from config import EnvironmentConfig
from config.constants import TAG_KEYS
from constructs import Construct


@dataclass(frozen=True)
class KmsKeyConfig:
    """KMS Key 配置。"""

    alias_suffix: str
    description: str
    enable_key_rotation: bool = True


class PlatformKmsKey(Construct):
    """统一 KMS Key Construct (密钥轮换 + 环境标签 + 别名命名)。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        config: KmsKeyConfig,
    ) -> None:
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

        cdk.Tags.of(self._key).add(TAG_KEYS.NAME, alias_name)
        cdk.Tags.of(self._key).add(TAG_KEYS.ENVIRONMENT, env_config.name.value)
        cdk.Tags.of(self._key).add(TAG_KEYS.MANAGED_BY, "CDK")

    @property
    def key(self) -> kms.IKey:
        return self._key
