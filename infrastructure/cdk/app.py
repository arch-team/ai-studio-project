#!/usr/bin/env python3
"""CDK 应用入口 — 按依赖顺序实例化所有 Stack。

用法: cdk deploy --context env=dev|staging|prod
"""

import json
import os
from pathlib import Path

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from aspects import apply_standard_tags
from cdk_constructs.kms_key import KmsKeyConfig, PlatformKmsKey
from config import get_environment_config
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
from utils import apply_nag_suppressions

# 兜底默认 region
_DEFAULT_REGION = "us-east-1"


def _resolve_from_cdk_json(env_name: str, field: str) -> str | None:
    """从 cdk.json 的 defaultContext.environments 中读取配置值。"""
    cdk_json_path = Path(__file__).parent / "cdk.json"
    if not cdk_json_path.exists():
        return None
    try:
        with open(cdk_json_path, encoding="utf-8") as f:
            data = json.load(f)
        value = (
            data.get("defaultContext", {})
            .get("environments", {})
            .get(env_name, {})
            .get(field)
        )
        return value if value else None
    except (json.JSONDecodeError, OSError):
        return None


def _resolve_context_value(
    app: cdk.App,
    env_name: str,
    *,
    context_key: str,
    cdk_json_field: str,
    env_var: str,
    default: str,
) -> str:
    """按统一优先级链解析配置值。

    优先级: --context > cdk.json > 环境变量 > 兜底默认值
    """
    # 优先级 1: 显式 CLI context 参数
    context_value = app.node.try_get_context(context_key)
    if context_value:
        return str(context_value)

    # 优先级 2: cdk.json defaultContext 配置
    cdk_json_value = _resolve_from_cdk_json(env_name, cdk_json_field)
    if cdk_json_value:
        return cdk_json_value

    # 优先级 3: 环境变量 → 优先级 4: 兜底默认值
    return os.environ.get(env_var) or default


def resolve_region(app: cdk.App, env_name: str) -> str:
    """解析部署 region，按以下优先级:

    1. --context region=xxx (显式 CLI 参数，最高优先级)
    2. cdk.json defaultContext.environments.{env}.region (配置文件)
    3. CDK_DEFAULT_REGION 环境变量 (CDK CLI 自动设置)
    4. "us-east-1" (兜底默认值)
    """
    return _resolve_context_value(
        app,
        env_name,
        context_key="region",
        cdk_json_field="region",
        env_var="CDK_DEFAULT_REGION",
        default=_DEFAULT_REGION,
    )


def resolve_account(app: cdk.App, env_name: str) -> str:
    """解析部署 account，按以下优先级:

    1. --context account=xxx (显式 CLI 参数)
    2. cdk.json defaultContext.environments.{env}.account (配置文件)
    3. CDK_DEFAULT_ACCOUNT 环境变量
    4. "" (空字符串兜底)
    """
    return _resolve_context_value(
        app,
        env_name,
        context_key="account",
        cdk_json_field="account",
        env_var="CDK_DEFAULT_ACCOUNT",
        default="",
    )


def create_app() -> cdk.App:
    """创建并配置 CDK 应用 (所有 Stack)。"""
    app = cdk.App()

    env_name = app.node.try_get_context("env") or "dev"

    # 按优先级解析 account 和 region
    # 优先级: --context > cdk.json defaultContext > 环境变量 > 兜底默认值
    account = resolve_account(app, env_name)
    region = resolve_region(app, env_name)

    # 部署确认日志
    print(f"Deploying to {env_name} environment: account={account}, region={region}")

    env_config = get_environment_config(
        env_name=env_name,
        account=account,
        region=region,
    )

    apply_standard_tags(app, env_config)

    # 通用变量
    stack_prefix = env_config.resource_prefix
    is_prod = env_config.name.value == "prod"

    # =========================================================================
    # Layer 1: Foundation Stacks (VPC, IAM base)
    # =========================================================================

    network_stack = NetworkStack(
        app,
        f"{stack_prefix}-network",
        env_config=env_config,
        env=env_config.to_cdk_environment(),
        description="VPC with public/private subnets, NAT Gateways, and VPC endpoints",
    )

    iam_stack = IamStack(
        app,
        f"{stack_prefix}-iam",
        env_config=env_config,
        env=env_config.to_cdk_environment(),
        description="IAM roles for EKS, Lambda, and service accounts",
    )

    # =========================================================================
    # KMS Keys (集中管理加密密钥)
    # =========================================================================

    s3_kms_key = PlatformKmsKey(
        iam_stack,
        "S3KmsKey",
        env_config=env_config,
        config=KmsKeyConfig(
            alias_suffix="s3",
            description="KMS key for S3 bucket encryption",
        ),
    )

    # RDS KMS key 预创建，但暂不绑定到已部署的 Aurora 集群
    # 未来迁移到 customer-managed key 需要手动操作 (快照 → 恢复)
    PlatformKmsKey(
        iam_stack,
        "RdsKmsKey",
        env_config=env_config,
        config=KmsKeyConfig(
            alias_suffix="rds",
            description="KMS key for Aurora database encryption",
        ),
    )

    # =========================================================================
    # Layer 2: Data Stacks (Aurora, S3, FSx)
    # =========================================================================

    database_stack = DatabaseStack(
        app,
        f"{stack_prefix}-database",
        env_config=env_config,
        vpc=network_stack.vpc,
        # 注意: 不传 customer-managed KMS key，避免对已部署集群触发 replacement
        # Aurora 仍通过 storage_encrypted=True 使用 AWS managed key 加密
        # 未来迁移到 customer-managed key 需要手动操作 (快照 → 恢复)
        # storage_encryption_key=rds_kms_key.key,
        env=env_config.to_cdk_environment(),
        description="Aurora MySQL Serverless v2 with RDS Proxy",
        termination_protection=is_prod,
    )
    database_stack.add_dependency(network_stack)
    database_stack.add_dependency(iam_stack)

    storage_stack = StorageStack(
        app,
        f"{stack_prefix}-storage",
        env_config=env_config,
        encryption_key=s3_kms_key.key,
        env=env_config.to_cdk_environment(),
        description="S3 buckets with lifecycle policies and KMS encryption",
        termination_protection=is_prod,
    )
    storage_stack.add_dependency(iam_stack)

    # =========================================================================
    # Layer 3a: EKS Foundation Stack
    # =========================================================================

    eks_stack = EksStack(
        app,
        f"{stack_prefix}-eks",
        env_config=env_config,
        vpc=network_stack.vpc,
        eks_node_role=iam_stack.eks_node_role,
        env=env_config.to_cdk_environment(),
        description="Amazon EKS cluster for HyperPod orchestration",
    )
    eks_stack.add_dependency(network_stack)
    eks_stack.add_dependency(iam_stack)

    # =========================================================================
    # Layer 3b: SageMaker HyperPod Stack
    # =========================================================================

    sagemaker_hyperpod_stack = SagemakerHyperPodStack(
        app,
        f"{stack_prefix}-sagemaker-hyperpod",
        env_config=env_config,
        vpc=network_stack.vpc,
        eks_cluster=eks_stack.eks_cluster,
        env=env_config.to_cdk_environment(),
        description="SageMaker HyperPod cluster with EKS orchestration",
    )
    sagemaker_hyperpod_stack.add_dependency(eks_stack)

    # =========================================================================
    # Layer 3c: HyperPod Add-ons (Training Operator, Task Governance, Observability)
    # =========================================================================

    hyperpod_addons_stack = HyperPodAddonsStack(
        app,
        f"{stack_prefix}-hyperpod-addons",
        env_config=env_config,
        eks_cluster=eks_stack.eks_cluster,
        env=env_config.to_cdk_environment(),
        description="HyperPod EKS add-ons: Training Operator, Task Governance, Observability",
    )
    hyperpod_addons_stack.add_dependency(eks_stack)
    hyperpod_addons_stack.add_dependency(sagemaker_hyperpod_stack)

    # =========================================================================
    # Layer 4: Observability (AMP + HyperPod Observability Add-on)
    # =========================================================================

    observability_stack = ObservabilityStack(
        app,
        f"{stack_prefix}-observability",
        env_config=env_config,
        eks_cluster=eks_stack.eks_cluster,
        env=env_config.to_cdk_environment(),
        description="Observability: Amazon Managed Prometheus + HyperPod Observability Add-on",
    )
    observability_stack.add_dependency(eks_stack)
    observability_stack.add_dependency(hyperpod_addons_stack)

    # =========================================================================
    # Layer 4: High-Performance Storage (FSx for Lustre)
    # =========================================================================

    fsx_stack = FsxLustreStack(
        app,
        f"{stack_prefix}-fsx",
        env_config=env_config,
        vpc=network_stack.vpc,
        datasets_bucket=storage_stack.datasets_bucket,
        env=env_config.to_cdk_environment(),
        description="FSx for Lustre with S3 Data Repository Association",
        termination_protection=is_prod,
    )
    fsx_stack.add_dependency(network_stack)
    fsx_stack.add_dependency(storage_stack)
    fsx_stack.add_dependency(eks_stack)  # Need EKS cluster for security group reference

    # =========================================================================
    # Layer 5: Network Ingress (ALB with TLS termination)
    # =========================================================================

    certificate_arn = app.node.try_get_context("certificate_arn")
    enable_waf = is_prod

    alb_stack = AlbStack(
        app,
        f"{stack_prefix}-alb",
        env_config=env_config,
        vpc=network_stack.vpc,
        certificate_arn=certificate_arn,
        enable_waf=enable_waf,
        env=env_config.to_cdk_environment(),
        description="Application Load Balancer with TLS 1.2+ termination and WAF",
    )
    alb_stack.add_dependency(network_stack)
    alb_stack.add_dependency(eks_stack)  # Target groups need EKS services

    # =========================================================================
    # Layer 6: Application (ECR, Service Discovery)
    # =========================================================================

    ApplicationStack(
        app,
        f"{stack_prefix}-application",
        env_config=env_config,
        env=env_config.to_cdk_environment(),
        description="Application deployment: ECR repository for backend images",
    )

    # =========================================================================
    # CDK Nag - Security and best practices checks
    # =========================================================================

    cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
    apply_nag_suppressions(app)

    return app


def main() -> None:
    """应用入口。"""
    app = create_app()
    app.synth()


if __name__ == "__main__":
    main()
