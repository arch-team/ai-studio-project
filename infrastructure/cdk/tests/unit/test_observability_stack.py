"""
Observability Stack 单元测试.

测试覆盖:
- AMP Workspace 创建
- HyperPod Observability Add-on 安装
- Pod Identity Association
- CloudFormation 输出
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_eks as eks
from aws_cdk.assertions import Template

from config import EnvironmentConfig
from stacks import ObservabilityStack


# 使用 conftest 的 lightweight_vpc 和 lightweight_eks_cluster fixtures
@pytest.fixture
def observability_stack(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    lightweight_eks_cluster: eks.Cluster,
) -> ObservabilityStack:
    """创建 Observability Stack."""
    return ObservabilityStack(
        cdk_app,
        "TestObservabilityStack",
        env_config=dev_config,
        eks_cluster=lightweight_eks_cluster,
        env=cdk_env,
    )


@pytest.fixture
def template(observability_stack: ObservabilityStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(observability_stack)


class TestObservabilityStackCreation:
    """Observability Stack 创建测试."""

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
            {"Alias": "ai-platform-dev-amp"},
        )

    def test_observability_addon_installed(self, template: Template) -> None:
        """验证 Observability Add-on 安装."""
        template.has_resource_properties(
            "AWS::EKS::Addon",
            {"AddonName": "amazon-sagemaker-hyperpod-observability"},
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
            {"RoleName": "ai-platform-dev-observability-collector-role"},
        )

    def test_amp_audit_log_group_created(self, template: Template) -> None:
        """验证 AMP 审计日志组创建."""
        template.has_resource_properties(
            "AWS::Logs::LogGroup",
            {"LogGroupName": "/aws/amp/ai-platform-dev"},
        )

    def test_amp_workspace_has_logging_configuration(self, template: Template) -> None:
        """验证 AMP Workspace 配置了 CloudWatch Logs。"""
        # 通过 JSON 模板验证 LoggingConfiguration 已设置
        cfn_template = template.to_json()
        amp_resources = [
            v for v in cfn_template.get("Resources", {}).values()
            if v.get("Type") == "AWS::APS::Workspace"
        ]
        assert len(amp_resources) == 1
        assert "LoggingConfiguration" in amp_resources[0]["Properties"]

    def test_outputs_exported(self, observability_stack: ObservabilityStack) -> None:
        """验证 Stack 输出."""
        template = Template.from_stack(observability_stack)
        outputs = template.to_json().get("Outputs", {})
        assert len(outputs) >= 2
