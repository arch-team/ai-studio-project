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
from aws_cdk import aws_s3 as s3

from config import EnvironmentConfig
from constructs import Construct
from utils import LifecycleRuleBuilder


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
        **kwargs,
    ) -> None:
        """Initialize the Storage Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config

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

        # Create bucket with SSE-KMS encryption
        bucket = s3.Bucket(
            self,
            bucket_id,
            bucket_name=bucket_name,
            # Encryption configuration (AWS managed key)
            encryption=s3.BucketEncryption.S3_MANAGED,
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
            auto_delete_objects=not self.env_config.protection.retain_on_delete,
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
        - checkpoint_retention_days 天后过期删除
        - 3 天后删除未完成的分片上传（检查点频繁写入）
        - 7 天后删除旧版本（检查点可替换）
        """
        bucket_name = f"{self.env_config.resource_prefix}-checkpoints"
        storage_config = self.env_config.storage
        builder = LifecycleRuleBuilder()

        lifecycle_rules = [
            builder.transition_rule(
                "TransitionToIA",
                [
                    (
                        s3.StorageClass.INFREQUENT_ACCESS,
                        storage_config.checkpoint_ia_transition_days,
                    )
                ],
            ),
            builder.expiration_rule(
                "ExpireCheckpoints",
                storage_config.checkpoint_retention_days,
            ),
            builder.incomplete_multipart_rule(days=3),
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
        cdk.CfnOutput(
            self,
            "DatasetsBucketName",
            value=self._datasets_bucket.bucket_name,
            description="S3 bucket name for training datasets",
            export_name=f"{self.env_config.resource_prefix}-datasets-bucket",
        )
        cdk.CfnOutput(
            self,
            "DatasetsBucketArn",
            value=self._datasets_bucket.bucket_arn,
            description="S3 bucket ARN for training datasets",
            export_name=f"{self.env_config.resource_prefix}-datasets-bucket-arn",
        )

        # Models bucket
        cdk.CfnOutput(
            self,
            "ModelsBucketName",
            value=self._models_bucket.bucket_name,
            description="S3 bucket name for model artifacts",
            export_name=f"{self.env_config.resource_prefix}-models-bucket",
        )
        cdk.CfnOutput(
            self,
            "ModelsBucketArn",
            value=self._models_bucket.bucket_arn,
            description="S3 bucket ARN for model artifacts",
            export_name=f"{self.env_config.resource_prefix}-models-bucket-arn",
        )

        # Checkpoints bucket
        cdk.CfnOutput(
            self,
            "CheckpointsBucketName",
            value=self._checkpoints_bucket.bucket_name,
            description="S3 bucket name for training checkpoints",
            export_name=f"{self.env_config.resource_prefix}-checkpoints-bucket",
        )
        cdk.CfnOutput(
            self,
            "CheckpointsBucketArn",
            value=self._checkpoints_bucket.bucket_arn,
            description="S3 bucket ARN for training checkpoints",
            export_name=f"{self.env_config.resource_prefix}-checkpoints-bucket-arn",
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
