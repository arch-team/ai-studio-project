"""
Export Name 冲突检测测试.

合成所有 dev 环境 Stack 模板，收集所有 CloudFormation Export Name，
断言没有重复，防止部署时因 Export Name 冲突而失败。

背景:
- database_stack 和 fsx_stack 的 SecurityGroupId 曾因自动生成的 export_name
  相同而冲突，已通过显式 export_name 解决。
- 本测试自动化检测，防止未来新增 output 时再次引入冲突。
"""

from collections import Counter

import aws_cdk as cdk
import pytest
from aws_cdk import aws_kms as kms
from aws_cdk.assertions import Template

from config import EnvironmentConfig
from stacks import (
    AlbStack,
    ApplicationStack,
    DatabaseStack,
    EksStack,
    FsxLustreStack,
    HyperPodAddonsStack,
    IamStack,
    NetworkStack,
    ObservabilityStack,
    SagemakerHyperPodStack,
    StorageStack,
)


@pytest.fixture
def all_dev_templates(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
) -> dict[str, Template]:
    """合成所有 dev 环境 Stack 模板."""
    # L1: Foundation
    network_stack = NetworkStack(
        cdk_app, "ExportTestNetwork", env_config=dev_config, env=cdk_env
    )
    iam_stack = IamStack(cdk_app, "ExportTestIam", env_config=dev_config, env=cdk_env)

    # KMS Key
    kms_stack = cdk.Stack(cdk_app, "ExportTestKms", env=cdk_env)
    test_key = kms.Key(kms_stack, "TestKey")

    # L2: Data & Storage
    database_stack = DatabaseStack(
        cdk_app,
        "ExportTestDatabase",
        env_config=dev_config,
        vpc=network_stack.vpc,
        env=cdk_env,
    )
    storage_stack = StorageStack(
        cdk_app,
        "ExportTestStorage",
        env_config=dev_config,
        encryption_key=test_key,
        env=cdk_env,
    )

    # L3: Compute
    eks_stack = EksStack(
        cdk_app,
        "ExportTestEks",
        env_config=dev_config,
        vpc=network_stack.vpc,
        eks_node_role=iam_stack.eks_node_role,
        env=cdk_env,
    )
    sagemaker_hyperpod_stack = SagemakerHyperPodStack(
        cdk_app,
        "ExportTestHyperPod",
        env_config=dev_config,
        vpc=network_stack.vpc,
        eks_cluster=eks_stack.eks_cluster,
        env=cdk_env,
    )
    hyperpod_addons_stack = HyperPodAddonsStack(
        cdk_app,
        "ExportTestHyperPodAddons",
        env_config=dev_config,
        eks_cluster=eks_stack.eks_cluster,
        env=cdk_env,
    )

    # L4: Observability & FSx
    observability_stack = ObservabilityStack(
        cdk_app,
        "ExportTestObservability",
        env_config=dev_config,
        eks_cluster=eks_stack.eks_cluster,
        env=cdk_env,
    )
    fsx_stack = FsxLustreStack(
        cdk_app,
        "ExportTestFsx",
        env_config=dev_config,
        vpc=network_stack.vpc,
        datasets_bucket=storage_stack.datasets_bucket,
        env=cdk_env,
    )

    # L5: ALB
    alb_stack = AlbStack(
        cdk_app,
        "ExportTestAlb",
        env_config=dev_config,
        vpc=network_stack.vpc,
        env=cdk_env,
    )

    # L6: Application
    application_stack = ApplicationStack(
        cdk_app,
        "ExportTestApplication",
        env_config=dev_config,
        env=cdk_env,
    )

    return {
        "Network": Template.from_stack(network_stack),
        "IAM": Template.from_stack(iam_stack),
        "Database": Template.from_stack(database_stack),
        "Storage": Template.from_stack(storage_stack),
        "EKS": Template.from_stack(eks_stack),
        "HyperPod": Template.from_stack(sagemaker_hyperpod_stack),
        "HyperPodAddons": Template.from_stack(hyperpod_addons_stack),
        "Observability": Template.from_stack(observability_stack),
        "FSx": Template.from_stack(fsx_stack),
        "ALB": Template.from_stack(alb_stack),
        "Application": Template.from_stack(application_stack),
    }


def _collect_export_names(templates: dict[str, Template]) -> list[tuple[str, str]]:
    """从所有模板中收集 (stack_name, export_name) 对."""
    exports: list[tuple[str, str]] = []
    for stack_name, template in templates.items():
        template_json = template.to_json()
        outputs = template_json.get("Outputs", {})
        for _output_id, output_def in outputs.items():
            export = output_def.get("Export", {})
            export_name = export.get("Name")
            if export_name and isinstance(export_name, str):
                exports.append((stack_name, export_name))
    return exports


class TestExportNameUniqueness:
    """Export Name 全局唯一性测试."""

    def test_no_duplicate_export_names(
        self, all_dev_templates: dict[str, Template]
    ) -> None:
        """验证所有 Stack 的 Export Name 没有重复."""
        exports = _collect_export_names(all_dev_templates)
        export_names = [name for _, name in exports]
        counts = Counter(export_names)
        duplicates = {name: count for name, count in counts.items() if count > 1}

        if duplicates:
            # 构建详细错误信息，显示冲突的 Stack
            details: list[str] = []
            for dup_name in sorted(duplicates):
                stacks = [s for s, n in exports if n == dup_name]
                details.append(f"  '{dup_name}' 出现在: {', '.join(stacks)}")
            msg = f"发现 {len(duplicates)} 个重复的 Export Name:\n" + "\n".join(details)
            pytest.fail(msg)

    def test_all_stacks_have_exports(
        self, all_dev_templates: dict[str, Template]
    ) -> None:
        """验证每个 Stack 至少有一个 Export（基础检查）."""
        for stack_name, template in all_dev_templates.items():
            template_json = template.to_json()
            outputs = template_json.get("Outputs", {})
            has_export = any("Export" in output_def for output_def in outputs.values())
            assert has_export, f"{stack_name} Stack 没有任何 Export"

    def test_explicit_export_names_follow_prefix_pattern(
        self, all_dev_templates: dict[str, Template]
    ) -> None:
        """验证显式 Export Name 都以 resource_prefix 开头.

        CDK 自动生成的跨 Stack 引用 Export (格式 StackId:ExportsOutput*)
        不在检查范围内，仅验证通过 create_output 创建的显式导出。
        """
        exports = _collect_export_names(all_dev_templates)
        prefix = "ai-platform-dev"
        # 过滤掉 CDK 自动生成的跨 Stack 引用 Export
        explicit_exports = [
            (stack, name) for stack, name in exports if ":ExportsOutput" not in name
        ]
        invalid = [
            (stack, name)
            for stack, name in explicit_exports
            if not name.startswith(prefix)
        ]
        if invalid:
            details = [f"  {stack}: '{name}'" for stack, name in invalid]
            msg = f"以下 Export Name 不以 '{prefix}' 开头:\n" + "\n".join(details)
            pytest.fail(msg)
