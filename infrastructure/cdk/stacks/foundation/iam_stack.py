"""
IAM Stack for AI Training Platform.

This stack creates IAM roles and policies following least-privilege principle:
- EKS node roles for GPU compute
- Service account roles for Kubernetes workloads (IRSA)
- Application roles for backend services
- Cross-account access policies (if needed)
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct
from utils.nag_suppressions import apply_resource_suppression
from utils.outputs import create_output


class IamStack(cdk.Stack):
    """IAM Roles and Policies Stack following least-privilege principle.

    This stack creates:
    - EKS node instance role (for EC2 nodes in the cluster)
    - Training job execution role (for HyperPod training jobs)
    - Backend service role (for FastAPI application)
    - S3 access policies for storage operations

    All roles follow AWS Well-Architected security best practices:
    - Least privilege permissions
    - Role separation by function
    - Session policies for temporary access
    - Condition keys for enhanced security

    Attributes:
        eks_node_role: IAM role for EKS worker nodes
        training_execution_role: IAM role for training job execution
        backend_service_role: IAM role for backend application
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        kms_key_arns: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        # kms_key_arns: 为 None 时使用 account 级别 ARN 模式
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        # 默认限制为当前 account 下的 KMS Key
        self._kms_key_arns = kms_key_arns or [
            f"arn:aws:kms:{env_config.region}:{env_config.account}:key/*"
        ]

        # Create IAM roles
        self._eks_node_role = self._create_eks_node_role()
        self._training_execution_role = self._create_training_execution_role()
        self._backend_service_role = self._create_backend_service_role()

        # Create shared policies
        self._create_shared_policies()

        # 资源级 Nag 抑制 (替代 Stack 级 IAM5 抑制)
        self._apply_nag_suppressions()

        # Export outputs
        self._create_outputs()

    def _create_eks_node_role(self) -> iam.Role:
        """Create IAM role for EKS worker nodes.

        This role is assumed by EC2 instances running as EKS nodes.
        Includes permissions for:
        - EKS worker node operations
        - ECR image pulling
        - CloudWatch logging
        - SSM for node management
        """
        role = iam.Role(
            self,
            "EksNodeRole",
            role_name=f"{self.env_config.resource_prefix}-eks-node-role",
            description="IAM role for EKS worker nodes",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            # Session duration for long-running nodes
            max_session_duration=cdk.Duration.hours(12),
        )

        # Attach AWS managed policies for EKS nodes
        managed_policies = [
            "AmazonEKSWorkerNodePolicy",
            "AmazonEKS_CNI_Policy",
            "AmazonEC2ContainerRegistryReadOnly",
            "AmazonSSMManagedInstanceCore",  # For Systems Manager access
        ]

        for policy_name in managed_policies:
            role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(policy_name)
            )

        # Add CloudWatch Logs permissions
        role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogsPermissions",
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                ],
                resources=[
                    f"arn:aws:logs:{self.env_config.region}:{self.env_config.account}:log-group:/aws/eks/*",
                    f"arn:aws:logs:{self.env_config.region}:{self.env_config.account}:log-group:/ai-platform/*",
                ],
            )
        )

        # Add CloudWatch Metrics permissions (for HyperPod Observability)
        role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchMetricsPermissions",
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                    "cloudwatch:GetMetricData",
                    "cloudwatch:GetMetricStatistics",
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": [
                            "AWS/EKS",
                            "ContainerInsights",
                            "AI-Platform",
                        ]
                    }
                },
            )
        )

        cdk.Tags.of(role).add(
            "Name", f"{self.env_config.resource_prefix}-eks-node-role"
        )

        return role

    def _s3_bucket_arns(self, *bucket_suffixes: str) -> list[str]:
        """生成 S3 bucket 和 object 的 ARN 列表。

        Args:
            *bucket_suffixes: bucket 名称后缀列表 (如 "datasets", "models")

        Returns:
            包含 bucket ARN 和 object ARN 的列表
        """
        arns: list[str] = []
        for suffix in bucket_suffixes:
            bucket_name = f"{self.env_config.resource_prefix}-{suffix}"
            arns.append(f"arn:aws:s3:::{bucket_name}")
            arns.append(f"arn:aws:s3:::{bucket_name}/*")
        return arns

    def _sagemaker_resource_arns(self, *resource_types: str) -> list[str]:
        """生成 SageMaker 资源的 ARN 列表。

        Args:
            *resource_types: SageMaker 资源类型 (如 "cluster", "training-job")

        Returns:
            SageMaker 资源 ARN 列表 (每个类型使用通配符 /*)
        """
        prefix = f"arn:aws:sagemaker:{self.env_config.region}:{self.env_config.account}"
        return [f"{prefix}:{rt}/*" for rt in resource_types]

    def _create_training_execution_role(self) -> iam.Role:
        """Create IAM role for training job execution.

        This role is assumed by training jobs via IRSA (IAM Roles for Service Accounts).
        Includes permissions for:
        - S3 access for datasets, models, checkpoints
        - SageMaker HyperPod operations
        - CloudWatch metrics publishing
        - FSx for Lustre access
        """
        role = iam.Role(
            self,
            "TrainingExecutionRole",
            role_name=f"{self.env_config.resource_prefix}-training-execution-role",
            description="IAM role for HyperPod training job execution",
            assumed_by=iam.CompositePrincipal(
                # Allow EKS service accounts via IRSA (with OIDC condition to prevent Confused Deputy)
                iam.FederatedPrincipal(
                    federated=f"arn:aws:iam::{self.env_config.account}:oidc-provider/oidc.eks.{self.env_config.region}.amazonaws.com",
                    conditions={
                        "StringEquals": {
                            f"oidc.eks.{self.env_config.region}.amazonaws.com:sub":
                                "system:serviceaccount:training-jobs:training-execution-sa",
                            f"oidc.eks.{self.env_config.region}.amazonaws.com:aud":
                                "sts.amazonaws.com",
                        }
                    },
                    assume_role_action="sts:AssumeRoleWithWebIdentity",
                ),
                # Allow SageMaker service
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            max_session_duration=cdk.Duration.hours(12),
        )

        # S3 permissions for training data access
        role.add_to_policy(
            iam.PolicyStatement(
                sid="S3TrainingDataAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                    "s3:ListBucketVersions",
                    "s3:PutObject",
                    "s3:DeleteObject",
                ],
                resources=self._s3_bucket_arns("datasets", "models", "checkpoints"),
            )
        )

        # SageMaker permissions for HyperPod operations
        role.add_to_policy(
            iam.PolicyStatement(
                sid="SageMakerHyperPodAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "sagemaker:DescribeCluster",
                    "sagemaker:ListClusterNodes",
                    "sagemaker:UpdateCluster",
                    # Training job operations
                    "sagemaker:CreateTrainingJob",
                    "sagemaker:DescribeTrainingJob",
                    "sagemaker:StopTrainingJob",
                    "sagemaker:ListTrainingJobs",
                ],
                resources=self._sagemaker_resource_arns("cluster", "training-job"),
            )
        )

        # CloudWatch metrics for training monitoring
        role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchMetricsTraining",
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {"cloudwatch:namespace": ["AI-Platform/Training"]}
                },
            )
        )

        # FSx for Lustre access
        role.add_to_policy(
            iam.PolicyStatement(
                sid="FSxLustreAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "fsx:DescribeFileSystems",
                    "fsx:DescribeDataRepositoryAssociations",
                ],
                resources=[
                    f"arn:aws:fsx:{self.env_config.region}:{self.env_config.account}:file-system/*",
                ],
            )
        )

        cdk.Tags.of(role).add(
            "Name", f"{self.env_config.resource_prefix}-training-execution-role"
        )

        return role

    def _create_backend_service_role(self) -> iam.Role:
        """Create IAM role for backend FastAPI application.

        This role is assumed by the backend service pods via IRSA.
        Includes permissions for:
        - SageMaker HyperPod API access
        - S3 metadata operations
        - Secrets Manager for database credentials
        - CloudWatch for application logging
        """
        role = iam.Role(
            self,
            "BackendServiceRole",
            role_name=f"{self.env_config.resource_prefix}-backend-service-role",
            description="IAM role for backend FastAPI application",
            assumed_by=iam.FederatedPrincipal(
                federated=f"arn:aws:iam::{self.env_config.account}:oidc-provider/oidc.eks.{self.env_config.region}.amazonaws.com",
                conditions={
                    "StringEquals": {
                        f"oidc.eks.{self.env_config.region}.amazonaws.com:sub":
                            "system:serviceaccount:backend:backend-service-sa",
                        f"oidc.eks.{self.env_config.region}.amazonaws.com:aud":
                            "sts.amazonaws.com",
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            max_session_duration=cdk.Duration.hours(12),
        )

        # SageMaker HyperPod read permissions (for status queries)
        role.add_to_policy(
            iam.PolicyStatement(
                sid="SageMakerReadAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "sagemaker:DescribeCluster",
                    "sagemaker:ListClusterNodes",
                    "sagemaker:DescribeTrainingJob",
                    "sagemaker:ListTrainingJobs",
                ],
                resources=self._sagemaker_resource_arns("cluster", "training-job"),
            )
        )

        # S3 metadata operations (for dataset/model management)
        role.add_to_policy(
            iam.PolicyStatement(
                sid="S3MetadataAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:GetObject",
                    "s3:GetObjectAttributes",
                    "s3:HeadObject",
                ],
                resources=self._s3_bucket_arns("datasets", "models"),
            )
        )

        # Presigned URL generation permissions
        role.add_to_policy(
            iam.PolicyStatement(
                sid="S3PresignedUrlAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                ],
                resources=self._s3_bucket_arns("datasets", "models", "checkpoints"),
            )
        )

        # Secrets Manager for database credentials
        role.add_to_policy(
            iam.PolicyStatement(
                sid="SecretsManagerAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.env_config.region}:{self.env_config.account}:secret:{self.env_config.resource_prefix}/*",
                ],
            )
        )

        # CloudWatch Logs for application logging
        role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogsAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{self.env_config.region}:{self.env_config.account}:log-group:/ai-platform/backend:*",
                ],
            )
        )

        cdk.Tags.of(role).add(
            "Name", f"{self.env_config.resource_prefix}-backend-service-role"
        )

        return role

    def _apply_nag_suppressions(self) -> None:
        """为已知合理的通配符权限资源添加 Nag 抑制 (资源级)。"""
        # EKS Node Role: CloudWatch Metrics 使用 resources=["*"] + namespace 条件约束
        apply_resource_suppression(
            self._eks_node_role,
            "AwsSolutions-IAM5",
            "CloudWatch PutMetricData requires resources=[*], scoped by cloudwatch:namespace condition",
        )
        # Training Execution Role: CloudWatch Metrics 同上
        apply_resource_suppression(
            self._training_execution_role,
            "AwsSolutions-IAM5",
            "CloudWatch PutMetricData requires resources=[*], scoped by cloudwatch:namespace condition",
        )
        # KMS Usage Policy: resources 使用 account key pattern + kms:ViaService 条件
        apply_resource_suppression(
            self._kms_usage_policy,
            "AwsSolutions-IAM5",
            "KMS key ARN pattern limited to current account, scoped by kms:ViaService condition for S3",
        )

    def _create_shared_policies(self) -> None:
        """Create shared IAM policies that can be attached to multiple roles."""
        # KMS key usage policy (for S3 encryption)
        self._kms_usage_policy = iam.ManagedPolicy(
            self,
            "KmsUsagePolicy",
            managed_policy_name=f"{self.env_config.resource_prefix}-kms-usage-policy",
            description="Policy for using KMS keys for S3 encryption",
            statements=[
                iam.PolicyStatement(
                    sid="KmsKeyUsage",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        "kms:GenerateDataKey",
                        "kms:DescribeKey",
                    ],
                    resources=self._kms_key_arns,
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"s3.{self.env_config.region}.amazonaws.com"
                            ]
                        }
                    },
                )
            ],
        )

        # Attach KMS policy to roles that need S3 access
        self._training_execution_role.add_managed_policy(self._kms_usage_policy)
        self._backend_service_role.add_managed_policy(self._kms_usage_policy)

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        create_output(
            self,
            "EksNodeRoleArn",
            self._eks_node_role.role_arn,
            "ARN of EKS node instance role",
        )
        create_output(
            self,
            "EksNodeRoleName",
            self._eks_node_role.role_name,
            "Name of EKS node instance role",
        )
        create_output(
            self,
            "TrainingExecutionRoleArn",
            self._training_execution_role.role_arn,
            "ARN of training job execution role",
        )
        create_output(
            self,
            "BackendServiceRoleArn",
            self._backend_service_role.role_arn,
            "ARN of backend service role",
        )

    @property
    def eks_node_role(self) -> iam.Role:
        return self._eks_node_role

    @property
    def training_execution_role(self) -> iam.Role:
        return self._training_execution_role

    @property
    def backend_service_role(self) -> iam.Role:
        return self._backend_service_role

    @property
    def kms_usage_policy(self) -> iam.ManagedPolicy:
        return self._kms_usage_policy
