"""IAM Stack — 最小权限 IAM 角色和策略。

EKS 节点角色 / 训练执行角色 / 后端服务角色 / KMS 使用策略。
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct
from utils.nag_suppressions import apply_resource_suppression
from utils.outputs import create_output


class IamStack(cdk.Stack):
    """IAM Stack — 最小权限角色和策略。"""

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

        self._eks_node_role = self._create_eks_node_role()
        self._training_execution_role = self._create_training_execution_role()
        self._backend_service_role = self._create_backend_service_role()
        self._create_shared_policies()

        # 资源级 Nag 抑制 (替代 Stack 级 IAM5 抑制)
        self._apply_nag_suppressions()

        self._create_outputs()

    def _create_eks_node_role(self) -> iam.Role:
        """创建 EKS 工作节点 IAM 角色 (ECR/CloudWatch/SSM)。"""
        role = iam.Role(
            self,
            "EksNodeRole",
            role_name=f"{self.env_config.resource_prefix}-eks-node-role",
            description="IAM role for EKS worker nodes",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            max_session_duration=cdk.Duration.hours(12),
        )

        managed_policies = [
            "AmazonEKSWorkerNodePolicy",
            "AmazonEKS_CNI_Policy",
            "AmazonEC2ContainerRegistryReadOnly",
            "AmazonSSMManagedInstanceCore",
        ]

        for policy_name in managed_policies:
            role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(policy_name)
            )

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
        """创建训练任务执行角色 (IRSA: S3/SageMaker/CloudWatch/FSx)。"""
        role = iam.Role(
            self,
            "TrainingExecutionRole",
            role_name=f"{self.env_config.resource_prefix}-training-execution-role",
            description="IAM role for HyperPod training job execution",
            assumed_by=iam.CompositePrincipal(
                # IRSA: OIDC 条件防止 Confused Deputy 攻击
                iam.FederatedPrincipal(
                    federated=f"arn:aws:iam::{self.env_config.account}:oidc-provider/oidc.eks.{self.env_config.region}.amazonaws.com",
                    conditions={
                        "StringEquals": {
                            f"oidc.eks.{self.env_config.region}.amazonaws.com:sub": "system:serviceaccount:training-jobs:training-execution-sa",
                            f"oidc.eks.{self.env_config.region}.amazonaws.com:aud": "sts.amazonaws.com",
                        }
                    },
                    assume_role_action="sts:AssumeRoleWithWebIdentity",
                ),
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            max_session_duration=cdk.Duration.hours(12),
        )

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

        role.add_to_policy(
            iam.PolicyStatement(
                sid="SageMakerHyperPodAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "sagemaker:DescribeCluster",
                    "sagemaker:ListClusterNodes",
                    "sagemaker:UpdateCluster",
                    "sagemaker:CreateTrainingJob",
                    "sagemaker:DescribeTrainingJob",
                    "sagemaker:StopTrainingJob",
                    "sagemaker:ListTrainingJobs",
                ],
                resources=self._sagemaker_resource_arns("cluster", "training-job"),
            )
        )

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
        """创建后端 FastAPI 服务角色 (IRSA: SageMaker/S3/SecretsManager/CloudWatch)。"""
        role = iam.Role(
            self,
            "BackendServiceRole",
            role_name=f"{self.env_config.resource_prefix}-backend-service-role",
            description="IAM role for backend FastAPI application",
            assumed_by=iam.FederatedPrincipal(
                federated=f"arn:aws:iam::{self.env_config.account}:oidc-provider/oidc.eks.{self.env_config.region}.amazonaws.com",
                conditions={
                    "StringEquals": {
                        f"oidc.eks.{self.env_config.region}.amazonaws.com:sub": "system:serviceaccount:ai-platform:backend-service-sa",
                        f"oidc.eks.{self.env_config.region}.amazonaws.com:aud": "sts.amazonaws.com",
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            max_session_duration=cdk.Duration.hours(12),
        )

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
        """创建可复用的 IAM 策略 (KMS 密钥使用)。"""
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

        self._training_execution_role.add_managed_policy(self._kms_usage_policy)
        self._backend_service_role.add_managed_policy(self._kms_usage_policy)

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出。"""
        outputs = [
            (
                "EksNodeRoleArn",
                self._eks_node_role.role_arn,
                "ARN of EKS node instance role",
            ),
            (
                "EksNodeRoleName",
                self._eks_node_role.role_name,
                "Name of EKS node instance role",
            ),
            (
                "TrainingExecutionRoleArn",
                self._training_execution_role.role_arn,
                "ARN of training job execution role",
            ),
            (
                "BackendServiceRoleArn",
                self._backend_service_role.role_arn,
                "ARN of backend service role",
            ),
        ]
        for output_id, value, description in outputs:
            create_output(self, output_id, value, description)

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
