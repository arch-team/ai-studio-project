"""
HyperPod Add-ons Stack 单元测试.

测试覆盖:
- Stack 合成
- Training Operator EKS Add-on 安装
- Task Governance EKS Add-on 安装
- Training Operator IAM Role (Pod Identity)
- Pod Identity Association
- Observability Add-on 迁移状态
- CloudFormation 输出
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_eks as eks
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import HyperPodAddonsStack


# 使用 conftest 的 lightweight_vpc 和 lightweight_eks_cluster fixtures
@pytest.fixture
def hyperpod_addons_stack(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    lightweight_eks_cluster: eks.Cluster,
) -> HyperPodAddonsStack:
    """创建 HyperPod Add-ons Stack."""
    return HyperPodAddonsStack(
        cdk_app,
        "TestHyperPodAddonsStack",
        env_config=dev_config,
        eks_cluster=lightweight_eks_cluster,
        env=cdk_env,
    )


@pytest.fixture
def template(hyperpod_addons_stack: HyperPodAddonsStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(hyperpod_addons_stack)


class TestHyperPodAddonsStack:
    """HyperPod Add-ons Stack 单元测试."""

    def test_stack_synthesizes(
        self, hyperpod_addons_stack: HyperPodAddonsStack
    ) -> None:
        """验证 Stack 可以成功合成."""
        assert hyperpod_addons_stack is not None

    def test_training_operator_addon_installed(self, template: Template) -> None:
        """验证 Training Operator add-on 安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "amazon-sagemaker-hyperpod-training-operator",
                "ResolveConflicts": "OVERWRITE",
            },
        )

    def test_task_governance_addon_installed(self, template: Template) -> None:
        """验证 Task Governance add-on 安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "amazon-sagemaker-hyperpod-taskgovernance",
                "ResolveConflicts": "OVERWRITE",
            },
        )

    def test_training_operator_role_created(self, template: Template) -> None:
        """验证 Training Operator Pod Identity IAM Role 创建."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": Match.object_like(
                    {
                        "Statement": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Action": Match.array_with(
                                            ["sts:AssumeRole", "sts:TagSession"]
                                        ),
                                        "Effect": "Allow",
                                        "Principal": {
                                            "Service": "pods.eks.amazonaws.com"
                                        },
                                    }
                                )
                            ]
                        ),
                    }
                ),
                "RoleName": "ai-platform-dev-training-operator-role",
                "ManagedPolicyArns": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Fn::Join": [
                                    "",
                                    [
                                        "arn:",
                                        {"Ref": "AWS::Partition"},
                                        ":iam::aws:policy/AmazonSageMakerHyperPodTrainingOperatorAccess",
                                    ],
                                ],
                            }
                        ),
                    ]
                ),
            },
        )

    def test_pod_identity_association_created(self, template: Template) -> None:
        """验证 Training Operator Pod Identity Association 创建."""
        template.has_resource_properties(
            "AWS::EKS::PodIdentityAssociation",
            {
                "Namespace": "aws-hyperpod",
                "ServiceAccount": "hp-training-operator-controller-manager",
            },
        )

    def test_observability_addon_is_none(
        self, hyperpod_addons_stack: HyperPodAddonsStack
    ) -> None:
        """验证 observability_addon 为 None (已迁移到 ObservabilityStack)."""
        assert hyperpod_addons_stack.observability_addon is None

    def test_outputs_exported(self, hyperpod_addons_stack: HyperPodAddonsStack) -> None:
        """验证 Stack 输出包含 Training Operator 和 Task Governance."""
        template = Template.from_stack(hyperpod_addons_stack)
        outputs = template.to_json().get("Outputs", {})
        # 至少包含: TrainingOperatorAddonName, TaskGovernanceAddonName, ObservabilityAddonStatus
        assert len(outputs) >= 3
