"""
CDK 测试共享 fixture 配置.

提供所有测试模块共用的 fixture:
- 环境配置 (dev/staging/prod)
- CDK App 和 Environment
- 常用 Stack 依赖链 (Network, IAM, EKS)
- 轻量级 EKS 集群 fixture (用于不需要完整 Stack 的测试)
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk.lambda_layer_kubectl_v33 import KubectlV33Layer

from config import EnvironmentConfig
from stacks import EksStack, IamStack, NetworkStack

# =============================================================================
# 环境配置 Fixtures
# =============================================================================


@pytest.fixture
def test_account() -> str:
    """测试 AWS 账户 ID."""
    return "123456789012"


@pytest.fixture
def test_region() -> str:
    """测试 AWS 区域."""
    return "us-east-1"


@pytest.fixture
def dev_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """开发环境配置."""
    return EnvironmentConfig.for_dev(account=test_account, region=test_region)


@pytest.fixture
def staging_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """预发布环境配置."""
    return EnvironmentConfig.for_staging(account=test_account, region=test_region)


@pytest.fixture
def prod_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """生产环境配置."""
    return EnvironmentConfig.for_prod(account=test_account, region=test_region)


# =============================================================================
# CDK App Fixtures
# =============================================================================


@pytest.fixture
def cdk_app() -> cdk.App:
    """为每个测试创建新的 CDK App."""
    return cdk.App()


@pytest.fixture
def cdk_env(test_account: str, test_region: str) -> cdk.Environment:
    """CDK 部署环境."""
    return cdk.Environment(account=test_account, region=test_region)


# =============================================================================
# 共用 Stack 依赖链 Fixtures
# 消除 ALB/HyperPod/FSx 等测试文件中的重复 Stack 创建
# =============================================================================


@pytest.fixture
def network_stack(
    cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
) -> NetworkStack:
    """共用 NetworkStack fixture."""
    return NetworkStack(cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env)


@pytest.fixture
def iam_stack(
    cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
) -> IamStack:
    """共用 IamStack fixture."""
    return IamStack(cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env)


@pytest.fixture
def eks_stack(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    network_stack: NetworkStack,
    iam_stack: IamStack,
) -> EksStack:
    """共用 EksStack fixture (依赖 network_stack 和 iam_stack)."""
    return EksStack(
        cdk_app,
        "TestEksStack",
        env_config=dev_config,
        vpc=network_stack.vpc,
        eks_node_role=iam_stack.eks_node_role,
        env=cdk_env,
    )


# =============================================================================
# 轻量级 EKS 集群 Fixtures
# 用于 HyperPodAddonsStack, ObservabilityStack 等不需要完整 EKS Stack 的测试
# =============================================================================


@pytest.fixture
def lightweight_vpc(cdk_app: cdk.App, cdk_env: cdk.Environment) -> ec2.Vpc:
    """轻量级测试 VPC (不经过 NetworkStack)."""
    stack = cdk.Stack(cdk_app, "VpcStack", env=cdk_env)
    return ec2.Vpc(stack, "Vpc", max_azs=2)


@pytest.fixture
def lightweight_eks_cluster(
    cdk_app: cdk.App, cdk_env: cdk.Environment, lightweight_vpc: ec2.Vpc
) -> eks.Cluster:
    """轻量级测试 EKS 集群 (不经过 EksStack)."""
    stack = cdk.Stack(cdk_app, "EksStack", env=cdk_env)
    return eks.Cluster(
        stack,
        "TestCluster",
        cluster_name="test-cluster",
        version=eks.KubernetesVersion.of("1.33"),
        vpc=lightweight_vpc,
        default_capacity=0,
        kubectl_layer=KubectlV33Layer(stack, "KubectlLayer"),
    )
