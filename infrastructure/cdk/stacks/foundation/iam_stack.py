"""
IAM Stack for AI Training Platform.

This stack creates IAM roles and policies following least-privilege principle:
- EKS node roles for GPU compute
- Service account roles for Kubernetes workloads (IRSA)
- Application roles for backend services
- Cross-account access policies (if needed)
"""

import aws_cdk as cdk
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct
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
        **kwargs,
    ) -> None:
        """Initialize the IAM Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config

        # Create IAM roles
        self._eks_node_role = self._create_eks_node_role()
        self._training_execution_role = self._create_training_execution_role()
        self._backend_service_role = self._create_backend_service_role()

        # Create shared policies
        self._create_shared_policies()

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
                # Allow EKS service accounts via IRSA
                iam.FederatedPrincipal(
                    federated=f"arn:aws:iam::{self.env_config.account}:oidc-provider/oidc.eks.{self.env_config.region}.amazonaws.com",
                    conditions={},
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
                resources=[
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-datasets/*",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-datasets",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-models/*",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-models",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-checkpoints/*",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-checkpoints",
                ],
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
                resources=[
                    f"arn:aws:sagemaker:{self.env_config.region}:{self.env_config.account}:cluster/*",
                    f"arn:aws:sagemaker:{self.env_config.region}:{self.env_config.account}:training-job/*",
                ],
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
                conditions={},
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
                resources=[
                    f"arn:aws:sagemaker:{self.env_config.region}:{self.env_config.account}:cluster/*",
                    f"arn:aws:sagemaker:{self.env_config.region}:{self.env_config.account}:training-job/*",
                ],
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
                resources=[
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-datasets",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-datasets/*",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-models",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-models/*",
                ],
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
                resources=[
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-datasets/*",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-models/*",
                    f"arn:aws:s3:::{self.env_config.resource_prefix}-checkpoints/*",
                ],
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
                    resources=["*"],
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
        """Get EKS node instance role."""
        return self._eks_node_role

    @property
    def training_execution_role(self) -> iam.Role:
        """Get training job execution role."""
        return self._training_execution_role

    @property
    def backend_service_role(self) -> iam.Role:
        """Get backend service role."""
        return self._backend_service_role

    @property
    def kms_usage_policy(self) -> iam.ManagedPolicy:
        """Get KMS usage policy."""
        return self._kms_usage_policy
