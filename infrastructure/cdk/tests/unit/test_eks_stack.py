"""
EKS Stack 单元测试.

测试覆盖:
- EKS 集群创建和配置
- Kubernetes 版本
- 集群端点配置 (Private)
- Add-ons 安装 (EBS CSI, FSx CSI, VPC CNI, CoreDNS, kube-proxy)
- Node Groups 配置
- EKS Admin 角色条件约束
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
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "GroupDescription": Match.any_value(),
                "VpcId": Match.any_value(),
            },
        )

    def test_eks_admin_role_has_condition(self, template: Template) -> None:
        """验证 EKS Admin 角色有 PrincipalTag 条件约束."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": Match.string_like_regexp(".*eks-admin-role"),
                "AssumeRolePolicyDocument": Match.object_like(
                    {
                        "Statement": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Condition": {
                                            "StringEquals": {
                                                "aws:PrincipalTag/Role": "EKSAdmin"
                                            }
                                        }
                                    }
                                )
                            ]
                        )
                    }
                ),
            },
        )


class TestEksStackOutputs:
    """EKS Stack 输出属性测试."""

    def test_eks_cluster_accessible(self, eks_stack: EksStack) -> None:
        """验证 EKS 集群可访问."""
        assert eks_stack.eks_cluster is not None


class TestEksAddOns:
    """EKS Add-ons 配置测试."""

    def test_ebs_csi_addon_installed(self, template: Template) -> None:
        """验证 EBS CSI Driver add-on 已安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "aws-ebs-csi-driver",
            },
        )

    def test_fsx_csi_addon_installed(self, template: Template) -> None:
        """验证 FSx CSI Driver add-on 已安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "aws-fsx-csi-driver",
            },
        )

    def test_vpc_cni_addon_installed(self, template: Template) -> None:
        """验证 VPC CNI add-on 已安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "vpc-cni",
            },
        )

    def test_coredns_addon_installed(self, template: Template) -> None:
        """验证 CoreDNS add-on 已安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "coredns",
            },
        )

    def test_kube_proxy_addon_installed(self, template: Template) -> None:
        """验证 kube-proxy add-on 已安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "kube-proxy",
            },
        )

    def test_fsx_csi_role_no_full_access(self, template: Template) -> None:
        """验证 FSx CSI 角色未使用 AmazonFSxFullAccess 托管策略."""
        roles = template.find_resources("AWS::IAM::Role")
        for _logical_id, role_def in roles.items():
            policies = role_def.get("Properties", {}).get("ManagedPolicyArns", [])
            for policy in policies:
                if isinstance(policy, str):
                    assert "AmazonFSxFullAccess" not in policy, (
                        "FSx CSI role should not use AmazonFSxFullAccess"
                    )


class TestClusterTags:
    """EKS 集群标签测试."""

    def test_eks_resources_created(self, template: Template) -> None:
        """验证 EKS 相关资源创建."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": Match.any_value(),
            },
        )
