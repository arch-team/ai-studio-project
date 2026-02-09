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

from config import EnvironmentConfig
from config.constants import (
    INSTANCE_GROUPS,
    MANAGED_POLICIES,
    SAGEMAKER_INSTANCES,
    TAG_KEYS,
)
from constructs import Construct
from utils.iam_helpers import (
    add_policy_statement,
    add_policy_statements,
    create_tagged_role,
)
from utils.outputs import create_output
from utils.tagging import create_cfn_tags


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
            removal_policy=self.env_config.protection.removal_policy,
            auto_delete_objects=not self.env_config.protection.retain_on_delete,
        )

        cdk.Tags.of(bucket).add(TAG_KEYS.NAME, bucket_name)
        cdk.Tags.of(bucket).add("Purpose", "hyperpod-lifecycle-scripts")

        # Deploy lifecycle scripts to S3
        # File location: stacks/compute/ -> assets/ (at cdk root)
        assets_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "lifecycle-scripts"
        )
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
        role = create_tagged_role(
            scope=self,
            construct_id="HyperPodExecutionRole",
            env_config=self.env_config,
            role_name_suffix="hyperpod-execution-role",
            description="Execution role for SageMaker HyperPod cluster instances",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[MANAGED_POLICIES.SAGEMAKER_CLUSTER_INSTANCE],
        )

        # Add S3 access for lifecycle scripts bucket
        self._lifecycle_scripts_bucket.grant_read(role)

        # Add EKS permissions for HyperPod to interact with the cluster
        add_policy_statement(
            role,
            sid="EksClusterAccess",
            actions=[
                "eks:DescribeCluster",
                "eks:ListNodegroups",
                "eks:DescribeNodegroup",
            ],
            resources=[self._eks_cluster.cluster_arn],
        )

        # Add EC2 permissions required for EKS-orchestrated HyperPod
        # Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html
        ec2_network_actions = [
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
        ]

        # Add remaining permissions using batch helper
        add_policy_statements(
            role,
            [
                ("Ec2NetworkAccess", ec2_network_actions, ["*"]),
                (
                    "Ec2CreateTags",
                    ["ec2:CreateTags"],
                    ["arn:aws:ec2:*:*:network-interface/*"],
                ),
                (
                    "EcrAccess",
                    [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetAuthorizationToken",
                        "ecr:GetDownloadUrlForLayer",
                    ],
                    ["*"],
                ),
                ("EksPodIdentity", ["eks-auth:AssumeRoleForPodIdentity"], ["*"]),
            ],
        )

        return role

    def _create_instance_group(
        self,
        name: str,
        instance_type: str,
        instance_count: int = 1,
    ) -> sagemaker.CfnCluster.ClusterInstanceGroupProperty:
        """Create a HyperPod instance group configuration.

        Args:
            name: Instance group name
            instance_type: SageMaker instance type (e.g., ml.m5.xlarge)
            instance_count: Number of instances

        Returns:
            ClusterInstanceGroupProperty for the instance group
        """
        return sagemaker.CfnCluster.ClusterInstanceGroupProperty(
            instance_group_name=name,
            instance_type=instance_type,
            instance_count=instance_count,
            life_cycle_config=sagemaker.CfnCluster.ClusterLifeCycleConfigProperty(
                source_s3_uri=f"s3://{self._lifecycle_scripts_bucket.bucket_name}/lifecycle-scripts",
                on_create="on_create.sh",
            ),
            execution_role=self._hyperpod_execution_role.role_arn,
        )

    def _create_hyperpod_cluster(self) -> sagemaker.CfnCluster:
        """Create SageMaker HyperPod cluster with EKS orchestration.

        Note: This creates the HyperPod cluster shell. Instance groups
        should be added via configuration or separate update operations
        based on workload requirements.
        """
        # Get private subnet IDs for the cluster
        private_subnet_ids = [subnet.subnet_id for subnet in self._vpc.private_subnets]

        # Get security group IDs (use EKS cluster security group)
        security_group_ids = [self._eks_cluster.cluster_security_group_id]

        # Create instance groups using helper method
        instance_groups = [
            self._create_instance_group(
                name=INSTANCE_GROUPS.CONTROLLER,
                instance_type=SAGEMAKER_INSTANCES.CONTROLLER,
                instance_count=1,
            ),
            # ml.m5.4xlarge supports ~234 pods (8 ENIs × 30 IPs per ENI)
            self._create_instance_group(
                name=INSTANCE_GROUPS.SYSTEM,
                instance_type=SAGEMAKER_INSTANCES.SYSTEM,
                instance_count=1,
            ),
        ]

        # Add GPU training instance group if enabled
        gpu_config = self.env_config.eks.gpu_instance_group
        if gpu_config.enabled:
            instance_groups.append(
                self._create_instance_group(
                    name=INSTANCE_GROUPS.GPU_TRAINING,
                    instance_type=SAGEMAKER_INSTANCES.GPU_G5_2XLARGE,
                    instance_count=gpu_config.instance_count,
                )
            )

        # Create HyperPod cluster with standard tags + SageMaker=true
        cluster = sagemaker.CfnCluster(
            self,
            "HyperPodCluster",
            cluster_name=f"{self.env_config.resource_prefix}-hyperpod",
            instance_groups=instance_groups,
            vpc_config=sagemaker.CfnCluster.VpcConfigProperty(
                security_group_ids=security_group_ids,
                subnets=private_subnet_ids,
            ),
            orchestrator=sagemaker.CfnCluster.OrchestratorProperty(
                eks=sagemaker.CfnCluster.ClusterOrchestratorEksConfigProperty(
                    cluster_arn=self._eks_cluster.cluster_arn,
                )
            ),
            node_recovery="Automatic",
            # SageMaker=true is required by AmazonSageMakerHyperPodTrainingOperatorAccess policy
            tags=create_cfn_tags(
                self.env_config,
                "hyperpod",
                additional_tags={TAG_KEYS.SAGEMAKER: "true"},
            ),
        )

        # Ensure HyperPod cluster is created after the IAM role
        cluster.node.add_dependency(self._hyperpod_execution_role)

        return cluster

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        create_output(
            self,
            "HyperPodClusterArn",
            self._hyperpod_cluster.attr_cluster_arn,
            "SageMaker HyperPod cluster ARN",
            export_name=f"{self.env_config.resource_prefix}-hyperpod-arn",
        )

        create_output(
            self,
            "LifecycleScriptsBucketName",
            self._lifecycle_scripts_bucket.bucket_name,
            "S3 bucket for HyperPod lifecycle scripts",
            export_name=f"{self.env_config.resource_prefix}-lifecycle-bucket",
        )

        create_output(
            self,
            "HyperPodExecutionRoleArn",
            self._hyperpod_execution_role.role_arn,
            "HyperPod execution role ARN",
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
