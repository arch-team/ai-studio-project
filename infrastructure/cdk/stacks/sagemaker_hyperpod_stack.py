"""
SageMaker HyperPod Stack for AI Training Platform.

This stack creates SageMaker HyperPod cluster attached to an existing EKS cluster:
- SageMaker HyperPod cluster with EKS orchestration
- Lifecycle scripts S3 bucket
- IAM execution role for HyperPod instances

Prerequisites:
1. EKS cluster must be deployed (EksStack)
2. HyperPod Helm Chart dependencies must be installed on the EKS cluster
   Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-install-packages-using-helm-chart.html
"""

import os

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import aws_sagemaker as sagemaker
from constructs import Construct

from config import EnvironmentConfig


class SagemakerHyperPodStack(cdk.Stack):
    """SageMaker HyperPod Stack.

    This stack creates:
    - S3 bucket for lifecycle scripts
    - IAM execution role for HyperPod instances
    - SageMaker HyperPod cluster with EKS orchestration

    Prerequisites:
    - EKS cluster must exist and have HyperPod Helm Chart dependencies installed

    Attributes:
        hyperpod_cluster: The SageMaker HyperPod cluster
        lifecycle_scripts_bucket: S3 bucket for lifecycle scripts
        hyperpod_execution_role: IAM execution role for HyperPod
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        eks_cluster: eks.ICluster,
        **kwargs,
    ) -> None:
        """Initialize the SageMaker HyperPod Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            vpc: VPC for the cluster
            eks_cluster: Existing EKS cluster with HyperPod dependencies installed
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._eks_cluster = eks_cluster

        # Create lifecycle scripts bucket
        self._lifecycle_scripts_bucket = self._create_lifecycle_scripts_bucket()

        # Create HyperPod execution role
        self._hyperpod_execution_role = self._create_hyperpod_execution_role()

        # Create HyperPod cluster
        self._hyperpod_cluster = self._create_hyperpod_cluster()

        # Create outputs
        self._create_outputs()

    def _create_lifecycle_scripts_bucket(self) -> s3.Bucket:
        """Create S3 bucket for HyperPod lifecycle scripts.

        The bucket stores on_create.sh and other lifecycle scripts
        that are executed during cluster provisioning.
        """
        bucket_name = f"sagemaker-{self.env_config.resource_prefix}-lifecycle"

        bucket = s3.Bucket(
            self,
            "LifecycleScriptsBucket",
            bucket_name=bucket_name,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=(
                cdk.RemovalPolicy.RETAIN
                if self.env_config.name.value == "prod"
                else cdk.RemovalPolicy.DESTROY
            ),
            auto_delete_objects=self.env_config.name.value != "prod",
        )

        cdk.Tags.of(bucket).add("Name", bucket_name)
        cdk.Tags.of(bucket).add("Purpose", "hyperpod-lifecycle-scripts")

        # Deploy lifecycle scripts to S3
        assets_path = os.path.join(os.path.dirname(__file__), "..", "assets", "lifecycle-scripts")
        s3deploy.BucketDeployment(
            self,
            "DeployLifecycleScripts",
            sources=[s3deploy.Source.asset(assets_path)],
            destination_bucket=bucket,
            destination_key_prefix="lifecycle-scripts",
        )

        return bucket

    def _create_hyperpod_execution_role(self) -> iam.Role:
        """Create IAM execution role for HyperPod cluster.

        This role is used by HyperPod instances to:
        - Access S3 for lifecycle scripts
        - Write CloudWatch logs
        - Communicate with EKS API
        - Access VPC/subnet information (required for EKS orchestration)
        """
        role = iam.Role(
            self,
            "HyperPodExecutionRole",
            role_name=f"{self.env_config.resource_prefix}-hyperpod-execution-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="Execution role for SageMaker HyperPod cluster instances",
        )

        # Attach the managed HyperPod policy
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSageMakerClusterInstanceRolePolicy"
            )
        )

        # Add S3 access for lifecycle scripts bucket
        self._lifecycle_scripts_bucket.grant_read(role)

        # Add EKS permissions for HyperPod to interact with the cluster
        role.add_to_policy(
            iam.PolicyStatement(
                sid="EksClusterAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "eks:DescribeCluster",
                    "eks:ListNodegroups",
                    "eks:DescribeNodegroup",
                ],
                resources=[self._eks_cluster.cluster_arn],
            )
        )

        # Add EC2 permissions required for EKS-orchestrated HyperPod
        # These permissions are required for HyperPod to retrieve subnet info
        # and manage network interfaces in customer VPC
        # Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html
        role.add_to_policy(
            iam.PolicyStatement(
                sid="Ec2NetworkAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:AssignPrivateIpAddresses",
                    "ec2:AttachNetworkInterface",
                    "ec2:CreateNetworkInterface",
                    "ec2:CreateNetworkInterfacePermission",
                    "ec2:DeleteNetworkInterface",
                    "ec2:DeleteNetworkInterfacePermission",
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceTypes",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DescribeTags",
                    "ec2:DescribeVpcs",
                    "ec2:DescribeDhcpOptions",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DetachNetworkInterface",
                    "ec2:ModifyNetworkInterfaceAttribute",
                    "ec2:UnassignPrivateIpAddresses",
                ],
                resources=["*"],
            )
        )

        # Add EC2 CreateTags permission for network interfaces
        role.add_to_policy(
            iam.PolicyStatement(
                sid="Ec2CreateTags",
                effect=iam.Effect.ALLOW,
                actions=["ec2:CreateTags"],
                resources=["arn:aws:ec2:*:*:network-interface/*"],
            )
        )

        # Add ECR permissions for pulling container images
        role.add_to_policy(
            iam.PolicyStatement(
                sid="EcrAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:BatchGetImage",
                    "ecr:GetAuthorizationToken",
                    "ecr:GetDownloadUrlForLayer",
                ],
                resources=["*"],
            )
        )

        # Add EKS Pod Identity permission (optional but recommended)
        role.add_to_policy(
            iam.PolicyStatement(
                sid="EksPodIdentity",
                effect=iam.Effect.ALLOW,
                actions=["eks-auth:AssumeRoleForPodIdentity"],
                resources=["*"],
            )
        )

        cdk.Tags.of(role).add(
            "Name", f"{self.env_config.resource_prefix}-hyperpod-execution-role"
        )

        return role

    def _create_hyperpod_cluster(self) -> sagemaker.CfnCluster:
        """Create SageMaker HyperPod cluster with EKS orchestration.

        Note: This creates the HyperPod cluster shell. Instance groups
        should be added via configuration or separate update operations
        based on workload requirements.
        """
        # Get private subnet IDs for the cluster
        private_subnet_ids = [
            subnet.subnet_id for subnet in self._vpc.private_subnets
        ]

        # Get security group IDs (use EKS cluster security group)
        security_group_ids = [self._eks_cluster.cluster_security_group_id]

        # Create minimal instance group for cluster validation
        # Note: HyperPod requires at least one instance group
        minimal_instance_group = sagemaker.CfnCluster.ClusterInstanceGroupProperty(
            instance_group_name="controller-group",
            instance_type="ml.m5.xlarge",  # Cost-effective for validation
            instance_count=1,
            life_cycle_config=sagemaker.CfnCluster.ClusterLifeCycleConfigProperty(
                source_s3_uri=f"s3://{self._lifecycle_scripts_bucket.bucket_name}/lifecycle-scripts",
                on_create="on_create.sh",
            ),
            execution_role=self._hyperpod_execution_role.role_arn,
        )

        # Create HyperPod cluster
        cluster = sagemaker.CfnCluster(
            self,
            "HyperPodCluster",
            cluster_name=f"{self.env_config.resource_prefix}-hyperpod",
            # Minimal instance group for validation
            instance_groups=[minimal_instance_group],
            # VPC configuration - same as EKS cluster
            vpc_config=sagemaker.CfnCluster.VpcConfigProperty(
                security_group_ids=security_group_ids,
                subnets=private_subnet_ids,
            ),
            # EKS orchestrator configuration
            orchestrator=sagemaker.CfnCluster.OrchestratorProperty(
                eks=sagemaker.CfnCluster.ClusterOrchestratorEksConfigProperty(
                    cluster_arn=self._eks_cluster.cluster_arn,
                )
            ),
            # Enable automatic node recovery
            node_recovery="Automatic",
            # Tags
            tags=[
                cdk.CfnTag(key="Name", value=f"{self.env_config.resource_prefix}-hyperpod"),
                cdk.CfnTag(key="Environment", value=self.env_config.name.value),
                cdk.CfnTag(key="ManagedBy", value="cdk"),
            ],
        )

        return cluster

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        # HyperPod Cluster outputs
        cdk.CfnOutput(
            self,
            "HyperPodClusterArn",
            value=self._hyperpod_cluster.attr_cluster_arn,
            description="SageMaker HyperPod cluster ARN",
            export_name=f"{self.env_config.resource_prefix}-hyperpod-arn",
        )

        # Lifecycle scripts bucket
        cdk.CfnOutput(
            self,
            "LifecycleScriptsBucketName",
            value=self._lifecycle_scripts_bucket.bucket_name,
            description="S3 bucket for HyperPod lifecycle scripts",
            export_name=f"{self.env_config.resource_prefix}-lifecycle-bucket",
        )

        # Execution role
        cdk.CfnOutput(
            self,
            "HyperPodExecutionRoleArn",
            value=self._hyperpod_execution_role.role_arn,
            description="HyperPod execution role ARN",
            export_name=f"{self.env_config.resource_prefix}-hyperpod-execution-role-arn",
        )

    @property
    def hyperpod_cluster(self) -> sagemaker.CfnCluster:
        """Get HyperPod cluster."""
        return self._hyperpod_cluster

    @property
    def lifecycle_scripts_bucket(self) -> s3.Bucket:
        """Get lifecycle scripts bucket."""
        return self._lifecycle_scripts_bucket

    @property
    def hyperpod_execution_role(self) -> iam.Role:
        """Get HyperPod execution role."""
        return self._hyperpod_execution_role
