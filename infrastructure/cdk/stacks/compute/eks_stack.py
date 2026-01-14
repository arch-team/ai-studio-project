"""
EKS Stack for AI Training Platform.

This stack creates Amazon EKS cluster as the foundation for HyperPod:
- Amazon EKS cluster with Kubernetes 1.33+
- EKS add-ons (EBS CSI, FSx CSI, VPC CNI, CoreDNS, kube-proxy)
- IAM roles for IRSA (IAM Roles for Service Accounts)
- HyperPod Helm Chart dependencies (auto-installed)

Prerequisites:
    Run ./scripts/setup_helm_chart.sh before deploying this stack
    to download and prepare the HyperPod Helm Chart.

Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-install-packages-using-helm-chart.html
"""

from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3_assets as s3_assets
from aws_cdk.lambda_layer_kubectl_v33 import KubectlV33Layer

from config import EnvironmentConfig
from config.constants import EKS_ADDON_NAMES
from constructs import Construct

# Path to the HyperPod Helm Chart (relative to this file)
# File location: stacks/compute/eks_stack.py -> resources/helm_charts/
HELM_CHART_PATH = (
    Path(__file__).parent.parent.parent / "resources" / "helm_charts" / "HyperPodHelmChart"
)


class EksStack(cdk.Stack):
    """Amazon EKS Stack for HyperPod orchestration.

    This stack creates:
    - Amazon EKS cluster (K8s 1.33+)
    - Required EKS add-ons (EBS CSI, FSx CSI, VPC CNI, CoreDNS, kube-proxy)
    - IAM roles for IRSA
    - HyperPod Helm Chart dependencies (health-monitoring-agent, device plugins, etc.)

    Prerequisites:
        Run ./scripts/setup_helm_chart.sh before deploying this stack.

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

        # Create System Node Group for control plane workloads
        self._create_system_node_group()

        # Install EKS add-ons (including cert-manager community add-on)
        self._install_eks_addons()

        # Install HyperPod Helm Chart dependencies (depends on cert-manager add-on)
        self._install_hyperpod_helm_chart()

        # Create outputs
        self._create_outputs()

    def _create_eks_cluster(self) -> eks.Cluster:
        """Create Amazon EKS cluster for HyperPod orchestration.

        Creates EKS cluster with:
        - Kubernetes version 1.33
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

        # Create EKS cluster with official kubectl layer for K8s 1.33
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
            # Official kubectl layer for K8s 1.33
            kubectl_layer=KubectlV33Layer(self, "KubectlLayer"),
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

    def _create_irsa_role(
        self,
        role_id: str,
        role_name: str,
        service_account: str,
        managed_policy_name: str,
        description: str,
    ) -> iam.Role:
        """创建 IRSA（IAM Roles for Service Accounts）角色。

        Args:
            role_id: CDK Construct ID
            role_name: IAM 角色名称
            service_account: Kubernetes ServiceAccount 名称
            managed_policy_name: AWS 托管策略名称
            description: 角色描述

        Returns:
            配置好的 IAM Role
        """
        oidc_issuer = self._eks_cluster.cluster_open_id_connect_issuer

        # 创建条件
        conditions = cdk.CfnJson(
            self,
            f"{role_id}Conditions",
            value={
                f"{oidc_issuer}:aud": "sts.amazonaws.com",
                f"{oidc_issuer}:sub": f"system:serviceaccount:kube-system:{service_account}",
            },
        )

        # 创建角色
        role = iam.Role(
            self,
            role_id,
            role_name=role_name,
            assumed_by=iam.FederatedPrincipal(
                self._eks_cluster.open_id_connect_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": conditions,
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description=description,
        )

        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name)
        )

        return role

    def _create_system_node_group(self) -> None:
        """Create EC2 node group for system components.

        This node group runs system workloads like HyperPod dependencies
        that require compute resources before HyperPod managed nodes are available.

        The node group uses:
        - t3.medium instances for cost efficiency
        - AL2023 AMI for K8s 1.33+ compatibility
        - CriticalAddonsOnly taint to reserve for system workloads
        """
        self._eks_cluster.add_nodegroup_capacity(
            "SystemNodeGroup",
            nodegroup_name=f"{self.env_config.resource_prefix}-system-nodes",
            instance_types=[ec2.InstanceType("t3.medium")],
            min_size=1,
            max_size=2,
            desired_size=1,
            disk_size=20,
            capacity_type=eks.CapacityType.ON_DEMAND,
            ami_type=eks.NodegroupAmiType.AL2023_X86_64_STANDARD,
            labels={
                "node-role": "system",
                "workload-type": "control-plane",
            },
            taints=[
                eks.TaintSpec(
                    key="CriticalAddonsOnly",
                    value="true",
                    effect=eks.TaintEffect.PREFER_NO_SCHEDULE,
                ),
            ],
        )

    def _install_eks_addons(self) -> None:
        """安装 EKS 必需的插件（含 cert-manager community add-on）。

        必需插件：
        - EBS CSI Driver (≥v1.28.0) - 持久化卷
        - FSx CSI Driver (≥v1.9.0) - Lustre 存储
        - VPC CNI (≥v1.16.0) - Pod 网络
        - CoreDNS - DNS 解析
        - kube-proxy - Service 网络
        - EKS Pod Identity Agent - IAM 认证
        - cert-manager - 证书管理（HyperPod Training Operator 前置条件）

        注意：EKS 插件会自动创建 ServiceAccount，我们只需创建 IRSA 角色。

        Reference:
        - https://docs.aws.amazon.com/eks/latest/userguide/community-addons.html
        """
        # 创建 EBS CSI Driver IRSA 角色
        ebs_csi_role = self._create_irsa_role(
            role_id="EbsCsiDriverRole",
            role_name=f"{self.env_config.resource_prefix}-ebs-csi-role",
            service_account="ebs-csi-controller-sa",
            managed_policy_name="service-role/AmazonEBSCSIDriverPolicy",
            description="IAM role for EBS CSI driver",
        )

        # 创建 FSx CSI Driver IRSA 角色
        fsx_csi_role = self._create_irsa_role(
            role_id="FsxCsiDriverRole",
            role_name=f"{self.env_config.resource_prefix}-fsx-csi-role",
            service_account="fsx-csi-controller-sa",
            managed_policy_name="AmazonFSxFullAccess",
            description="IAM role for FSx CSI driver",
        )

        # 获取插件版本（集中式版本管理）
        addon_versions = self.env_config.eks.addon_versions

        # Install EBS CSI Driver add-on
        # The add-on will create the ServiceAccount automatically
        eks.CfnAddon(
            self,
            "EbsCsiAddon",
            addon_name=EKS_ADDON_NAMES.EBS_CSI_DRIVER,
            cluster_name=self._eks_cluster.cluster_name,
            addon_version=addon_versions.ebs_csi,
            service_account_role_arn=ebs_csi_role.role_arn,
            resolve_conflicts="OVERWRITE",
        )

        # Install FSx CSI Driver add-on
        # The add-on will create the ServiceAccount automatically
        eks.CfnAddon(
            self,
            "FsxCsiAddon",
            addon_name=EKS_ADDON_NAMES.FSX_CSI_DRIVER,
            cluster_name=self._eks_cluster.cluster_name,
            addon_version=addon_versions.fsx_csi,
            service_account_role_arn=fsx_csi_role.role_arn,
            resolve_conflicts="OVERWRITE",
        )

        # Install VPC CNI add-on
        eks.CfnAddon(
            self,
            "VpcCniAddon",
            addon_name=EKS_ADDON_NAMES.VPC_CNI,
            cluster_name=self._eks_cluster.cluster_name,
            addon_version=addon_versions.vpc_cni,
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
            addon_name=EKS_ADDON_NAMES.COREDNS,
            cluster_name=self._eks_cluster.cluster_name,
            addon_version=addon_versions.coredns,
            resolve_conflicts="OVERWRITE",
        )

        # Install kube-proxy add-on
        eks.CfnAddon(
            self,
            "KubeProxyAddon",
            addon_name=EKS_ADDON_NAMES.KUBE_PROXY,
            cluster_name=self._eks_cluster.cluster_name,
            addon_version=addon_versions.kube_proxy,
            resolve_conflicts="OVERWRITE",
        )

        # Install EKS Pod Identity Agent add-on
        # Required by HyperPod Training Operator for IAM authentication
        eks.CfnAddon(
            self,
            "PodIdentityAgentAddon",
            addon_name=EKS_ADDON_NAMES.POD_IDENTITY_AGENT,
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
        )

        # Install cert-manager community add-on
        # Required by HyperPod Training Operator for webhook certificates
        # Reference: https://docs.aws.amazon.com/eks/latest/userguide/community-addons.html
        self._cert_manager_addon = eks.CfnAddon(
            self,
            "CertManagerAddon",
            addon_name=EKS_ADDON_NAMES.CERT_MANAGER,
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
        )

    def _install_hyperpod_helm_chart(self) -> None:
        """Install HyperPod Helm Chart dependencies.

        This installs the HyperPod Helm Chart which includes:
        - Health monitoring agent (required for cluster monitoring)
        - Deep health check (for HyperPod deep health check feature)
        - Job auto-restart (for PyTorch training job auto-restart)
        - Kubeflow MPI operator (for distributed ML workloads)
        - NVIDIA device plugin (for GPU instances)
        - Neuron device plugin (for Trainium/Inferentia instances)
        - AWS EFA device plugin (for Elastic Fabric Adapter)
        - Training operators (Kubeflow training operators)

        Prerequisites:
            Run ./scripts/setup_helm_chart.sh to download the Helm Chart first.

        Raises:
            FileNotFoundError: If the Helm Chart is not found at the expected path.
        """
        # Check if Helm Chart exists
        if not HELM_CHART_PATH.exists():
            raise FileNotFoundError(
                f"HyperPod Helm Chart not found at {HELM_CHART_PATH}. "
                "Please run ./scripts/setup_helm_chart.sh first to download the Helm Chart."
            )

        # Create S3 Asset from the Helm Chart directory
        helm_chart_asset = s3_assets.Asset(
            self,
            "HyperPodHelmChartAsset",
            path=str(HELM_CHART_PATH),
        )

        # Install HyperPod Helm Chart using the EKS cluster's addHelmChart method
        # Note: We use chart_asset to install from the local packaged chart
        # Increase timeout to 15 minutes for complex chart with many dependencies
        # Skip CRDs if they already exist from previous installations
        hyperpod_chart = self._eks_cluster.add_helm_chart(
            "HyperPodDependencies",
            chart_asset=helm_chart_asset,
            namespace="kube-system",
            release="hyperpod-dependencies",
            wait=False,  # Don't wait for pods to be ready (no nodes yet)
            timeout=cdk.Duration.minutes(15),
            skip_crds=True,  # Skip CRDs that may already exist
            # Custom values for HyperPod configuration
            values={
                # Global settings
                "global": {
                    "region": self.env_config.region,
                },
                # Enable required components
                "trainingOperators": {
                    "enabled": True,
                },
                "health-monitoring-agent": {
                    "enabled": True,
                },
                "deep-health-check": {
                    "enabled": True,
                },
                "job-auto-restart": {
                    "enabled": True,
                },
                "mpi-operator": {
                    "enabled": True,
                },
                "hyperpod-patching": {
                    "enabled": True,
                },
                # Device plugins
                "nvidia-device-plugin": {
                    "devicePlugin": {
                        "enabled": True,
                    },
                },
                "neuron-device-plugin": {
                    "devicePlugin": {
                        "enabled": True,
                    },
                },
                "aws-efa-k8s-device-plugin": {
                    "devicePlugin": {
                        "enabled": True,
                    },
                },
                # cert-manager is installed separately via its own Helm Chart
                "cert-manager": {
                    "enabled": False,  # Installed separately before HyperPod dependencies
                },
                "mlflow": {
                    "enabled": False,  # Optional
                },
                "storage": {
                    "enabled": False,  # Using EKS add-ons for storage
                },
                "inferenceOperators": {
                    "enabled": False,  # Enable when inference is needed
                },
                "gpu-operator": {
                    "enabled": False,  # Using nvidia-device-plugin instead
                },
            },
        )

        # Ensure HyperPod dependencies are installed after cert-manager
        hyperpod_chart.node.add_dependency(self._cert_manager_addon)

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出用于跨 Stack 引用。"""
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

        # cert-manager add-on output
        cdk.CfnOutput(
            self,
            "CertManagerAddonName",
            value=EKS_ADDON_NAMES.CERT_MANAGER,
            description="cert-manager EKS add-on name",
            export_name=f"{self.env_config.resource_prefix}-cert-manager-addon",
        )

        # Output Helm Chart installation status
        cdk.CfnOutput(
            self,
            "HelmChartStatus",
            value="HyperPod Helm Chart automatically installed via CDK",
            description="HyperPod Helm Chart is automatically installed during stack deployment",
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
