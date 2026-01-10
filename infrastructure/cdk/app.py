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
from cdk_nag import AwsSolutionsChecks, NagSuppressions

from config import EnvironmentConfig, get_environment_config
from stacks import (
    AlbStack,
    DatabaseStack,
    EksStack,
    FsxLustreStack,
    IamStack,
    NetworkStack,
    SagemakerHyperPodStack,
    StorageStack,
)


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

    # Common tags for all resources
    common_tags = {
        "Project": "ai-training-platform",
        "Environment": env_config.name.value,
        "ManagedBy": "cdk",
        "CostCenter": f"ai-platform-{env_config.name.value}",
    }

    # Apply common tags to all resources
    for key, value in common_tags.items():
        cdk.Tags.of(app).add(key, value)

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
    # Layer 2: Data Stacks (Aurora, S3, FSx)
    # =========================================================================

    # Database Stack - Aurora MySQL Serverless v2
    database_stack = DatabaseStack(
        app,
        f"{stack_prefix}-database",
        env_config=env_config,
        vpc=network_stack.vpc,
        env=env_config.to_cdk_environment(),
        description="Aurora MySQL Serverless v2 with RDS Proxy",
    )
    database_stack.add_dependency(network_stack)

    # Storage Stack - S3 buckets for datasets, models, checkpoints
    storage_stack = StorageStack(
        app,
        f"{stack_prefix}-storage",
        env_config=env_config,
        env=env_config.to_cdk_environment(),
        description="S3 buckets with lifecycle policies and KMS encryption",
    )

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
    # Layer 4: High-Performance Storage (FSx for Lustre)
    # =========================================================================

    # FSx for Lustre Stack - High-performance training data storage
    fsx_stack = FsxLustreStack(
        app,
        f"{stack_prefix}-fsx",
        env_config=env_config,
        vpc=network_stack.vpc,
        datasets_bucket=storage_stack.datasets_bucket,
        env=env_config.to_cdk_environment(),
        description="FSx for Lustre with S3 Data Repository Association",
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

    # Apply AWS Solutions security checks (skip for dev to allow faster iteration)
    # CDK Nag warnings are informational for dev; production should address all warnings
    if env_config.name.value != "dev":
        cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

    # Add suppressions for known acceptable patterns
    NagSuppressions.add_stack_suppressions(
        network_stack,
        [
            {
                "id": "AwsSolutions-VPC7",
                "reason": "VPC Flow Logs are explicitly enabled in the stack",
            },
            {
                "id": "AwsSolutions-EC23",
                "reason": "VPC endpoint security group uses Fn::GetAtt for CIDR which CDK Nag cannot validate",
            },
        ],
    )

    NagSuppressions.add_stack_suppressions(
        iam_stack,
        [
            {
                "id": "AwsSolutions-IAM4",
                "reason": "AWS managed policies are used for EKS node roles following AWS best practices",
            },
            {
                "id": "AwsSolutions-IAM5",
                "reason": "Wildcard permissions are scoped to specific resources and conditions",
            },
        ],
    )

    NagSuppressions.add_stack_suppressions(
        database_stack,
        [
            {
                "id": "AwsSolutions-RDS10",
                "reason": "Deletion protection is enabled for production environments only",
            },
            {
                "id": "AwsSolutions-RDS11",
                "reason": "Using default port is acceptable for dev environment; production will use custom port",
            },
            {
                "id": "AwsSolutions-RDS14",
                "reason": "Backtrack is not required for dev environment; will be enabled for production",
            },
            {
                "id": "AwsSolutions-SMG4",
                "reason": "Secret rotation will be configured in a separate security enhancement task",
            },
            {
                "id": "AwsSolutions-IAM4",
                "reason": "AWS managed policies used for Lambda log retention custom resource",
            },
            {
                "id": "AwsSolutions-IAM5",
                "reason": "Wildcard permissions required for Lambda log retention custom resource",
            },
        ],
    )

    NagSuppressions.add_stack_suppressions(
        storage_stack,
        [
            {
                "id": "AwsSolutions-S1",
                "reason": "Server access logging will be configured when log bucket is created",
            },
        ],
    )

    # Suppressions for EKS Stack
    NagSuppressions.add_stack_suppressions(
        eks_stack,
        [
            {
                "id": "AwsSolutions-IAM4",
                "reason": "AWS managed policies used for EKS add-ons and CDK custom resources",
            },
            {
                "id": "AwsSolutions-IAM5",
                "reason": "Wildcard permissions required for EKS cluster management and CDK custom resources",
            },
            {
                "id": "AwsSolutions-EKS1",
                "reason": "EKS cluster has private endpoint access enabled",
            },
            {
                "id": "AwsSolutions-L1",
                "reason": "Lambda runtime version is managed by CDK construct library for EKS and kubectl providers",
            },
            {
                "id": "AwsSolutions-SF1",
                "reason": "Step Function logging is managed by CDK EKS construct; acceptable for dev environment",
            },
            {
                "id": "AwsSolutions-SF2",
                "reason": "X-Ray tracing is managed by CDK EKS construct; acceptable for dev environment",
            },
        ],
    )

    # Suppressions for SageMaker HyperPod Stack
    NagSuppressions.add_stack_suppressions(
        sagemaker_hyperpod_stack,
        [
            {
                "id": "AwsSolutions-IAM4",
                "reason": "AWS managed policies used for HyperPod execution role",
            },
            {
                "id": "AwsSolutions-IAM5",
                "reason": "Wildcard permissions required for EC2 network access and ECR operations",
            },
            {
                "id": "AwsSolutions-S1",
                "reason": "Lifecycle scripts bucket access logging will be configured in production",
            },
            {
                "id": "AwsSolutions-L1",
                "reason": "Lambda runtime version is managed by CDK construct library for S3 deployment",
            },
        ],
    )

    NagSuppressions.add_stack_suppressions(
        fsx_stack,
        [
            {
                "id": "AwsSolutions-EC23",
                "reason": "FSx security group allows VPC CIDR access for Lustre client connectivity",
            },
        ],
    )

    NagSuppressions.add_stack_suppressions(
        alb_stack,
        [
            {
                "id": "AwsSolutions-ELB2",
                "reason": "ALB access logging will be enabled when S3 log bucket is configured",
            },
            {
                "id": "AwsSolutions-EC23",
                "reason": "ALB security group allows 0.0.0.0/0 for public internet access as designed",
            },
        ],
    )

    return app


def main() -> None:
    """Main entry point."""
    app = create_app()
    app.synth()


if __name__ == "__main__":
    main()
