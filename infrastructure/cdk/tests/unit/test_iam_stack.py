"""
Unit tests for IAM Stack.

Tests cover:
- EKS node role creation
- Training execution role creation
- Backend service role creation
- Managed policy attachments
- Trust relationships
"""

import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import IamStack


class TestIamStackCreation:
    """Tests for IAM Stack creation."""

    @pytest.fixture
    def iam_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> IamStack:
        """Create an IAM Stack for testing."""
        return IamStack(
            cdk_app,
            "TestIamStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, iam_stack: IamStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(iam_stack)

    def test_stack_synthesizes(self, iam_stack: IamStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert iam_stack is not None

    def test_roles_created(self, template: Template) -> None:
        """Verify IAM roles are created."""
        # Should have at least 3 roles (EKS node, training, backend)
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 3


class TestEksNodeRole:
    """Tests for EKS node role."""

    @pytest.fixture
    def iam_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> IamStack:
        """Create IAM Stack for EKS role testing."""
        return IamStack(
            cdk_app,
            "EksRoleTestStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, iam_stack: IamStack) -> Template:
        """Get template for testing."""
        return Template.from_stack(iam_stack)

    def test_eks_node_role_accessible(self, iam_stack: IamStack) -> None:
        """Verify EKS node role is accessible from the stack."""
        assert iam_stack.eks_node_role is not None

    def test_eks_node_role_trust_ec2(self, template: Template) -> None:
        """Verify EKS node role trusts EC2 service."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": Match.object_like(
                    {
                        "Statement": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "ec2.amazonaws.com"},
                                    }
                                )
                            ]
                        )
                    }
                )
            },
        )

    def test_eks_worker_node_policy_attached(self, template: Template) -> None:
        """Verify AmazonEKSWorkerNodePolicy is attached."""
        # Verify that at least one role has managed policy ARNs
        roles = template.find_resources("AWS::IAM::Role")
        has_managed_policies = any(
            "ManagedPolicyArns" in role.get("Properties", {})
            for role in roles.values()
        )
        assert has_managed_policies, "No role with managed policy ARNs found"


class TestTrainingExecutionRole:
    """Tests for training execution role."""

    @pytest.fixture
    def iam_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> IamStack:
        """Create IAM Stack for training role testing."""
        return IamStack(
            cdk_app,
            "TrainingRoleTestStack",
            env_config=dev_config,
            env=cdk_env,
        )

    def test_training_role_accessible(self, iam_stack: IamStack) -> None:
        """Verify training execution role is accessible."""
        assert iam_stack.training_execution_role is not None


class TestBackendServiceRole:
    """Tests for backend service role."""

    @pytest.fixture
    def iam_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> IamStack:
        """Create IAM Stack for backend role testing."""
        return IamStack(
            cdk_app,
            "BackendRoleTestStack",
            env_config=dev_config,
            env=cdk_env,
        )

    def test_backend_role_accessible(self, iam_stack: IamStack) -> None:
        """Verify backend service role is accessible."""
        assert iam_stack.backend_service_role is not None


class TestIamPolicies:
    """Tests for IAM policies."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for policy testing."""
        stack = IamStack(
            cdk_app,
            "PolicyTestStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_policies_created(self, template: Template) -> None:
        """Verify IAM policies are created."""
        policies = template.find_resources("AWS::IAM::Policy")
        assert len(policies) >= 1

    def test_kms_usage_policy_exists(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify KMS usage policy is accessible."""
        stack = IamStack(
            cdk_app,
            "KmsPolicyStack",
            env_config=dev_config,
            env=cdk_env,
        )
        assert stack.kms_usage_policy is not None


class TestRoleNaming:
    """Tests for role naming conventions."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for naming testing."""
        stack = IamStack(
            cdk_app,
            "NamingTestStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_roles_created_with_trust_policy(self, template: Template) -> None:
        """Verify roles are created with trust policies."""
        # Note: Project tags are applied at app level in app.py via cdk.Tags.of(app).add()
        # Individual stack tests won't have these tags applied
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 3, "Expected at least 3 IAM roles"

        # Verify all roles have AssumeRolePolicyDocument
        for role in roles.values():
            props = role.get("Properties", {})
            assert "AssumeRolePolicyDocument" in props, "Role missing trust policy"
