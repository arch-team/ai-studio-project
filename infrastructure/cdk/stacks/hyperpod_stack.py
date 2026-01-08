"""
HyperPod Stack for AI Training Platform.

This stack creates SageMaker HyperPod with EKS orchestration:
- Amazon EKS cluster as the orchestrator
- HyperPod cluster with GPU instance groups
- EKS add-ons (EBS CSI, FSx CSI, VPC CNI)
- IAM roles for cluster operations

Architecture:
1. Create EKS cluster first (foundation)
2. Install required add-ons
3. Create HyperPod cluster pointing to EKS
"""

from typing import Optional

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sagemaker as sagemaker
from constructs import Construct

from config import EnvironmentConfig


class HyperPodStack(cdk.Stack):
    """SageMaker HyperPod Stack with EKS orchestration.

    This stack creates:
    - Amazon EKS cluster (K8s 1.32+)
    - Required EKS add-ons (EBS CSI, FSx CSI, VPC CNI)
    - SageMaker HyperPod cluster with EKS orchestration
    - Lifecycle scripts bucket
    - IAM roles for HyperPod operations

    Note: HyperPod instance groups will be created through a separate
    configuration or update operation after initial cluster creation.

    Attributes:
        eks_cluster: The EKS cluster for orchestration
        hyperpod_cluster: The SageMaker HyperPod cluster
        lifecycle_scripts_bucket: S3 bucket for lifecycle scripts
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        eks_node_role: iam.IRole,
        **kwargs,
    ) -> None:
        """Initialize the HyperPod Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            vpc: VPC for the cluster
            eks_node_role: IAM role for EKS nodes
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._eks_node_role = eks_node_role

        # Create lifecycle scripts bucket
        self._lifecycle_scripts_bucket = self._create_lifecycle_scripts_bucket()

        # Create EKS cluster
        self._eks_cluster = self._create_eks_cluster()

        # Install EKS add-ons
        self._install_eks_addons()

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

        return bucket

    def _create_eks_cluster(self) -> eks.Cluster:
        """Create Amazon EKS cluster for HyperPod orchestration.

        Creates EKS cluster with:
        - Kubernetes version 1.32
        - API and API_AND_CONFIG_MAP authentication modes
        - Private endpoint access
        - Cluster logging enabled
        """
        eks_config = self.env_config.eks

        # Create EKS cluster admin role
        cluster_admin_role = iam.Role(
            self,
            "ClusterAdminRole",
            role_name=f"{self.env_config.resource_prefix}-eks-admin-role",
            assumed_by=iam.AccountRootPrincipal(),
            description="Admin role for EKS cluster management",
        )

        # Create EKS cluster
        cluster = eks.Cluster(
            self,
            "EksCluster",
            cluster_name=f"{self.env_config.resource_prefix}-eks",
            version=eks.KubernetesVersion.of(eks_config.kubernetes_version),
            vpc=self._vpc,
            vpc_subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ],
            default_capacity=0,  # We'll manage node groups separately
            endpoint_access=eks.EndpointAccess.PRIVATE,
            masters_role=cluster_admin_role,
            # Cluster logging
            cluster_logging=[
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR,
                eks.ClusterLoggingTypes.CONTROLLER_MANAGER,
                eks.ClusterLoggingTypes.SCHEDULER,
            ],
            # Authentication mode for HyperPod compatibility
            authentication_mode=eks.AuthenticationMode.API_AND_CONFIG_MAP,
        )

        # Add cluster-level tags
        cdk.Tags.of(cluster).add("Name", f"{self.env_config.resource_prefix}-eks")
        cdk.Tags.of(cluster).add("kubernetes.io/cluster-type", "hyperpod-orchestrator")

        return cluster

    def _install_eks_addons(self) -> None:
        """Install required EKS add-ons for HyperPod.

        Required add-ons:
        - EBS CSI Driver (≥v1.28.0) - for persistent volumes
        - FSx CSI Driver (≥v1.9.0) - for Lustre storage
        - VPC CNI (≥v1.16.0) - for pod networking
        - CoreDNS - for DNS resolution
        - kube-proxy - for service networking
        """
        # Create IAM role for EBS CSI driver
        ebs_csi_role = iam.Role(
            self,
            "EbsCsiDriverRole",
            role_name=f"{self.env_config.resource_prefix}-ebs-csi-role",
            assumed_by=iam.FederatedPrincipal(
                federated=self._eks_cluster.open_id_connect_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        f"{self._eks_cluster.cluster_open_id_connect_issuer}:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa",
                        f"{self._eks_cluster.cluster_open_id_connect_issuer}:aud": "sts.amazonaws.com",
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )
        ebs_csi_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmazonEBSCSIDriverPolicy"
            )
        )

        # Create IAM role for FSx CSI driver
        fsx_csi_role = iam.Role(
            self,
            "FsxCsiDriverRole",
            role_name=f"{self.env_config.resource_prefix}-fsx-csi-role",
            assumed_by=iam.FederatedPrincipal(
                federated=self._eks_cluster.open_id_connect_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        f"{self._eks_cluster.cluster_open_id_connect_issuer}:sub": "system:serviceaccount:kube-system:fsx-csi-controller-sa",
                        f"{self._eks_cluster.cluster_open_id_connect_issuer}:aud": "sts.amazonaws.com",
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )
        fsx_csi_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmazonFSxCSIDriverPolicy"
            )
        )

        # Install EBS CSI Driver add-on
        eks.CfnAddon(
            self,
            "EbsCsiAddon",
            addon_name="aws-ebs-csi-driver",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.28.0-eksbuild.1",
            service_account_role_arn=ebs_csi_role.role_arn,
            resolve_conflicts="OVERWRITE",
        )

        # Install FSx CSI Driver add-on
        eks.CfnAddon(
            self,
            "FsxCsiAddon",
            addon_name="aws-fsx-csi-driver",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.9.0-eksbuild.1",
            service_account_role_arn=fsx_csi_role.role_arn,
            resolve_conflicts="OVERWRITE",
        )

        # Install VPC CNI add-on
        eks.CfnAddon(
            self,
            "VpcCniAddon",
            addon_name="vpc-cni",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.18.3-eksbuild.1",
            resolve_conflicts="OVERWRITE",
            configuration_values=cdk.Fn.to_json_string(
                {
                    "env": {
                        # Enable prefix delegation for more IPs per node
                        "ENABLE_PREFIX_DELEGATION": "true",
                        "WARM_PREFIX_TARGET": "1",
                    }
                }
            ),
        )

        # Install CoreDNS add-on
        eks.CfnAddon(
            self,
            "CoreDnsAddon",
            addon_name="coredns",
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
        )

        # Install kube-proxy add-on
        eks.CfnAddon(
            self,
            "KubeProxyAddon",
            addon_name="kube-proxy",
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
        )

    def _create_hyperpod_execution_role(self) -> iam.Role:
        """Create IAM execution role for HyperPod cluster.

        This role is used by HyperPod instances to:
        - Access S3 for lifecycle scripts
        - Write CloudWatch logs
        - Communicate with EKS API
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

        # Create HyperPod cluster
        cluster = sagemaker.CfnCluster(
            self,
            "HyperPodCluster",
            cluster_name=f"{self.env_config.resource_prefix}-hyperpod",
            # Instance groups will be configured separately
            # Start with empty groups - actual GPU instances added via update
            instance_groups=[],
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

        # Add explicit dependency on EKS cluster
        cluster.node.add_dependency(self._eks_cluster)

        return cluster

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        # EKS Cluster outputs
        cdk.CfnOutput(
            self,
            "EksClusterName",
            value=self._eks_cluster.cluster_name,
            description="EKS cluster name",
            export_name=f"{self.env_config.resource_prefix}-eks-cluster-name",
        )

        cdk.CfnOutput(
            self,
            "EksClusterArn",
            value=self._eks_cluster.cluster_arn,
            description="EKS cluster ARN",
            export_name=f"{self.env_config.resource_prefix}-eks-cluster-arn",
        )

        cdk.CfnOutput(
            self,
            "EksClusterEndpoint",
            value=self._eks_cluster.cluster_endpoint,
            description="EKS cluster API endpoint",
            export_name=f"{self.env_config.resource_prefix}-eks-endpoint",
        )

        cdk.CfnOutput(
            self,
            "EksClusterSecurityGroupId",
            value=self._eks_cluster.cluster_security_group_id,
            description="EKS cluster security group ID",
            export_name=f"{self.env_config.resource_prefix}-eks-sg-id",
        )

        cdk.CfnOutput(
            self,
            "EksOidcProviderArn",
            value=self._eks_cluster.open_id_connect_provider.open_id_connect_provider_arn,
            description="EKS OIDC provider ARN for IRSA",
            export_name=f"{self.env_config.resource_prefix}-eks-oidc-arn",
        )

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
    def eks_cluster(self) -> eks.Cluster:
        """Get EKS cluster."""
        return self._eks_cluster

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

    def get_kubeconfig_command(self) -> str:
        """Get command to configure kubectl for cluster access."""
        return (
            f"aws eks update-kubeconfig "
            f"--name {self._eks_cluster.cluster_name} "
            f"--region {self.env_config.region}"
        )
