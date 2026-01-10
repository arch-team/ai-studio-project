"""
EKS Stack for AI Training Platform.

This stack creates Amazon EKS cluster as the foundation for HyperPod:
- Amazon EKS cluster with Kubernetes 1.32+
- EKS add-ons (EBS CSI, FSx CSI, VPC CNI, CoreDNS, kube-proxy)
- IAM roles for IRSA (IAM Roles for Service Accounts)

After deploying this stack, you need to:
1. Configure kubectl to access the EKS cluster
2. Install HyperPod Helm Chart dependencies
3. Then deploy the SagemakerHyperPodStack

Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-install-packages-using-helm-chart.html
"""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk.lambda_layer_kubectl_v32 import KubectlV32Layer
from constructs import Construct

from config import EnvironmentConfig


class EksStack(cdk.Stack):
    """Amazon EKS Stack for HyperPod orchestration.

    This stack creates:
    - Amazon EKS cluster (K8s 1.32+)
    - Required EKS add-ons (EBS CSI, FSx CSI, VPC CNI, CoreDNS, kube-proxy)
    - IAM roles for IRSA

    Attributes:
        eks_cluster: The EKS cluster for orchestration
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
        """Initialize the EKS Stack.

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

        # Create EKS cluster
        self._eks_cluster = self._create_eks_cluster()

        # Install EKS add-ons
        self._install_eks_addons()

        # Create outputs
        self._create_outputs()

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

        # Create EKS cluster with official kubectl layer for K8s 1.32
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
            # Official kubectl layer for K8s 1.32
            kubectl_layer=KubectlV32Layer(self, "KubectlLayer"),
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

        Note: EKS add-ons automatically create their own ServiceAccounts.
        We only need to create IAM roles for IRSA (IAM Roles for Service Accounts)
        and reference them via serviceAccountRoleArn in the add-on configuration.
        """
        # Use CfnJson to handle dynamic OIDC issuer URL in IAM conditions
        # This is required because the OIDC issuer URL is a CloudFormation Token
        # that resolves at deployment time, not synth time
        oidc_issuer = self._eks_cluster.cluster_open_id_connect_issuer

        # Create CfnJson for EBS CSI driver IRSA conditions
        ebs_csi_conditions = cdk.CfnJson(
            self,
            "EbsCsiConditions",
            value={
                f"{oidc_issuer}:aud": "sts.amazonaws.com",
                f"{oidc_issuer}:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa",
            },
        )

        # Create IAM role for EBS CSI driver (IRSA)
        ebs_csi_role = iam.Role(
            self,
            "EbsCsiDriverRole",
            role_name=f"{self.env_config.resource_prefix}-ebs-csi-role",
            assumed_by=iam.FederatedPrincipal(
                self._eks_cluster.open_id_connect_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": ebs_csi_conditions,
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="IAM role for EBS CSI driver",
        )
        ebs_csi_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmazonEBSCSIDriverPolicy"
            )
        )

        # Create CfnJson for FSx CSI driver IRSA conditions
        fsx_csi_conditions = cdk.CfnJson(
            self,
            "FsxCsiConditions",
            value={
                f"{oidc_issuer}:aud": "sts.amazonaws.com",
                f"{oidc_issuer}:sub": "system:serviceaccount:kube-system:fsx-csi-controller-sa",
            },
        )

        # Create IAM role for FSx CSI driver (IRSA)
        fsx_csi_role = iam.Role(
            self,
            "FsxCsiDriverRole",
            role_name=f"{self.env_config.resource_prefix}-fsx-csi-role",
            assumed_by=iam.FederatedPrincipal(
                self._eks_cluster.open_id_connect_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": fsx_csi_conditions,
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="IAM role for FSx CSI driver",
        )
        fsx_csi_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonFSxFullAccess"
            )
        )

        # Install EBS CSI Driver add-on (EKS 1.33 compatible)
        # The add-on will create the ServiceAccount automatically
        eks.CfnAddon(
            self,
            "EbsCsiAddon",
            addon_name="aws-ebs-csi-driver",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.54.0-eksbuild.1",
            service_account_role_arn=ebs_csi_role.role_arn,
            resolve_conflicts="OVERWRITE",
        )

        # Install FSx CSI Driver add-on (EKS 1.33 compatible)
        # The add-on will create the ServiceAccount automatically
        eks.CfnAddon(
            self,
            "FsxCsiAddon",
            addon_name="aws-fsx-csi-driver",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.8.0-eksbuild.1",
            service_account_role_arn=fsx_csi_role.role_arn,
            resolve_conflicts="OVERWRITE",
        )

        # Install VPC CNI add-on (EKS 1.33 compatible)
        eks.CfnAddon(
            self,
            "VpcCniAddon",
            addon_name="vpc-cni",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.21.1-eksbuild.1",
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

        # Install CoreDNS add-on (EKS 1.33 compatible)
        eks.CfnAddon(
            self,
            "CoreDnsAddon",
            addon_name="coredns",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.12.4-eksbuild.1",
            resolve_conflicts="OVERWRITE",
        )

        # Install kube-proxy add-on (EKS 1.33 compatible)
        eks.CfnAddon(
            self,
            "KubeProxyAddon",
            addon_name="kube-proxy",
            cluster_name=self._eks_cluster.cluster_name,
            addon_version="v1.33.5-eksbuild.2",
            resolve_conflicts="OVERWRITE",
        )

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

        # Output kubeconfig command
        cdk.CfnOutput(
            self,
            "KubeconfigCommand",
            value=f"aws eks update-kubeconfig --name {self._eks_cluster.cluster_name} --region {self.env_config.region}",
            description="Command to configure kubectl",
        )

        # Output Helm install command
        cdk.CfnOutput(
            self,
            "HelmInstallCommand",
            value="git clone https://github.com/aws/sagemaker-hyperpod-cli.git && cd sagemaker-hyperpod-cli/helm_chart && helm dependencies update HyperPodHelmChart && helm install hyperpod-dependencies HyperPodHelmChart --namespace kube-system",
            description="Command to install HyperPod Helm dependencies",
        )

    @property
    def eks_cluster(self) -> eks.Cluster:
        """Get EKS cluster."""
        return self._eks_cluster

    def get_kubeconfig_command(self) -> str:
        """Get command to configure kubectl for cluster access."""
        return (
            f"aws eks update-kubeconfig "
            f"--name {self._eks_cluster.cluster_name} "
            f"--region {self.env_config.region}"
        )
