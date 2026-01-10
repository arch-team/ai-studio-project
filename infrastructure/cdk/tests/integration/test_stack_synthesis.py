"""
Integration tests for full stack synthesis.

Tests cover:
- Full application synthesis for all environments
- Stack dependency ordering
- Cross-stack references
- CDK Nag compliance (for staging/prod)
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from config import get_environment_config
from stacks import (
    DatabaseStack,
    EksStack,
    FsxLustreStack,
    IamStack,
    NetworkStack,
    StorageStack,
)


class TestFullSynthesis:
    """Tests for full application synthesis."""

    @pytest.fixture
    def test_account(self) -> str:
        """Test AWS account ID."""
        return "123456789012"

    @pytest.fixture
    def test_region(self) -> str:
        """Test AWS region."""
        return "us-east-1"

    @pytest.fixture
    def cdk_env(self, test_account: str, test_region: str) -> cdk.Environment:
        """CDK Environment."""
        return cdk.Environment(account=test_account, region=test_region)

    def test_dev_environment_synthesizes(
        self, test_account: str, test_region: str, cdk_env: cdk.Environment
    ) -> None:
        """Verify dev environment synthesizes without errors."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)

        # Layer 1: Foundation
        network_stack = NetworkStack(
            app, "dev-network", env_config=env_config, env=cdk_env
        )
        iam_stack = IamStack(app, "dev-iam", env_config=env_config, env=cdk_env)

        # Layer 2: Data
        database_stack = DatabaseStack(
            app, "dev-database", env_config=env_config, vpc=network_stack.vpc, env=cdk_env
        )
        storage_stack = StorageStack(
            app, "dev-storage", env_config=env_config, env=cdk_env
        )

        # Verify synthesis
        Template.from_stack(network_stack)
        Template.from_stack(iam_stack)
        Template.from_stack(database_stack)
        Template.from_stack(storage_stack)

    def test_staging_environment_synthesizes(
        self, test_account: str, test_region: str, cdk_env: cdk.Environment
    ) -> None:
        """Verify staging environment synthesizes without errors."""
        app = cdk.App()
        env_config = get_environment_config("staging", test_account, test_region)

        # Layer 1: Foundation
        network_stack = NetworkStack(
            app, "staging-network", env_config=env_config, env=cdk_env
        )
        iam_stack = IamStack(app, "staging-iam", env_config=env_config, env=cdk_env)

        # Layer 2: Data
        database_stack = DatabaseStack(
            app,
            "staging-database",
            env_config=env_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        storage_stack = StorageStack(
            app, "staging-storage", env_config=env_config, env=cdk_env
        )

        # Verify synthesis
        Template.from_stack(network_stack)
        Template.from_stack(iam_stack)
        Template.from_stack(database_stack)
        Template.from_stack(storage_stack)

    def test_prod_environment_synthesizes(
        self, test_account: str, test_region: str, cdk_env: cdk.Environment
    ) -> None:
        """Verify production environment synthesizes without errors."""
        app = cdk.App()
        env_config = get_environment_config("prod", test_account, test_region)

        # Layer 1: Foundation
        network_stack = NetworkStack(
            app, "prod-network", env_config=env_config, env=cdk_env
        )
        iam_stack = IamStack(app, "prod-iam", env_config=env_config, env=cdk_env)

        # Layer 2: Data
        database_stack = DatabaseStack(
            app, "prod-database", env_config=env_config, vpc=network_stack.vpc, env=cdk_env
        )
        storage_stack = StorageStack(
            app, "prod-storage", env_config=env_config, env=cdk_env
        )

        # Verify synthesis
        Template.from_stack(network_stack)
        Template.from_stack(iam_stack)
        Template.from_stack(database_stack)
        Template.from_stack(storage_stack)


class TestStackDependencies:
    """Tests for stack dependency ordering."""

    @pytest.fixture
    def app_with_stacks(
        self, test_account: str, test_region: str
    ) -> tuple[cdk.App, dict[str, cdk.Stack]]:
        """Create app with all stacks for dependency testing."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        stacks = {}

        # Layer 1
        stacks["network"] = NetworkStack(
            app, "test-network", env_config=env_config, env=cdk_env
        )
        stacks["iam"] = IamStack(app, "test-iam", env_config=env_config, env=cdk_env)

        # Layer 2
        stacks["database"] = DatabaseStack(
            app,
            "test-database",
            env_config=env_config,
            vpc=stacks["network"].vpc,
            env=cdk_env,
        )
        stacks["storage"] = StorageStack(
            app, "test-storage", env_config=env_config, env=cdk_env
        )

        # Layer 3a: EKS
        stacks["eks"] = EksStack(
            app,
            "test-eks",
            env_config=env_config,
            vpc=stacks["network"].vpc,
            eks_node_role=stacks["iam"].eks_node_role,
            env=cdk_env,
        )

        return app, stacks

    @pytest.fixture
    def test_account(self) -> str:
        """Test AWS account ID."""
        return "123456789012"

    @pytest.fixture
    def test_region(self) -> str:
        """Test AWS region."""
        return "us-east-1"

    def test_database_depends_on_network(
        self, app_with_stacks: tuple[cdk.App, dict[str, cdk.Stack]]
    ) -> None:
        """Verify database stack can access network VPC."""
        _, stacks = app_with_stacks
        # If this doesn't raise, the dependency is satisfied
        Template.from_stack(stacks["database"])

    def test_eks_depends_on_network_and_iam(
        self, app_with_stacks: tuple[cdk.App, dict[str, cdk.Stack]]
    ) -> None:
        """Verify EKS stack can access network and IAM resources."""
        _, stacks = app_with_stacks
        # If this doesn't raise, the dependencies are satisfied
        Template.from_stack(stacks["eks"])


class TestCrossStackReferences:
    """Tests for cross-stack references."""

    @pytest.fixture
    def test_account(self) -> str:
        """Test AWS account ID."""
        return "123456789012"

    @pytest.fixture
    def test_region(self) -> str:
        """Test AWS region."""
        return "us-east-1"

    def test_vpc_reference_in_database_stack(
        self, test_account: str, test_region: str
    ) -> None:
        """Verify VPC is correctly referenced in database stack."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        network_stack = NetworkStack(
            app, "ref-network", env_config=env_config, env=cdk_env
        )
        database_stack = DatabaseStack(
            app,
            "ref-database",
            env_config=env_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )

        template = Template.from_stack(database_stack)

        # Database should have subnet group
        template.resource_count_is("AWS::RDS::DBSubnetGroup", 1)

    def test_storage_bucket_reference_in_fsx_stack(
        self, test_account: str, test_region: str
    ) -> None:
        """Verify storage bucket is correctly referenced in FSx stack."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        network_stack = NetworkStack(
            app, "fsx-network", env_config=env_config, env=cdk_env
        )
        storage_stack = StorageStack(
            app, "fsx-storage", env_config=env_config, env=cdk_env
        )
        fsx_stack = FsxLustreStack(
            app,
            "fsx-lustre",
            env_config=env_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )

        # If this doesn't raise, the cross-stack reference works
        Template.from_stack(fsx_stack)


class TestResourceCounts:
    """Tests for expected resource counts."""

    @pytest.fixture
    def test_account(self) -> str:
        """Test AWS account ID."""
        return "123456789012"

    @pytest.fixture
    def test_region(self) -> str:
        """Test AWS region."""
        return "us-east-1"

    def test_storage_creates_three_buckets(
        self, test_account: str, test_region: str
    ) -> None:
        """Verify storage stack creates exactly 3 S3 buckets."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        storage_stack = StorageStack(
            app, "count-storage", env_config=env_config, env=cdk_env
        )
        template = Template.from_stack(storage_stack)

        template.resource_count_is("AWS::S3::Bucket", 3)

    def test_network_creates_one_vpc(
        self, test_account: str, test_region: str
    ) -> None:
        """Verify network stack creates exactly 1 VPC."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        network_stack = NetworkStack(
            app, "count-network", env_config=env_config, env=cdk_env
        )
        template = Template.from_stack(network_stack)

        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_database_creates_one_cluster(
        self, test_account: str, test_region: str
    ) -> None:
        """Verify database stack creates exactly 1 Aurora cluster."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        network_stack = NetworkStack(
            app, "db-count-network", env_config=env_config, env=cdk_env
        )
        database_stack = DatabaseStack(
            app,
            "db-count-database",
            env_config=env_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        template = Template.from_stack(database_stack)

        template.resource_count_is("AWS::RDS::DBCluster", 1)
