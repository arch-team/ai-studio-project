"""
Unit tests for Observability Stack.

Tests cover:
- AMP Workspace 创建
- HyperPod Observability Add-on 安装
- Pod Identity Association
- CloudFormation 输出
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk.assertions import Template
from aws_cdk.lambda_layer_kubectl_v33 import KubectlV33Layer

from config import EnvironmentConfig
from stacks import ObservabilityStack


class TestObservabilityStackCreation:
    """Tests for Observability Stack creation."""

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
    def observability_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        eks_cluster: eks.Cluster,
    ) -> ObservabilityStack:
        """创建 Observability Stack for testing."""
        return ObservabilityStack(
            cdk_app,
            "TestObservabilityStack",
            env_config=dev_config,
            eks_cluster=eks_cluster,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, observability_stack: ObservabilityStack) -> Template:
        """Get CloudFormation template."""
        return Template.from_stack(observability_stack)

    def test_stack_synthesizes(self, observability_stack: ObservabilityStack) -> None:
        """验证 Stack 可以成功合成."""
        assert observability_stack is not None

    def test_amp_workspace_created(self, template: Template) -> None:
        """验证 AMP Workspace 创建."""
        template.resource_count_is("AWS::APS::Workspace", 1)

    def test_amp_workspace_has_alias(self, template: Template) -> None:
        """验证 AMP Workspace 有正确的别名."""
        template.has_resource_properties(
            "AWS::APS::Workspace",
            {
                "Alias": "ai-platform-dev-amp",
            },
        )

    def test_observability_addon_installed(self, template: Template) -> None:
        """验证 Observability Add-on 安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {
                "AddonName": "amazon-sagemaker-hyperpod-observability",
            },
        )

    def test_pod_identity_association_created(self, template: Template) -> None:
        """验证 Pod Identity Association 创建."""
        template.has_resource_properties(
            "AWS::EKS::PodIdentityAssociation",
            {
                "Namespace": "hyperpod-observability",
                "ServiceAccount": "hyperpod-observability-operator-otel-collector",
            },
        )

    def test_collector_role_created(self, template: Template) -> None:
        """验证 Collector IAM Role 创建."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": "ai-platform-dev-observability-collector-role",
            },
        )

    def test_outputs_exported(self, observability_stack: ObservabilityStack) -> None:
        """验证 Stack 输出."""
        template = Template.from_stack(observability_stack)
        # 验证至少有 AMP 和 Add-on 相关输出
        outputs = template.to_json().get("Outputs", {})
        assert len(outputs) >= 2
