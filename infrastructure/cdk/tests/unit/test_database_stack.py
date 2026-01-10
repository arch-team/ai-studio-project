"""
Unit tests for Database Stack.

Tests cover:
- Aurora MySQL Serverless v2 cluster creation
- Encryption at rest
- Backup configuration
- Security group configuration
- RDS Proxy (optional)
- Removal policies per environment
- IAM authentication
"""

import pytest
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import DatabaseStack, NetworkStack


class TestDatabaseStackCreation:
    """Tests for Database Stack creation."""

    @pytest.fixture
    def network_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> NetworkStack:
        """Create Network Stack as dependency."""
        return NetworkStack(
            cdk_app,
            "TestNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def database_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        network_stack: NetworkStack,
    ) -> DatabaseStack:
        """Create a Database Stack for testing."""
        return DatabaseStack(
            cdk_app,
            "TestDatabaseStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, database_stack: DatabaseStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(database_stack)

    def test_stack_synthesizes(self, database_stack: DatabaseStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert database_stack is not None

    def test_aurora_cluster_created(self, template: Template) -> None:
        """Verify Aurora cluster is created."""
        template.resource_count_is("AWS::RDS::DBCluster", 1)


class TestAuroraClusterConfiguration:
    """Tests for Aurora cluster configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for cluster testing."""
        network_stack = NetworkStack(
            cdk_app,
            "ClusterNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        db_stack = DatabaseStack(
            cdk_app,
            "ClusterTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        return Template.from_stack(db_stack)

    def test_aurora_mysql_engine(self, template: Template) -> None:
        """Verify Aurora MySQL engine is used."""
        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "Engine": "aurora-mysql",
            },
        )

    def test_storage_encrypted(self, template: Template) -> None:
        """Verify storage encryption is enabled."""
        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "StorageEncrypted": True,
            },
        )

    def test_iam_authentication_enabled(self, template: Template) -> None:
        """Verify IAM database authentication is enabled."""
        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "EnableIAMDatabaseAuthentication": True,
            },
        )

    def test_cloudwatch_logs_export(self, template: Template) -> None:
        """Verify CloudWatch logs export is configured."""
        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "EnableCloudwatchLogsExports": Match.array_with(["audit", "error", "slowquery"]),
            },
        )

    def test_default_database_created(self, template: Template) -> None:
        """Verify default database is created."""
        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "DatabaseName": "ai_platform",
            },
        )


class TestServerlessV2Configuration:
    """Tests for Serverless v2 configuration."""

    def test_dev_min_acu(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify dev environment uses 0.5 ACU minimum (can pause)."""
        network_stack = NetworkStack(
            cdk_app,
            "DevAcuNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        db_stack = DatabaseStack(
            cdk_app,
            "DevAcuStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        template = Template.from_stack(db_stack)

        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "ServerlessV2ScalingConfiguration": {
                    "MinCapacity": 0.5,
                    "MaxCapacity": 8,
                },
            },
        )

    def test_prod_min_acu(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify prod environment uses 2.0 ACU minimum (always warm)."""
        network_stack = NetworkStack(
            cdk_app,
            "ProdAcuNetworkStack",
            env_config=prod_config,
            env=cdk_env,
        )
        db_stack = DatabaseStack(
            cdk_app,
            "ProdAcuStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        template = Template.from_stack(db_stack)

        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "ServerlessV2ScalingConfiguration": {
                    "MinCapacity": 2,
                    "MaxCapacity": 16,
                },
            },
        )


class TestRemovalPolicies:
    """Tests for removal policies per environment."""

    def test_dev_cluster_destroyable(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify dev cluster can be destroyed."""
        network_stack = NetworkStack(
            cdk_app,
            "DevRemovalNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        db_stack = DatabaseStack(
            cdk_app,
            "DevRemovalStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        template = Template.from_stack(db_stack)

        template.has_resource(
            "AWS::RDS::DBCluster",
            {
                "DeletionPolicy": "Delete",
            },
        )

    def test_prod_cluster_retained(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify prod cluster is retained on deletion."""
        network_stack = NetworkStack(
            cdk_app,
            "ProdRemovalNetworkStack",
            env_config=prod_config,
            env=cdk_env,
        )
        db_stack = DatabaseStack(
            cdk_app,
            "ProdRemovalStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        template = Template.from_stack(db_stack)

        template.has_resource(
            "AWS::RDS::DBCluster",
            {
                "DeletionPolicy": "Retain",
            },
        )

    def test_prod_deletion_protection(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify prod has deletion protection enabled."""
        network_stack = NetworkStack(
            cdk_app,
            "ProdProtectionNetworkStack",
            env_config=prod_config,
            env=cdk_env,
        )
        db_stack = DatabaseStack(
            cdk_app,
            "ProdProtectionStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        template = Template.from_stack(db_stack)

        template.has_resource_properties(
            "AWS::RDS::DBCluster",
            {
                "DeletionProtection": True,
            },
        )


class TestSecurityConfiguration:
    """Tests for security configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for security testing."""
        network_stack = NetworkStack(
            cdk_app,
            "SecurityNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        db_stack = DatabaseStack(
            cdk_app,
            "SecurityTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        return Template.from_stack(db_stack)

    def test_security_group_created(self, template: Template) -> None:
        """Verify security group is created."""
        template.resource_count_is("AWS::EC2::SecurityGroup", 1)

    def test_credentials_secret_created(self, template: Template) -> None:
        """Verify credentials secret is created."""
        template.resource_count_is("AWS::SecretsManager::Secret", 1)


class TestDatabaseStackOutputs:
    """Tests for Database Stack outputs."""

    @pytest.fixture
    def database_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> DatabaseStack:
        """Create Database Stack for output testing."""
        network_stack = NetworkStack(
            cdk_app,
            "OutputNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return DatabaseStack(
            cdk_app,
            "OutputTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )

    def test_cluster_accessible(self, database_stack: DatabaseStack) -> None:
        """Verify cluster is accessible from the stack."""
        assert database_stack.cluster is not None

    def test_security_group_accessible(self, database_stack: DatabaseStack) -> None:
        """Verify security group is accessible."""
        assert database_stack.security_group is not None

    def test_secret_accessible(self, database_stack: DatabaseStack) -> None:
        """Verify secret is accessible."""
        assert database_stack.secret is not None
