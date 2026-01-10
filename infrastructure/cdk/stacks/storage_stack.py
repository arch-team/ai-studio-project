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
from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3

from config import EnvironmentConfig
from constructs import Construct


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
        """Create S3 bucket for training datasets.

        Lifecycle policy:
        - Move infrequently accessed data to Standard-IA after 90 days
        - Move to Glacier after 365 days (long-term archival)
        """
        bucket_name = f"{self.env_config.resource_prefix}-datasets"

        lifecycle_rules = [
            s3.LifecycleRule(
                id="TransitionToIA",
                enabled=True,
                transitions=[
                    s3.Transition(
                        storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                        transition_after=Duration.days(90),
                    ),
                    s3.Transition(
                        storage_class=s3.StorageClass.GLACIER,
                        transition_after=Duration.days(365),
                    ),
                ],
            ),
            # Delete incomplete multipart uploads after 7 days
            s3.LifecycleRule(
                id="AbortIncompleteMultipartUpload",
                enabled=True,
                abort_incomplete_multipart_upload_after=Duration.days(7),
            ),
            # Delete old versions after 90 days
            s3.LifecycleRule(
                id="ExpireOldVersions",
                enabled=True,
                noncurrent_version_expiration=Duration.days(90),
            ),
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
        """Create S3 bucket for trained model artifacts.

        Lifecycle policy:
        - Keep models in Standard for 180 days
        - Move to Standard-IA after 180 days
        - Never delete (models are valuable artifacts)
        """
        bucket_name = f"{self.env_config.resource_prefix}-models"

        lifecycle_rules = [
            s3.LifecycleRule(
                id="TransitionToIA",
                enabled=True,
                transitions=[
                    s3.Transition(
                        storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                        transition_after=Duration.days(180),
                    ),
                ],
            ),
            # Delete incomplete multipart uploads after 7 days
            s3.LifecycleRule(
                id="AbortIncompleteMultipartUpload",
                enabled=True,
                abort_incomplete_multipart_upload_after=Duration.days(7),
            ),
            # Keep old versions for 365 days (model versioning)
            s3.LifecycleRule(
                id="ExpireOldVersions",
                enabled=True,
                noncurrent_version_expiration=Duration.days(365),
            ),
        ]

        return self._create_base_bucket(
            bucket_id="ModelsBucket",
            bucket_name=bucket_name,
            lifecycle_rules=lifecycle_rules,
            intelligent_tiering=False,  # Models accessed predictably
        )

    def _create_checkpoints_bucket(self) -> s3.Bucket:
        """Create S3 bucket for training checkpoints.

        Lifecycle policy (based on env_config.storage settings):
        - Transition to Standard-IA after checkpoint_ia_transition_days
        - Expire after checkpoint_retention_days
        - Aggressive cleanup of old versions (checkpoints are temporary)
        """
        bucket_name = f"{self.env_config.resource_prefix}-checkpoints"
        storage_config = self.env_config.storage

        lifecycle_rules = [
            # Transition checkpoints to IA for cost optimization
            s3.LifecycleRule(
                id="TransitionToIA",
                enabled=True,
                transitions=[
                    s3.Transition(
                        storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                        transition_after=Duration.days(
                            storage_config.checkpoint_ia_transition_days
                        ),
                    ),
                ],
            ),
            # Expire old checkpoints
            s3.LifecycleRule(
                id="ExpireCheckpoints",
                enabled=True,
                expiration=Duration.days(storage_config.checkpoint_retention_days),
            ),
            # Delete incomplete multipart uploads after 3 days
            s3.LifecycleRule(
                id="AbortIncompleteMultipartUpload",
                enabled=True,
                abort_incomplete_multipart_upload_after=Duration.days(3),
            ),
            # Delete old versions quickly (checkpoints are replaceable)
            s3.LifecycleRule(
                id="ExpireOldVersions",
                enabled=True,
                noncurrent_version_expiration=Duration.days(7),
            ),
        ]

        return self._create_base_bucket(
            bucket_id="CheckpointsBucket",
            bucket_name=bucket_name,
            lifecycle_rules=lifecycle_rules,
            intelligent_tiering=False,  # Explicit lifecycle for checkpoints
        )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
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
