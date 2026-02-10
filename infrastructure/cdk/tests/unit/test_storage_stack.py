"""
Unit tests for Storage Stack.

Tests cover:
- S3 bucket creation (datasets, models, checkpoints)
- Encryption configuration (SSE-S3)
- Versioning enabled
- Public access blocked
- SSL enforcement
- Lifecycle policies
- Removal policies per environment

T038b-2 测试用例:
- S3 生命周期规则验证 (Standard-IA 转换、自动删除、分片上传清理)
- 冷检查点标签过滤 (checkpoint_type=cold)
- CDK 参数化配置验证

参考: spec.md FR-011 S3 生命周期策略要求
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_kms as kms
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import StorageStack


class TestStorageStackCreation:
    """Tests for Storage Stack creation."""

    @pytest.fixture
    def storage_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> StorageStack:
        """Create a Storage Stack for testing."""
        return StorageStack(
            cdk_app,
            "TestStorageStack",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, storage_stack: StorageStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(storage_stack)

    def test_stack_synthesizes(self, storage_stack: StorageStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert storage_stack is not None

    def test_three_buckets_created(self, template: Template) -> None:
        """Verify all three buckets are created."""
        template.resource_count_is("AWS::S3::Bucket", 3)


class TestBucketSecurity:
    """Tests for S3 bucket security configuration."""

    @pytest.fixture
    def template(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> Template:
        """Create template for security testing."""
        stack = StorageStack(
            cdk_app,
            "SecurityTestStack",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_public_access_blocked(self, template: Template) -> None:
        """Verify all buckets have public access blocked."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                },
            },
        )

    def test_versioning_enabled(self, template: Template) -> None:
        """Verify buckets have versioning enabled."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "VersioningConfiguration": {"Status": "Enabled"},
            },
        )

    def test_bucket_ownership_enforced(self, template: Template) -> None:
        """Verify bucket ownership is enforced."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "OwnershipControls": {
                    "Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]
                },
            },
        )


class TestRemovalPolicies:
    """Tests for removal policies per environment."""

    def test_dev_buckets_destroyable(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> None:
        """Verify dev buckets can be destroyed."""
        stack = StorageStack(
            cdk_app,
            "DevRemovalStack",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        template = Template.from_stack(stack)

        # Dev buckets should have DeletionPolicy: Delete
        template.has_resource(
            "AWS::S3::Bucket",
            {
                "DeletionPolicy": "Delete",
                "UpdateReplacePolicy": "Delete",
            },
        )

    def test_prod_buckets_retained(
        self,
        cdk_app: cdk.App,
        prod_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> None:
        """Verify prod buckets are retained on deletion."""
        stack = StorageStack(
            cdk_app,
            "ProdRemovalStack",
            env_config=prod_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        template = Template.from_stack(stack)

        # Prod buckets should have DeletionPolicy: Retain
        template.has_resource(
            "AWS::S3::Bucket",
            {
                "DeletionPolicy": "Retain",
                "UpdateReplacePolicy": "Retain",
            },
        )


class TestLifecyclePolicies:
    """Tests for S3 lifecycle policies."""

    @pytest.fixture
    def template(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> Template:
        """Create template for lifecycle testing."""
        stack = StorageStack(
            cdk_app,
            "LifecycleTestStack",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_checkpoints_bucket_has_lifecycle(self, template: Template) -> None:
        """Verify checkpoints bucket has lifecycle rules."""
        # At least one bucket should have lifecycle configuration
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": Match.object_like(
                    {"Rules": Match.any_value()}
                ),
            },
        )


class TestStorageStackOutputs:
    """Tests for Storage Stack outputs."""

    @pytest.fixture
    def storage_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> StorageStack:
        """Create Storage Stack for output testing."""
        return StorageStack(
            cdk_app,
            "OutputTestStack",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )

    def test_datasets_bucket_accessible(self, storage_stack: StorageStack) -> None:
        """Verify datasets bucket is accessible."""
        assert storage_stack.datasets_bucket is not None

    def test_models_bucket_accessible(self, storage_stack: StorageStack) -> None:
        """Verify models bucket is accessible."""
        assert storage_stack.models_bucket is not None

    def test_checkpoints_bucket_accessible(self, storage_stack: StorageStack) -> None:
        """Verify checkpoints bucket is accessible."""
        assert storage_stack.checkpoints_bucket is not None


class TestBucketTags:
    """Tests for bucket tagging."""

    @pytest.fixture
    def template(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> Template:
        """Create template for tag testing."""
        stack = StorageStack(
            cdk_app,
            "TagTestStack",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_buckets_have_name_tag(self, template: Template) -> None:
        """Verify buckets have Name tag."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with([Match.object_like({"Key": "Name"})]),
            },
        )

    def test_buckets_have_data_classification_tag(self, template: Template) -> None:
        """Verify buckets have DataClassification tag."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "DataClassification", "Value": "internal"}
                        )
                    ]
                ),
            },
        )


# =============================================================================
# T038b-2: Checkpoint S3 Lifecycle Policy 测试
# =============================================================================


class TestCheckpointLifecyclePolicies:
    """T038b-2: 检查点 S3 生命周期策略测试.

    验证 FR-011 S3 生命周期策略要求:
    - 30 天后转换到 Standard-IA (成本节省 ~50%)
    - 90 天后自动删除冷检查点 (可配置)
    - 3 天后中止未完成的分段上传
    - 仅对冷检查点应用规则 (checkpoint_type=cold 标签过滤)
    """

    @pytest.fixture
    def storage_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> StorageStack:
        """Create Storage Stack for lifecycle testing."""
        return StorageStack(
            cdk_app,
            "CheckpointLifecycleStack",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, storage_stack: StorageStack) -> Template:
        """Get CloudFormation template."""
        return Template.from_stack(storage_stack)

    def test_s3_lifecycle_transition_to_ia_after_30_days(
        self, template: Template, dev_config: EnvironmentConfig
    ) -> None:
        """验证 30 天后转换到 S3 Standard-IA.

        FR-011 要求: 对象创建 30 天后自动转换为 Standard-IA (低频访问).
        成本优化: Standard-IA 比 Standard 节省约 50% 存储成本.
        """
        # 验证存在 Standard-IA 转换规则
        expected_days = dev_config.storage.checkpoint_ia_transition_days

        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Status": "Enabled",
                                    "Transitions": Match.array_with(
                                        [
                                            Match.object_like(
                                                {
                                                    "StorageClass": "STANDARD_IA",
                                                    "TransitionInDays": expected_days,
                                                }
                                            )
                                        ]
                                    ),
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_s3_lifecycle_delete_after_retention_days(
        self, template: Template, dev_config: EnvironmentConfig
    ) -> None:
        """验证保留期后自动删除冷检查点.

        FR-011 要求: 对象创建 N 天后自动删除 (默认 90 天).
        合规性说明: 90 天保留期满足审计要求和模型回滚需求.
        """
        expected_days = dev_config.storage.checkpoint_retention_days

        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Status": "Enabled",
                                    "ExpirationInDays": expected_days,
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_s3_lifecycle_abort_incomplete_multipart_upload(
        self, template: Template
    ) -> None:
        """验证 3 天后中止未完成的分段上传.

        检查点频繁写入场景下，未完成的分片上传会占用存储空间.
        3 天清理周期在检查点场景下是合理的折衷.
        """
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Status": "Enabled",
                                    "AbortIncompleteMultipartUpload": {
                                        "DaysAfterInitiation": 3
                                    },
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_s3_lifecycle_noncurrent_version_expiration(
        self, template: Template
    ) -> None:
        """验证 7 天后删除旧版本.

        检查点可替换，旧版本保留 7 天足够进行故障恢复.
        """
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Status": "Enabled",
                                    "NoncurrentVersionExpiration": {
                                        "NoncurrentDays": 7
                                    },
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_s3_lifecycle_filter_by_cold_checkpoint_prefix(
        self, template: Template
    ) -> None:
        """验证仅对冷检查点应用生命周期规则.

        T038b-2 要求: 仅对标签为 checkpoint_type=cold 或前缀为 cold/ 的对象
        应用生命周期规则，避免误删热/温检查点.

        当前实现: 使用 cold/ 前缀过滤 (S3 生命周期规则原生支持).
        """
        # 验证过期规则带有 cold/ 前缀过滤
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Status": "Enabled",
                                    "ExpirationInDays": Match.any_value(),
                                    "Prefix": "cold/",
                                }
                            )
                        ]
                    )
                }
            },
        )


class TestCheckpointLifecycleParameterization:
    """T038b-2: CDK 参数化配置测试.

    验证检查点生命周期规则可通过 CDK 配置参数调整.
    """

    def test_custom_retention_days(
        self,
        cdk_app: cdk.App,
        test_account: str,
        test_region: str,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> None:
        """验证可自定义冷检查点保留天数.

        CDK 参数: checkpoint_retention_days (默认 90)
        """
        from dataclasses import replace

        from config import EnvironmentConfig

        # 创建自定义保留期配置 (180 天)
        base_config = EnvironmentConfig.for_dev(
            account=test_account, region=test_region
        )
        custom_storage = replace(
            base_config.storage,
            checkpoint_retention_days=180,
        )
        custom_config = replace(base_config, storage=custom_storage)

        stack = StorageStack(
            cdk_app,
            "CustomRetentionStack",
            env_config=custom_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        template = Template.from_stack(stack)

        # 验证使用自定义保留期
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "ExpirationInDays": 180,
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_custom_ia_transition_days(
        self,
        cdk_app: cdk.App,
        test_account: str,
        test_region: str,
        cdk_env: cdk.Environment,
        test_kms_key: kms.Key,
    ) -> None:
        """验证可自定义 Standard-IA 转换天数.

        CDK 参数: checkpoint_ia_transition_days (默认 30)
        """
        from dataclasses import replace

        from config import EnvironmentConfig

        # 创建自定义 IA 转换配置 (60 天)
        base_config = EnvironmentConfig.for_dev(
            account=test_account, region=test_region
        )
        custom_storage = replace(
            base_config.storage,
            checkpoint_ia_transition_days=60,
        )
        custom_config = replace(base_config, storage=custom_storage)

        stack = StorageStack(
            cdk_app,
            "CustomIATransitionStack",
            env_config=custom_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        template = Template.from_stack(stack)

        # 验证使用自定义 IA 转换天数
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Transitions": Match.array_with(
                                        [
                                            Match.object_like(
                                                {
                                                    "StorageClass": "STANDARD_IA",
                                                    "TransitionInDays": 60,
                                                }
                                            )
                                        ]
                                    ),
                                }
                            )
                        ]
                    )
                }
            },
        )
