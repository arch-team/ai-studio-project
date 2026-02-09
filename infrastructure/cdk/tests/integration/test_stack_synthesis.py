"""
全栈合成集成测试.

测试覆盖:
- 各环境 (dev/staging/prod) 全应用合成
- Stack 依赖顺序
- 跨 Stack 引用
- 资源数量验证
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from config import get_environment_config
from stacks import (
    ApplicationStack,
    DatabaseStack,
    EksStack,
    FsxLustreStack,
    IamStack,
    NetworkStack,
    ObservabilityStack,
    StorageStack,
)

# =============================================================================
# 辅助函数 - 消除各环境测试中的重复代码
# =============================================================================


def _synthesize_foundation_stacks(
    env_name: str, test_account: str, test_region: str, cdk_env: cdk.Environment
) -> dict[str, Template]:
    """合成基础层 Stack 并返回模板字典.

    注意: 所有 Stack 必须在同一个 App 中先全部创建，再一次性合成。
    """
    app = cdk.App()
    env_config = get_environment_config(env_name, test_account, test_region)

    # Layer 1: Foundation
    network_stack = NetworkStack(
        app, f"{env_name}-network", env_config=env_config, env=cdk_env
    )
    iam_stack = IamStack(app, f"{env_name}-iam", env_config=env_config, env=cdk_env)

    # Layer 2: Data
    database_stack = DatabaseStack(
        app,
        f"{env_name}-database",
        env_config=env_config,
        vpc=network_stack.vpc,
        env=cdk_env,
    )
    storage_stack = StorageStack(
        app, f"{env_name}-storage", env_config=env_config, env=cdk_env
    )

    # Application (仅 dev 需要验证)
    app_stack = None
    if env_name == "dev":
        app_stack = ApplicationStack(
            app, f"{env_name}-application", env_config=env_config, env=cdk_env
        )

    # 一次性合成所有 Stack (避免 multiple synth 错误)
    templates = {
        "network": Template.from_stack(network_stack),
        "iam": Template.from_stack(iam_stack),
        "database": Template.from_stack(database_stack),
        "storage": Template.from_stack(storage_stack),
    }
    if app_stack is not None:
        templates["application"] = Template.from_stack(app_stack)

    return templates


# =============================================================================
# 各环境合成测试
# =============================================================================


class TestFullSynthesis:
    """全应用合成测试."""

    def test_dev_environment_synthesizes(
        self, test_account: str, test_region: str, cdk_env: cdk.Environment
    ) -> None:
        """验证 dev 环境合成无错误."""
        templates = _synthesize_foundation_stacks(
            "dev", test_account, test_region, cdk_env
        )
        assert "application" in templates

    def test_staging_environment_synthesizes(
        self, test_account: str, test_region: str, cdk_env: cdk.Environment
    ) -> None:
        """验证 staging 环境合成无错误."""
        _synthesize_foundation_stacks("staging", test_account, test_region, cdk_env)

    def test_prod_environment_synthesizes(
        self, test_account: str, test_region: str, cdk_env: cdk.Environment
    ) -> None:
        """验证 prod 环境合成无错误."""
        _synthesize_foundation_stacks("prod", test_account, test_region, cdk_env)


# =============================================================================
# Stack 依赖测试
# =============================================================================


class TestStackDependencies:
    """Stack 依赖顺序测试."""

    @pytest.fixture
    def app_with_stacks(
        self, test_account: str, test_region: str
    ) -> tuple[cdk.App, dict[str, cdk.Stack]]:
        """创建包含所有 Stack 的应用 (用于依赖测试)."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        stacks: dict[str, cdk.Stack] = {}
        stacks["network"] = NetworkStack(
            app, "test-network", env_config=env_config, env=cdk_env
        )
        stacks["iam"] = IamStack(app, "test-iam", env_config=env_config, env=cdk_env)
        stacks["database"] = DatabaseStack(
            app,
            "test-database",
            env_config=env_config,
            vpc=stacks["network"].vpc,
            env=cdk_env,
        )
        stacks["storage"] = StorageStack(
            app, "test-storage", env_config=env_config, env=cdk_env
        )
        stacks["eks"] = EksStack(
            app,
            "test-eks",
            env_config=env_config,
            vpc=stacks["network"].vpc,
            eks_node_role=stacks["iam"].eks_node_role,
            env=cdk_env,
        )
        return app, stacks

    def test_database_depends_on_network(
        self, app_with_stacks: tuple[cdk.App, dict[str, cdk.Stack]]
    ) -> None:
        """验证 Database Stack 可访问 Network VPC."""
        _, stacks = app_with_stacks
        Template.from_stack(stacks["database"])

    def test_eks_depends_on_network_and_iam(
        self, app_with_stacks: tuple[cdk.App, dict[str, cdk.Stack]]
    ) -> None:
        """验证 EKS Stack 可访问 Network 和 IAM 资源."""
        _, stacks = app_with_stacks
        Template.from_stack(stacks["eks"])


# =============================================================================
# 跨 Stack 引用测试
# =============================================================================


class TestCrossStackReferences:
    """跨 Stack 引用测试."""

    def test_vpc_reference_in_database_stack(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 VPC 在 Database Stack 中正确引用."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        network_stack = NetworkStack(
            app, "ref-network", env_config=env_config, env=cdk_env
        )
        database_stack = DatabaseStack(
            app,
            "ref-database",
            env_config=env_config,
            vpc=network_stack.vpc,
            env=cdk_env,
        )
        template = Template.from_stack(database_stack)
        template.resource_count_is("AWS::RDS::DBSubnetGroup", 1)

    def test_storage_bucket_reference_in_fsx_stack(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 Storage Bucket 在 FSx Stack 中正确引用."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        network_stack = NetworkStack(
            app, "fsx-network", env_config=env_config, env=cdk_env
        )
        storage_stack = StorageStack(
            app, "fsx-storage", env_config=env_config, env=cdk_env
        )
        fsx_stack = FsxLustreStack(
            app,
            "fsx-lustre",
            env_config=env_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )
        Template.from_stack(fsx_stack)


# =============================================================================
# 资源数量测试
# =============================================================================


class TestResourceCounts:
    """资源数量验证测试."""

    def _make_template(
        self, test_account: str, test_region: str, stack_factory, prefix: str, **kwargs
    ) -> Template:
        """辅助方法: 创建 Stack 模板."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)
        stack = stack_factory(
            app, f"{prefix}-stack", env_config=env_config, env=cdk_env, **kwargs
        )
        return Template.from_stack(stack)

    def test_storage_creates_three_buckets(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 Storage Stack 创建 3 个 S3 Bucket."""
        template = self._make_template(
            test_account, test_region, StorageStack, "count-storage"
        )
        template.resource_count_is("AWS::S3::Bucket", 3)

    def test_network_creates_one_vpc(self, test_account: str, test_region: str) -> None:
        """验证 Network Stack 创建 1 个 VPC."""
        template = self._make_template(
            test_account, test_region, NetworkStack, "count-network"
        )
        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_database_creates_one_cluster(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 Database Stack 创建 1 个 Aurora 集群."""
        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)
        network = NetworkStack(
            app, "db-count-network", env_config=env_config, env=cdk_env
        )
        db = DatabaseStack(
            app,
            "db-count-database",
            env_config=env_config,
            vpc=network.vpc,
            env=cdk_env,
        )
        Template.from_stack(db).resource_count_is("AWS::RDS::DBCluster", 1)

    def test_application_creates_one_ecr_repository(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 Application Stack 创建 1 个 ECR 仓库."""
        template = self._make_template(
            test_account, test_region, ApplicationStack, "app-count"
        )
        template.resource_count_is("AWS::ECR::Repository", 1)

    def test_observability_creates_amp_workspace(
        self, test_account: str, test_region: str
    ) -> None:
        """验证 Observability Stack 创建 1 个 AMP Workspace."""
        from aws_cdk import aws_ec2 as ec2
        from aws_cdk import aws_eks as eks
        from aws_cdk.lambda_layer_kubectl_v33 import KubectlV33Layer

        app = cdk.App()
        env_config = get_environment_config("dev", test_account, test_region)
        cdk_env = cdk.Environment(account=test_account, region=test_region)

        vpc_stack = cdk.Stack(app, "obs-vpc-stack", env=cdk_env)
        vpc = ec2.Vpc(vpc_stack, "Vpc", max_azs=2)
        eks_stack = cdk.Stack(app, "obs-eks-stack", env=cdk_env)
        cluster = eks.Cluster(
            eks_stack,
            "Cluster",
            cluster_name="test-cluster",
            version=eks.KubernetesVersion.of("1.33"),
            vpc=vpc,
            default_capacity=0,
            kubectl_layer=KubectlV33Layer(eks_stack, "KubectlLayer"),
        )

        observability_stack = ObservabilityStack(
            app,
            "obs-count-observability",
            env_config=env_config,
            eks_cluster=cluster,
            env=cdk_env,
        )
        Template.from_stack(observability_stack).resource_count_is(
            "AWS::APS::Workspace", 1
        )
