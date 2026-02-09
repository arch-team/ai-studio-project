"""
Unit tests for PlatformKmsKey Construct.

Tests cover:
- KMS Key 创建和属性
- 自动密钥轮换
- 别名命名
- 环境标签
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from cdk_constructs.kms_key import KmsKeyConfig, PlatformKmsKey
from config import EnvironmentConfig


class TestKmsKeyConfig:
    """Tests for KmsKeyConfig dataclass."""

    def test_default_rotation_enabled(self) -> None:
        """验证默认启用密钥轮换."""
        config = KmsKeyConfig(alias_suffix="s3", description="S3 encryption key")
        assert config.enable_key_rotation is True

    def test_custom_rotation_disabled(self) -> None:
        """验证可禁用密钥轮换."""
        config = KmsKeyConfig(
            alias_suffix="test", description="Test key", enable_key_rotation=False
        )
        assert config.enable_key_rotation is False

    def test_frozen_dataclass(self) -> None:
        """验证配置不可变."""
        config = KmsKeyConfig(alias_suffix="s3", description="Test")
        with pytest.raises(AttributeError):
            config.alias_suffix = "changed"  # type: ignore[misc]


class TestPlatformKmsKey:
    """Tests for PlatformKmsKey Construct."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    def test_creates_kms_key(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证 KMS Key 创建."""
        kms_key = PlatformKmsKey(
            stack,
            "TestKmsKey",
            env_config=dev_config,
            config=KmsKeyConfig(
                alias_suffix="s3",
                description="Test S3 encryption key",
            ),
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::KMS::Key", 1)
        assert kms_key.key is not None

    def test_key_rotation_enabled(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证密钥轮换启用."""
        PlatformKmsKey(
            stack,
            "TestKmsKey",
            env_config=dev_config,
            config=KmsKeyConfig(
                alias_suffix="s3",
                description="Test key",
            ),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::KMS::Key",
            {
                "EnableKeyRotation": True,
            },
        )

    def test_key_alias(self, stack: cdk.Stack, dev_config: EnvironmentConfig) -> None:
        """验证 KMS Key 别名格式正确."""
        PlatformKmsKey(
            stack,
            "TestKmsKey",
            env_config=dev_config,
            config=KmsKeyConfig(
                alias_suffix="rds",
                description="RDS encryption key",
            ),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::KMS::Alias",
            {
                "AliasName": "alias/ai-platform-dev-rds-key",
            },
        )

    def test_key_tags(self, stack: cdk.Stack, dev_config: EnvironmentConfig) -> None:
        """验证 KMS Key 标签."""
        PlatformKmsKey(
            stack,
            "TestKmsKey",
            env_config=dev_config,
            config=KmsKeyConfig(
                alias_suffix="s3",
                description="Test key",
            ),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::KMS::Key",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like({"Key": "Environment", "Value": "dev"}),
                        Match.object_like({"Key": "ManagedBy", "Value": "CDK"}),
                    ]
                ),
            },
        )
