"""
Unit tests for IAM helper functions.

Tests cover:
- create_tagged_role: 标准 IAM 角色创建
- create_pod_identity_role: EKS Pod Identity 角色创建
- create_irsa_role: IRSA 角色创建
- add_policy_statement: 策略语句添加
- create_irsa_conditions: IRSA 条件创建
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_iam as iam
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from utils.iam_helpers import (
    add_policy_statement,
    add_policy_statements,
    create_irsa_conditions,
    create_irsa_role,
    create_pod_identity_role,
    create_pod_identity_trust_policy,
    create_tagged_role,
)


class TestCreateTaggedRole:
    """Tests for create_tagged_role function."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    def test_creates_role_with_name(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证角色创建时使用正确的命名前缀."""
        role = create_tagged_role(
            scope=stack,
            construct_id="TestRole",
            env_config=dev_config,
            role_name_suffix="test-role",
            description="Test role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": "ai-platform-dev-test-role",
                "Description": "Test role",
            },
        )
        assert role is not None

    def test_attaches_managed_policies(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证托管策略正确附加."""
        create_tagged_role(
            scope=stack,
            construct_id="TestRole",
            env_config=dev_config,
            role_name_suffix="test-role",
            description="Test role with policies",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=["AmazonS3ReadOnlyAccess"],
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "ManagedPolicyArns": Match.array_with(
                    [
                        {
                            "Fn::Join": Match.any_value(),
                        }
                    ]
                ),
            },
        )

    def test_applies_tags(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证标签正确应用."""
        create_tagged_role(
            scope=stack,
            construct_id="TestRole",
            env_config=dev_config,
            role_name_suffix="test-role",
            description="Test role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            additional_tags={"Component": "test"},
        )

        template = Template.from_stack(stack)
        # 分别检查每个标签是否存在
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "Name", "Value": "ai-platform-dev-test-role"}
                        ),
                    ]
                ),
            },
        )
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like({"Key": "Component", "Value": "test"}),
                    ]
                ),
            },
        )


class TestCreatePodIdentityRole:
    """Tests for create_pod_identity_role function."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    def test_creates_pod_identity_role(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证 Pod Identity 角色创建."""
        role = create_pod_identity_role(
            scope=stack,
            construct_id="TestPodRole",
            env_config=dev_config,
            role_name_suffix="pod-test-role",
            description="Pod Identity test role",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": "ai-platform-dev-pod-test-role",
                "Description": "Pod Identity test role",
            },
        )
        assert role is not None

    def test_pod_identity_trust_policy(self) -> None:
        """验证 Pod Identity 信任策略包含 sts:TagSession."""
        policy = create_pod_identity_trust_policy()
        policy_json = policy.to_json()

        statements = policy_json["Statement"]
        assert len(statements) == 1
        assert "sts:AssumeRole" in statements[0]["Action"]
        assert "sts:TagSession" in statements[0]["Action"]


class TestCreateIrsaRole:
    """Tests for create_irsa_role function."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    def test_creates_irsa_role(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证 IRSA 角色创建."""
        role = create_irsa_role(
            scope=stack,
            construct_id="TestIrsaRole",
            env_config=dev_config,
            oidc_provider_arn="arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
            oidc_issuer="oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
            role_name_suffix="irsa-test-role",
            service_account="test-sa",
            namespace="kube-system",
            description="IRSA test role",
            managed_policies=["AmazonS3ReadOnlyAccess"],
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": "ai-platform-dev-irsa-test-role",
                "Description": "IRSA test role",
            },
        )
        assert role is not None

    def test_irsa_role_has_federated_principal(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证 IRSA 角色使用联合身份提供者."""
        create_irsa_role(
            scope=stack,
            construct_id="TestIrsaRole",
            env_config=dev_config,
            oidc_provider_arn="arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
            oidc_issuer="oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
            role_name_suffix="irsa-test-role",
            service_account="test-sa",
            description="IRSA test role",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            {
                                "Action": "sts:AssumeRoleWithWebIdentity",
                                "Effect": "Allow",
                                "Condition": Match.object_like(
                                    {"StringEquals": Match.any_value()}
                                ),
                                "Principal": {
                                    "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
                                },
                            }
                        ]
                    ),
                },
            },
        )

    def test_irsa_role_custom_namespace(
        self, stack: cdk.Stack, dev_config: EnvironmentConfig
    ) -> None:
        """验证 IRSA 角色支持自定义 namespace."""
        role = create_irsa_role(
            scope=stack,
            construct_id="TestIrsaRole",
            env_config=dev_config,
            oidc_provider_arn="arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
            oidc_issuer="oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
            role_name_suffix="irsa-test-role",
            service_account="custom-sa",
            namespace="custom-ns",
            description="IRSA test role",
        )
        assert role is not None


class TestCreateIrsaConditions:
    """Tests for create_irsa_conditions function."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    def test_creates_conditions(self, stack: cdk.Stack) -> None:
        """验证 IRSA 条件创建."""
        conditions = create_irsa_conditions(
            scope=stack,
            construct_id="TestConditions",
            oidc_issuer="oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE",
            namespace="kube-system",
            service_account="test-sa",
        )
        assert conditions is not None


class TestAddPolicyStatement:
    """Tests for add_policy_statement function."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    def test_adds_single_statement(self, stack: cdk.Stack) -> None:
        """验证单条策略语句添加."""
        role = iam.Role(
            stack,
            "TestRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        add_policy_statement(
            role=role,
            sid="TestStatement",
            actions=["s3:GetObject"],
            resources=["arn:aws:s3:::test-bucket/*"],
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            {
                                "Sid": "TestStatement",
                                "Effect": "Allow",
                                "Action": "s3:GetObject",
                                "Resource": "arn:aws:s3:::test-bucket/*",
                            }
                        ]
                    ),
                },
            },
        )

    def test_adds_multiple_statements(self, stack: cdk.Stack) -> None:
        """验证多条策略语句批量添加."""
        role = iam.Role(
            stack,
            "TestRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        add_policy_statements(
            role=role,
            statements=[
                ("Statement1", ["s3:GetObject"], ["arn:aws:s3:::bucket1/*"]),
                ("Statement2", ["s3:PutObject"], ["arn:aws:s3:::bucket2/*"]),
            ],
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like({"Sid": "Statement1"}),
                            Match.object_like({"Sid": "Statement2"}),
                        ]
                    ),
                },
            },
        )
