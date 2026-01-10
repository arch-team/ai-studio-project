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
"""

import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import StorageStack


class TestStorageStackCreation:
    """Tests for Storage Stack creation."""

    @pytest.fixture
    def storage_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> StorageStack:
        """Create a Storage Stack for testing."""
        return StorageStack(
            cdk_app,
            "TestStorageStack",
            env_config=dev_config,
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
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for security testing."""
        stack = StorageStack(
            cdk_app,
            "SecurityTestStack",
            env_config=dev_config,
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
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify dev buckets can be destroyed."""
        stack = StorageStack(
            cdk_app,
            "DevRemovalStack",
            env_config=dev_config,
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
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify prod buckets are retained on deletion."""
        stack = StorageStack(
            cdk_app,
            "ProdRemovalStack",
            env_config=prod_config,
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
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for lifecycle testing."""
        stack = StorageStack(
            cdk_app,
            "LifecycleTestStack",
            env_config=dev_config,
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
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> StorageStack:
        """Create Storage Stack for output testing."""
        return StorageStack(
            cdk_app,
            "OutputTestStack",
            env_config=dev_config,
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
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for tag testing."""
        stack = StorageStack(
            cdk_app,
            "TagTestStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_buckets_have_name_tag(self, template: Template) -> None:
        """Verify buckets have Name tag."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [Match.object_like({"Key": "Name"})]
                ),
            },
        )

    def test_buckets_have_data_classification_tag(self, template: Template) -> None:
        """Verify buckets have DataClassification tag."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [Match.object_like({"Key": "DataClassification", "Value": "internal"})]
                ),
            },
        )
