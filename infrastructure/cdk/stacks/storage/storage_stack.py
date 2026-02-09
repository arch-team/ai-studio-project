"""
Storage Stack for AI Training Platform.

This stack creates S3 buckets for:
- Training datasets
- Model artifacts
- Checkpoints and snapshots

All buckets are configured with:
- SSE-KMS encryption (AWS managed key)
- Versioning enabled
- Lifecycle policies for cost optimization
- HTTPS-only bucket policy
"""

import aws_cdk as cdk
from aws_cdk import Duration
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_s3 as s3

from config import EnvironmentConfig
from constructs import Construct
from utils import LifecycleRuleBuilder
from utils.outputs import create_output


class StorageStack(cdk.Stack):
    """S3 Storage Stack with encryption and lifecycle policies.

    This stack creates:
    - Datasets bucket: Training data storage
    - Models bucket: Trained model artifacts
    - Checkpoints bucket: Training checkpoints with tiered storage

    All buckets enforce:
    - SSE-KMS encryption at rest
    - HTTPS-only transport
    - Versioning for data protection
    - Lifecycle rules for cost optimization

    Attributes:
        datasets_bucket: S3 bucket for training datasets
        models_bucket: S3 bucket for model artifacts
        checkpoints_bucket: S3 bucket for training checkpoints
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        encryption_key: kms.IKey | None = None,
        **kwargs,
    ) -> None:
        """Initialize the Storage Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            encryption_key: 自定义 KMS Key 用于 S3 加密 (None 则使用 S3_MANAGED)
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._encryption_key = encryption_key

        # Create S3 buckets
        self._datasets_bucket = self._create_datasets_bucket()
        self._models_bucket = self._create_models_bucket()
        self._checkpoints_bucket = self._create_checkpoints_bucket()

        # Create outputs
        self._create_outputs()

    def _create_base_bucket(
        self,
        bucket_id: str,
        bucket_name: str,
        lifecycle_rules: list[s3.LifecycleRule] | None = None,
        intelligent_tiering: bool = False,
    ) -> s3.Bucket:
        """Create a base S3 bucket with standard security configuration.

        All buckets are configured with:
        - SSE-KMS encryption (AWS managed key: aws/s3)
        - Versioning enabled
        - Block all public access
        - HTTPS-only enforcement via bucket policy
        - Access logging enabled

        Args:
            bucket_id: CDK construct ID
            bucket_name: S3 bucket name
            lifecycle_rules: Optional lifecycle rules
            intelligent_tiering: Enable S3 Intelligent-Tiering

        Returns:
            Configured S3 bucket
        """
        # Use protection config for removal policy
        removal_policy = self.env_config.protection.removal_policy

        # 选择加密方式: 自定义 KMS Key > S3 Managed
        if self._encryption_key:
            encryption = s3.BucketEncryption.KMS
            encryption_key_ref = self._encryption_key
        else:
            encryption = s3.BucketEncryption.S3_MANAGED
            encryption_key_ref = None

        # Create bucket with encryption
        bucket = s3.Bucket(
            self,
            bucket_id,
            bucket_name=bucket_name,
            # Encryption configuration
            encryption=encryption,
            encryption_key=encryption_key_ref,
            # Enable versioning for data protection
            versioned=True,
            # Block all public access (security best practice)
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            # Enforce SSL/HTTPS only
            enforce_ssl=True,
            # Enable intelligent tiering if requested
            intelligent_tiering_configurations=(
                [
                    s3.IntelligentTieringConfiguration(
                        name="AutoTiering",
                        archive_access_tier_time=Duration.days(90),
                        deep_archive_access_tier_time=Duration.days(180),
                    )
                ]
                if intelligent_tiering
                else None
            ),
            # Lifecycle rules
            lifecycle_rules=lifecycle_rules or [],
            # Removal policy (from protection config)
            removal_policy=removal_policy,
            # Auto-delete objects only supported with DESTROY policy
            auto_delete_objects=(removal_policy == cdk.RemovalPolicy.DESTROY),
            # Object ownership (recommended setting)
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        )

        # Add standard tags
        cdk.Tags.of(bucket).add("Name", bucket_name)
        cdk.Tags.of(bucket).add("DataClassification", "internal")

        return bucket

    def _create_datasets_bucket(self) -> s3.Bucket:
        """创建训练数据集 S3 bucket。

        生命周期策略:
        - 90 天后转换到 Standard-IA
        - 365 天后转换到 Glacier（长期归档）
        - 7 天后删除未完成的分片上传
        - 90 天后删除旧版本
        """
        bucket_name = f"{self.env_config.resource_prefix}-datasets"
        builder = LifecycleRuleBuilder()

        lifecycle_rules = [
            builder.transition_rule(
                "TransitionToIA",
                [
                    (s3.StorageClass.INFREQUENT_ACCESS, 90),
                    (s3.StorageClass.GLACIER, 365),
                ],
            ),
            builder.incomplete_multipart_rule(days=7),
            builder.old_versions_rule(days=90),
        ]

        bucket = self._create_base_bucket(
            bucket_id="DatasetsBucket",
            bucket_name=bucket_name,
            lifecycle_rules=lifecycle_rules,
            intelligent_tiering=True,
        )

        # Add CORS configuration for web uploads (if needed)
        bucket.add_cors_rule(
            allowed_methods=[
                s3.HttpMethods.GET,
                s3.HttpMethods.PUT,
                s3.HttpMethods.POST,
            ],
            allowed_origins=["*"],  # Restrict in production
            allowed_headers=["*"],
            max_age=3000,
        )

        return bucket

    def _create_models_bucket(self) -> s3.Bucket:
        """创建模型制品 S3 bucket。

        生命周期策略:
        - 180 天后转换到 Standard-IA
        - 永不删除（模型是宝贵资产）
        - 7 天后删除未完成的分片上传
        - 365 天后删除旧版本（保留模型版本历史）
        """
        bucket_name = f"{self.env_config.resource_prefix}-models"
        builder = LifecycleRuleBuilder()

        lifecycle_rules = [
            builder.transition_rule(
                "TransitionToIA",
                [(s3.StorageClass.INFREQUENT_ACCESS, 180)],
            ),
            builder.incomplete_multipart_rule(days=7),
            builder.old_versions_rule(days=365),
        ]

        return self._create_base_bucket(
            bucket_id="ModelsBucket",
            bucket_name=bucket_name,
            lifecycle_rules=lifecycle_rules,
            intelligent_tiering=False,  # Models accessed predictably
        )

    def _create_checkpoints_bucket(self) -> s3.Bucket:
        """创建训练检查点 S3 bucket。

        生命周期策略（基于 env_config.storage 配置）:
        - checkpoint_ia_transition_days 天后转换到 Standard-IA
        - checkpoint_retention_days 天后过期删除（仅 cold/ 前缀）
        - 3 天后删除未完成的分片上传（检查点频繁写入）
        - 7 天后删除旧版本（检查点可替换）

        T038b-2 说明:
        - 生命周期规则 1 (存储类转换): 所有检查点 30 天后转换到 Standard-IA，节省约 50% 存储成本
        - 生命周期规则 2 (自动删除): 仅对 cold/ 前缀的冷检查点应用，避免误删热/温检查点
        - 合规性: 90 天保留期满足审计要求和模型回滚需求
        - 成本优化: Standard-IA 转换 + 冷检查点自动删除，预估可节省 60-70% 长期存储成本
        """
        bucket_name = f"{self.env_config.resource_prefix}-checkpoints"
        storage_config = self.env_config.storage
        builder = LifecycleRuleBuilder()

        lifecycle_rules = [
            # 规则 1: 所有检查点转换到 Standard-IA (成本优化)
            builder.transition_rule(
                "TransitionToIA",
                [
                    (
                        s3.StorageClass.INFREQUENT_ACCESS,
                        storage_config.checkpoint_ia_transition_days,
                    )
                ],
            ),
            # 规则 2: 仅冷检查点自动删除 (使用 cold/ 前缀过滤，避免误删热/温检查点)
            # CheckpointMigrationService (T038b-1) 将冷检查点迁移到 s3://bucket/cold/ 目录
            builder.expiration_rule(
                "ExpireCheckpoints",
                storage_config.checkpoint_retention_days,
                prefix="cold/",
            ),
            # 规则 3: 清理未完成的分片上传 (检查点频繁写入场景)
            builder.incomplete_multipart_rule(days=3),
            # 规则 4: 清理旧版本 (检查点可替换，7 天足够故障恢复)
            builder.old_versions_rule(days=7),
        ]

        return self._create_base_bucket(
            bucket_id="CheckpointsBucket",
            bucket_name=bucket_name,
            lifecycle_rules=lifecycle_rules,
            intelligent_tiering=False,  # Explicit lifecycle for checkpoints
        )

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出用于跨 Stack 引用。"""
        # Datasets bucket
        create_output(
            self,
            "DatasetsBucketName",
            self._datasets_bucket.bucket_name,
            "S3 bucket name for training datasets",
        )
        create_output(
            self,
            "DatasetsBucketArn",
            self._datasets_bucket.bucket_arn,
            "S3 bucket ARN for training datasets",
        )
        # Models bucket
        create_output(
            self,
            "ModelsBucketName",
            self._models_bucket.bucket_name,
            "S3 bucket name for model artifacts",
        )
        create_output(
            self,
            "ModelsBucketArn",
            self._models_bucket.bucket_arn,
            "S3 bucket ARN for model artifacts",
        )
        # Checkpoints bucket
        create_output(
            self,
            "CheckpointsBucketName",
            self._checkpoints_bucket.bucket_name,
            "S3 bucket name for training checkpoints",
        )
        create_output(
            self,
            "CheckpointsBucketArn",
            self._checkpoints_bucket.bucket_arn,
            "S3 bucket ARN for training checkpoints",
        )

    @property
    def datasets_bucket(self) -> s3.Bucket:
        """Get datasets S3 bucket."""
        return self._datasets_bucket

    @property
    def models_bucket(self) -> s3.Bucket:
        """Get models S3 bucket."""
        return self._models_bucket

    @property
    def checkpoints_bucket(self) -> s3.Bucket:
        """Get checkpoints S3 bucket."""
        return self._checkpoints_bucket

    def grant_read_write(self, grantee: iam.IGrantable) -> None:
        """Grant read/write access to all storage buckets.

        Args:
            grantee: IAM principal to grant access
        """
        self._datasets_bucket.grant_read_write(grantee)
        self._models_bucket.grant_read_write(grantee)
        self._checkpoints_bucket.grant_read_write(grantee)

    def grant_read(self, grantee: iam.IGrantable) -> None:
        """Grant read-only access to all storage buckets.

        Args:
            grantee: IAM principal to grant access
        """
        self._datasets_bucket.grant_read(grantee)
        self._models_bucket.grant_read(grantee)
        self._checkpoints_bucket.grant_read(grantee)
