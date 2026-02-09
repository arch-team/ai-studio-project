#!/usr/bin/env python3
"""
AWS CDK Application Entry Point for AI Training Platform.

This is the main entry point for deploying the AI Training Platform infrastructure.
It instantiates all stacks with proper dependency ordering and environment configuration.

Usage:
    cdk deploy --context env=dev       # Deploy development environment
    cdk deploy --context env=staging   # Deploy staging environment
    cdk deploy --context env=prod      # Deploy production environment
    cdk synth                          # Synthesize CloudFormation templates
"""

import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from aspects import apply_standard_tags
from cdk_constructs.kms_key import KmsKeyConfig, PlatformKmsKey
from config import get_environment_config
from stacks import (
    AlbStack,
    DatabaseStack,
    EksStack,
    FsxLustreStack,
    HyperPodAddonsStack,
    IamStack,
    NetworkStack,
    SagemakerHyperPodStack,
    StorageStack,
)
from utils import apply_nag_suppressions


def create_app() -> cdk.App:
    """Create and configure the CDK application with all stacks."""
    app = cdk.App()

    # Get environment from context or default to 'dev'
    env_name = app.node.try_get_context("env") or "dev"

    # Get account and region from context or environment variables
    account = (
        app.node.try_get_context("account")
        or os.environ.get("CDK_DEFAULT_ACCOUNT")
        or ""
    )
    region = (
        app.node.try_get_context("region")
        or os.environ.get("CDK_DEFAULT_REGION")
        or "us-east-1"
    )

    # Load environment configuration
    env_config = get_environment_config(
        env_name=env_name,
        account=account,
        region=region,
    )

    # Apply standard tags (centralized tag management)
    # This includes: Project, Environment, ManagedBy, CostCenter
    apply_standard_tags(app, env_config)

    # Stack naming convention: ai-platform-{env}-{stack-name}
    stack_prefix = env_config.resource_prefix

    # =========================================================================
    # Layer 1: Foundation Stacks (VPC, IAM base)
    # =========================================================================

    # Network Stack - VPC with 3-tier subnet isolation
    network_stack = NetworkStack(
        app,
        f"{stack_prefix}-network",
        env_config=env_config,
        env=env_config.to_cdk_environment(),
        description="VPC with public/private subnets, NAT Gateways, and VPC endpoints",
    )

    # IAM Stack - Base IAM roles and policies
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

    # 在 IAM Stack 中创建 KMS Keys (与 IAM 角色共存)
    s3_kms_key = PlatformKmsKey(
        iam_stack,
        "S3KmsKey",
        env_config=env_config,
        config=KmsKeyConfig(
            alias_suffix="s3",
            description="KMS key for S3 bucket encryption",
        ),
    )

    rds_kms_key = PlatformKmsKey(
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

    # Database Stack - Aurora MySQL Serverless v2
    # Enable termination protection for production to prevent accidental deletion
    database_stack = DatabaseStack(
        app,
        f"{stack_prefix}-database",
        env_config=env_config,
        vpc=network_stack.vpc,
        storage_encryption_key=rds_kms_key.key,
        env=env_config.to_cdk_environment(),
        description="Aurora MySQL Serverless v2 with RDS Proxy",
        termination_protection=env_config.name.value == "prod",
    )
    database_stack.add_dependency(network_stack)
    database_stack.add_dependency(iam_stack)

    # Storage Stack - S3 buckets for datasets, models, checkpoints
    # Enable termination protection for production to prevent accidental deletion
    storage_stack = StorageStack(
        app,
        f"{stack_prefix}-storage",
        env_config=env_config,
        encryption_key=s3_kms_key.key,
        env=env_config.to_cdk_environment(),
        description="S3 buckets with lifecycle policies and KMS encryption",
        termination_protection=env_config.name.value == "prod",
    )
    storage_stack.add_dependency(iam_stack)

    # =========================================================================
    # Layer 3a: EKS Foundation Stack
    # =========================================================================

    # EKS Stack - EKS cluster foundation for HyperPod
    # This stack creates the EKS cluster and add-ons
    # After deployment, you need to install HyperPod Helm Chart before deploying HyperPod
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

    # SageMaker HyperPod Stack - HyperPod cluster attached to EKS
    # Note: EksStack automatically installs HyperPod Helm Chart via addHelmChart()
    # Prerequisites: Run ./scripts/setup_helm_chart.sh before first deployment
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

    # HyperPod Add-ons Stack - EKS add-ons for distributed training
    # T008d-1: Training Operator (PyTorchJob/TFJob CRD) + Task Governance (Kueue)
    # T008d-2: Observability (Prometheus + Grafana via Amazon Managed Service)
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
    # Layer 4: High-Performance Storage (FSx for Lustre)
    # =========================================================================

    # FSx for Lustre Stack - High-performance training data storage
    # Enable termination protection for production to prevent accidental deletion
    fsx_stack = FsxLustreStack(
        app,
        f"{stack_prefix}-fsx",
        env_config=env_config,
        vpc=network_stack.vpc,
        datasets_bucket=storage_stack.datasets_bucket,
        env=env_config.to_cdk_environment(),
        description="FSx for Lustre with S3 Data Repository Association",
        termination_protection=env_config.name.value == "prod",
    )
    fsx_stack.add_dependency(network_stack)
    fsx_stack.add_dependency(storage_stack)
    fsx_stack.add_dependency(eks_stack)  # Need EKS cluster for security group reference

    # =========================================================================
    # Layer 5: Network Ingress (ALB with TLS termination)
    # =========================================================================

    # ALB Stack - Application Load Balancer with HTTPS and WAF
    # Note: certificate_arn should be provided via context for production
    certificate_arn = app.node.try_get_context("certificate_arn")
    enable_waf = env_config.name.value == "prod"  # WAF enabled in production

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
    # CDK Nag - Security and best practices checks
    # =========================================================================

    # Apply AWS Solutions security checks for all environments
    # CDK Nag ensures consistent security posture across dev/staging/prod
    cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

    # Apply all Nag suppressions (centrally managed in utils/nag_suppressions.py)
    apply_nag_suppressions(app)

    return app


def main() -> None:
    """Main entry point."""
    app = create_app()
    app.synth()


if __name__ == "__main__":
    main()
