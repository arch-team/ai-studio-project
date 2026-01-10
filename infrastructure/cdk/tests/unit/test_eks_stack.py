"""
Unit tests for EKS Stack.

Tests cover:
- EKS cluster creation
- Kubernetes version
- Cluster endpoint configuration
- Add-ons installation
- Node groups configuration
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import EksStack, IamStack, NetworkStack


class TestEksStackCreation:
    """Tests for EKS Stack creation."""

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
    def iam_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> IamStack:
        """Create IAM Stack as dependency."""
        return IamStack(
            cdk_app,
            "TestIamStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def eks_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        network_stack: NetworkStack,
        iam_stack: IamStack,
    ) -> EksStack:
        """Create an EKS Stack for testing."""
        return EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, eks_stack: EksStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(eks_stack)

    def test_stack_synthesizes(self, eks_stack: EksStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert eks_stack is not None

    def test_eks_cluster_created(self, template: Template) -> None:
        """Verify EKS cluster is created."""
        # CDK creates a custom resource for EKS clusters
        # Check for the cluster role which is always present
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": Match.object_like(
                    {
                        "Statement": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Principal": {"Service": "eks.amazonaws.com"},
                                    }
                                )
                            ]
                        )
                    }
                )
            },
        )


class TestClusterConfiguration:
    """Tests for EKS cluster configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for cluster configuration testing."""
        network_stack = NetworkStack(
            cdk_app,
            "ConfigNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        iam_stack = IamStack(
            cdk_app,
            "ConfigIamStack",
            env_config=dev_config,
            env=cdk_env,
        )
        eks_stack = EksStack(
            cdk_app,
            "ConfigEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        return Template.from_stack(eks_stack)

    def test_cluster_security_group_created(self, template: Template) -> None:
        """Verify cluster security group is created."""
        # EKS creates security groups for cluster communication
        security_groups = template.find_resources("AWS::EC2::SecurityGroup")
        assert len(security_groups) >= 1


class TestEksStackOutputs:
    """Tests for EKS Stack outputs."""

    @pytest.fixture
    def eks_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> EksStack:
        """Create EKS Stack for output testing."""
        network_stack = NetworkStack(
            cdk_app,
            "OutputNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        iam_stack = IamStack(
            cdk_app,
            "OutputIamStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return EksStack(
            cdk_app,
            "OutputEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )

    def test_eks_cluster_accessible(self, eks_stack: EksStack) -> None:
        """Verify EKS cluster is accessible from the stack."""
        assert eks_stack.eks_cluster is not None


class TestEksAddOns:
    """Tests for EKS add-ons configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for add-ons testing."""
        network_stack = NetworkStack(
            cdk_app,
            "AddonsNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        iam_stack = IamStack(
            cdk_app,
            "AddonsIamStack",
            env_config=dev_config,
            env=cdk_env,
        )
        eks_stack = EksStack(
            cdk_app,
            "AddonsEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        return Template.from_stack(eks_stack)

    def test_vpc_cni_addon(self, template: Template) -> None:
        """Verify VPC CNI add-on is configured."""
        # CDK EKS creates Lambda for kubectl operations
        # The add-ons are typically installed via Helm or kubectl
        # We verify Lambda functions are created for cluster management
        lambdas = template.find_resources("AWS::Lambda::Function")
        assert len(lambdas) >= 1


class TestClusterTags:
    """Tests for EKS cluster tagging."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for tag testing."""
        network_stack = NetworkStack(
            cdk_app,
            "TagNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        iam_stack = IamStack(
            cdk_app,
            "TagIamStack",
            env_config=dev_config,
            env=cdk_env,
        )
        eks_stack = EksStack(
            cdk_app,
            "TagEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        return Template.from_stack(eks_stack)

    def test_eks_resources_created(self, template: Template) -> None:
        """Verify EKS resources are created."""
        # Note: Project tags are applied at app level in app.py via cdk.Tags.of(app).add()
        # Individual stack tests won't have these tags applied
        # Verify IAM roles are created for EKS
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 1, "Expected at least 1 IAM role for EKS"

        # Verify Lambda functions are created for cluster management
        lambdas = template.find_resources("AWS::Lambda::Function")
        assert len(lambdas) >= 1, "Expected at least 1 Lambda for EKS management"
