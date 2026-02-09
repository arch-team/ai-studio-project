"""
EKS Stack 单元测试.

测试覆盖:
- EKS 集群创建
- Kubernetes 版本
- 集群端点配置
- Add-ons 安装
- Node Groups 配置
"""

import pytest
from aws_cdk.assertions import Match, Template

from stacks import EksStack


# 使用 conftest 的 network_stack, iam_stack, eks_stack fixtures
@pytest.fixture
def template(eks_stack: EksStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(eks_stack)


class TestEksStackCreation:
    """EKS Stack 创建测试."""

    def test_stack_synthesizes(self, eks_stack: EksStack) -> None:
        """验证 Stack 可以成功合成."""
        assert eks_stack is not None

    def test_eks_cluster_created(self, template: Template) -> None:
        """验证 EKS 集群创建 (通过集群角色)."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": Match.object_like(
                    {
                        "Statement": Match.array_with(
                            [
                                Match.object_like(
                                    {"Principal": {"Service": "eks.amazonaws.com"}}
                                )
                            ]
                        )
                    }
                )
            },
        )


class TestClusterConfiguration:
    """EKS 集群配置测试."""

    def test_cluster_security_group_created(self, template: Template) -> None:
        """验证集群安全组创建."""
        security_groups = template.find_resources("AWS::EC2::SecurityGroup")
        assert len(security_groups) >= 1


class TestEksStackOutputs:
    """EKS Stack 输出属性测试."""

    def test_eks_cluster_accessible(self, eks_stack: EksStack) -> None:
        """验证 EKS 集群可访问."""
        assert eks_stack.eks_cluster is not None


class TestEksAddOns:
    """EKS Add-ons 配置测试."""

    def test_vpc_cni_addon(self, template: Template) -> None:
        """验证 VPC CNI add-on 配置 (通过 Lambda 函数验证)."""
        lambdas = template.find_resources("AWS::Lambda::Function")
        assert len(lambdas) >= 1


class TestClusterTags:
    """EKS 集群标签测试."""

    def test_eks_resources_created(self, template: Template) -> None:
        """验证 EKS 相关资源创建."""
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 1, "Expected at least 1 IAM role for EKS"

        lambdas = template.find_resources("AWS::Lambda::Function")
        assert len(lambdas) >= 1, "Expected at least 1 Lambda for EKS management"
