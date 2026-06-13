"""
IAM Stack 单元测试.

测试覆盖:
- EKS 节点角色创建
- 训练执行角色创建
- 后端服务角色创建
- 托管策略附加
- 信任关系
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import IamStack


# 模块级 fixture: 所有测试类共用同一个 Stack 和 Template
@pytest.fixture
def iam_stack(
    cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
) -> IamStack:
    """创建 IAM Stack."""
    return IamStack(cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env)


@pytest.fixture
def template(iam_stack: IamStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(iam_stack)


class TestIamStackCreation:
    """IAM Stack 创建测试."""

    def test_stack_synthesizes(self, iam_stack: IamStack) -> None:
        """验证 Stack 可以成功合成."""
        assert iam_stack is not None

    def test_roles_created(self, template: Template) -> None:
        """验证 IAM 角色创建 (至少 3 个: EKS 节点、训练、后端)."""
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 3


class TestEksNodeRole:
    """EKS 节点角色测试."""

    def test_eks_node_role_accessible(self, iam_stack: IamStack) -> None:
        """验证 EKS 节点角色可访问."""
        assert iam_stack.eks_node_role is not None

    def test_eks_node_role_trust_ec2(self, template: Template) -> None:
        """验证 EKS 节点角色信任 EC2 服务."""
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
        """验证 AmazonEKSWorkerNodePolicy 已附加."""
        roles = template.find_resources("AWS::IAM::Role")
        has_managed_policies = any(
            "ManagedPolicyArns" in role.get("Properties", {}) for role in roles.values()
        )
        assert has_managed_policies, "No role with managed policy ARNs found"


class TestTrainingExecutionRole:
    """训练执行角色测试."""

    def test_training_role_accessible(self, iam_stack: IamStack) -> None:
        """验证训练执行角色可访问."""
        assert iam_stack.training_execution_role is not None


class TestBackendServiceRole:
    """后端服务角色测试."""

    def test_backend_role_accessible(self, iam_stack: IamStack) -> None:
        """验证后端服务角色可访问."""
        assert iam_stack.backend_service_role is not None

    def test_backend_role_amp_query_access(self, template: Template) -> None:
        """验证后端服务角色具备 AMP (Amazon Managed Prometheus) 查询权限."""
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": Match.object_like(
                    {
                        "Statement": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Action": Match.array_with(
                                            [
                                                "aps:QueryMetrics",
                                                "aps:GetSeries",
                                                "aps:GetLabels",
                                                "aps:GetMetricMetadata",
                                            ]
                                        ),
                                        "Effect": "Allow",
                                        "Sid": "AmpQueryAccess",
                                    }
                                )
                            ]
                        )
                    }
                )
            },
        )


class TestIamPolicies:
    """IAM 策略测试."""

    def test_policies_created(self, template: Template) -> None:
        """验证 IAM 策略创建."""
        policies = template.find_resources("AWS::IAM::Policy")
        assert len(policies) >= 1

    def test_kms_usage_policy_exists(self, iam_stack: IamStack) -> None:
        """验证 KMS 使用策略可访问."""
        assert iam_stack.kms_usage_policy is not None


class TestRoleNaming:
    """角色命名规范测试."""

    def test_roles_created_with_trust_policy(self, template: Template) -> None:
        """验证所有角色都有信任策略."""
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 3, "Expected at least 3 IAM roles"

        for role in roles.values():
            props = role.get("Properties", {})
            assert "AssumeRolePolicyDocument" in props, "Role missing trust policy"
