"""
CDK Nag 安全合规测试 — 验证关键 Stack 通过 AwsSolutionsChecks.

测试覆盖:
- IamStack: 无未抑制的 Nag 错误
- StorageStack: 无未抑制的 Nag 错误
- DatabaseStack: 无未抑制的 Nag 错误

注意: Stack construct ID 必须以 -iam, -storage, -database 结尾，
才能匹配 nag_suppressions.py 中的抑制规则。
"""

import aws_cdk as cdk
from aws_cdk import aws_kms as kms
from cdk_nag import AwsSolutionsChecks

from config import EnvironmentConfig
from stacks import DatabaseStack, IamStack, NetworkStack, StorageStack
from utils import apply_nag_suppressions


def _get_nag_errors(stack: cdk.Stack) -> list[str]:
    """从 Stack 的 annotations 中提取 Nag 错误。"""
    errors: list[str] = []
    for child in stack.node.find_all():
        metadata = child.node.metadata
        for entry in metadata:
            if entry.type == "aws:cdk:error":
                errors.append(f"{child.node.path}: {entry.data}")
    return errors


class TestIamStackNagCompliance:
    """IamStack CDK Nag 合规测试."""

    def test_no_unsuppressed_nag_errors(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 IamStack 无未抑制的 Nag 错误."""
        app = cdk.App()
        env_config = EnvironmentConfig.for_dev(account=test_account, region=test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        # construct ID 以 -iam 结尾以匹配 nag_suppressions 规则
        stack = IamStack(app, "nag-test-iam", env_config=env_config, env=cdk_env)

        cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
        apply_nag_suppressions(app)
        app.synth()

        errors = _get_nag_errors(stack)
        assert len(errors) == 0, (
            f"IamStack 有 {len(errors)} 个未抑制的 Nag 错误:\n" + "\n".join(errors[:10])
        )


class TestStorageStackNagCompliance:
    """StorageStack CDK Nag 合规测试."""

    def test_no_unsuppressed_nag_errors(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 StorageStack 无未抑制的 Nag 错误."""
        app = cdk.App()
        env_config = EnvironmentConfig.for_dev(account=test_account, region=test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        kms_stack = cdk.Stack(app, "nag-kms", env=cdk_env)
        test_key = kms.Key(kms_stack, "TestKey")

        # construct ID 以 -storage 结尾以匹配 nag_suppressions 规则
        stack = StorageStack(
            app,
            "nag-test-storage",
            env_config=env_config,
            encryption_key=test_key,
            env=cdk_env,
        )

        cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
        apply_nag_suppressions(app)
        app.synth()

        errors = _get_nag_errors(stack)
        assert len(errors) == 0, (
            f"StorageStack 有 {len(errors)} 个未抑制的 Nag 错误:\n"
            + "\n".join(errors[:10])
        )


class TestDatabaseStackNagCompliance:
    """DatabaseStack CDK Nag 合规测试."""

    def test_no_unsuppressed_nag_errors(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 DatabaseStack 无未抑制的 Nag 错误."""
        app = cdk.App()
        env_config = EnvironmentConfig.for_dev(account=test_account, region=test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        network_stack = NetworkStack(
            app, "nag-network", env_config=env_config, env=cdk_env
        )
        # construct ID 以 -database 结尾以匹配 nag_suppressions 规则
        stack = DatabaseStack(
            app,
            "nag-test-database",
            env_config=env_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )

        cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
        apply_nag_suppressions(app)
        app.synth()

        errors = _get_nag_errors(stack)
        assert len(errors) == 0, (
            f"DatabaseStack 有 {len(errors)} 个未抑制的 Nag 错误:\n"
            + "\n".join(errors[:10])
        )
