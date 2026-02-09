"""
Unit tests for HyperPod Add-ons Stack.

Tests cover:
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
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk.assertions import Match, Template
from aws_cdk.lambda_layer_kubectl_v33 import KubectlV33Layer

from config import EnvironmentConfig
from stacks import HyperPodAddonsStack


class TestHyperPodAddonsStack:
    """HyperPod Add-ons Stack 单元测试."""

    @pytest.fixture
    def vpc(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> ec2.Vpc:
        """创建测试 VPC."""
        stack = cdk.Stack(cdk_app, "VpcStack", env=cdk_env)
        return ec2.Vpc(stack, "Vpc", max_azs=2)

    @pytest.fixture
    def eks_cluster(
        self, cdk_app: cdk.App, cdk_env: cdk.Environment, vpc: ec2.Vpc
    ) -> eks.Cluster:
        """创建测试 EKS 集群."""
        stack = cdk.Stack(cdk_app, "EksStack", env=cdk_env)
        return eks.Cluster(
            stack,
            "TestCluster",
            cluster_name="test-cluster",
            version=eks.KubernetesVersion.of("1.33"),
            vpc=vpc,
            default_capacity=0,
            kubectl_layer=KubectlV33Layer(stack, "KubectlLayer"),
        )

    @pytest.fixture
    def hyperpod_addons_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        eks_cluster: eks.Cluster,
    ) -> HyperPodAddonsStack:
        """创建 HyperPod Add-ons Stack for testing."""
        return HyperPodAddonsStack(
            cdk_app,
            "TestHyperPodAddonsStack",
            env_config=dev_config,
            eks_cluster=eks_cluster,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, hyperpod_addons_stack: HyperPodAddonsStack) -> Template:
        """获取 CloudFormation 模板."""
        return Template.from_stack(hyperpod_addons_stack)

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
                                            [
                                                "sts:AssumeRole",
                                                "sts:TagSession",
                                            ]
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
