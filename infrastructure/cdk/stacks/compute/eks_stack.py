"""EKS Stack — HyperPod 编排基础。

创建 EKS 集群、Add-ons、IRSA 角色和 HyperPod Helm Chart 依赖。
前提: 部署前需运行 ./scripts/setup_helm_chart.sh 下载 Helm Chart。
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3_assets as s3_assets
from aws_cdk.lambda_layer_kubectl_v33 import KubectlV33Layer

from cdk_constructs.gpu_node_group import create_default_gpu_node_groups
from config import EnvironmentConfig
from config.constants import EKS_ADDON_NAMES, ProjectPaths
from constructs import Construct
from utils.eks_helpers import create_eks_addon
from utils.iam_helpers import add_policy_statement, create_irsa_role
from utils.outputs import create_output

HELM_CHART_PATH = ProjectPaths.HYPERPOD_HELM_CHART


class EksStack(cdk.Stack):
    """EKS Stack — 创建 EKS 集群、Add-ons、IRSA 角色和 HyperPod Helm Chart。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        eks_node_role: iam.IRole,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._eks_node_role = eks_node_role

        self._eks_cluster = self._create_eks_cluster()
        self._create_system_node_group()

        self._gpu_node_groups = create_default_gpu_node_groups(
            scope=self,
            env_config=self.env_config,
            eks_cluster=self._eks_cluster,
            node_role=self._eks_node_role,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=self._vpc,
        )

        self._install_eks_addons()
        self._install_hyperpod_helm_chart()
        self._create_outputs()

    def _create_eks_cluster(self) -> eks.Cluster:
        eks_config = self.env_config.eks

        # 限制仅 EKSAdmin 标签用户可 assume
        cluster_admin_role = iam.Role(
            self,
            "ClusterAdminRole",
            role_name=f"{self.env_config.resource_prefix}-eks-admin-role",
            assumed_by=iam.AccountRootPrincipal().with_conditions(
                {
                    "StringEquals": {
                        "aws:PrincipalTag/Role": "EKSAdmin",
                    }
                }
            ),
            description="Admin role for EKS cluster management",
        )

        cluster = eks.Cluster(
            self,
            "EksCluster",
            cluster_name=f"{self.env_config.resource_prefix}-eks",
            version=eks.KubernetesVersion.of(eks_config.kubernetes_version),
            vpc=self._vpc,
            vpc_subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ],
            default_capacity=0,  # 由独立节点组管理
            endpoint_access=eks.EndpointAccess.PRIVATE,
            masters_role=cluster_admin_role,
            kubectl_layer=KubectlV33Layer(self, "KubectlLayer"),
            cluster_logging=[
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR,
                eks.ClusterLoggingTypes.CONTROLLER_MANAGER,
                eks.ClusterLoggingTypes.SCHEDULER,
            ],
            # HyperPod 兼容性要求 API_AND_CONFIG_MAP 模式
            authentication_mode=eks.AuthenticationMode.API_AND_CONFIG_MAP,
        )

        cdk.Tags.of(cluster).add("Name", f"{self.env_config.resource_prefix}-eks")
        cdk.Tags.of(cluster).add("kubernetes.io/cluster-type", "hyperpod-orchestrator")

        return cluster

    def _create_system_node_group(self) -> None:
        self._eks_cluster.add_nodegroup_capacity(
            "SystemNodeGroup",
            nodegroup_name=f"{self.env_config.resource_prefix}-system-nodes",
            instance_types=[ec2.InstanceType("m5.4xlarge")],
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

    def _create_addon(
        self,
        construct_id: str,
        addon_name: str,
        addon_version: str | None = None,
        service_account_role_arn: str | None = None,
        configuration_values: str | None = None,
    ) -> eks.CfnAddon:
        return create_eks_addon(
            self,
            construct_id,
            addon_name=addon_name,
            cluster_name=self._eks_cluster.cluster_name,
            addon_version=addon_version,
            service_account_role_arn=service_account_role_arn,
            configuration_values=configuration_values,
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
        oidc_arn = (
            self._eks_cluster.open_id_connect_provider.open_id_connect_provider_arn
        )
        oidc_issuer = self._eks_cluster.cluster_open_id_connect_issuer

        # 创建 EBS CSI Driver IRSA 角色
        ebs_csi_role = create_irsa_role(
            scope=self,
            construct_id="EbsCsiDriverRole",
            env_config=self.env_config,
            oidc_provider_arn=oidc_arn,
            oidc_issuer=oidc_issuer,
            role_name_suffix="ebs-csi-role",
            service_account="ebs-csi-controller-sa",
            description="IAM role for EBS CSI driver",
            managed_policies=["service-role/AmazonEBSCSIDriverPolicy"],
        )

        # 创建 FSx CSI Driver IRSA 角色 (最小权限，不使用 AmazonFSxFullAccess)
        fsx_csi_role = create_irsa_role(
            scope=self,
            construct_id="FsxCsiDriverRole",
            env_config=self.env_config,
            oidc_provider_arn=oidc_arn,
            oidc_issuer=oidc_issuer,
            role_name_suffix="fsx-csi-role",
            service_account="fsx-csi-controller-sa",
            description="IAM role for FSx CSI driver",
            managed_policies=[],  # 使用自定义最小权限策略替代 AmazonFSxFullAccess
        )
        # FSx CSI Driver 仅需描述和挂载相关权限
        add_policy_statement(
            fsx_csi_role,
            sid="FsxCsiDescribe",
            actions=[
                "fsx:DescribeFileSystems",
                "fsx:DescribeVolumes",
                "fsx:DescribeDataRepositoryAssociations",
            ],
            resources=["*"],  # fsx:Describe 操作不支持资源级限制
        )

        # 获取插件版本（集中式版本管理）
        addon_versions = self.env_config.eks.addon_versions

        # 存储驱动插件（需要 IRSA 角色）
        self._create_addon(
            "EbsCsiAddon",
            EKS_ADDON_NAMES.EBS_CSI_DRIVER,
            addon_version=addon_versions.ebs_csi,
            service_account_role_arn=ebs_csi_role.role_arn,
        )
        self._create_addon(
            "FsxCsiAddon",
            EKS_ADDON_NAMES.FSX_CSI_DRIVER,
            addon_version=addon_versions.fsx_csi,
            service_account_role_arn=fsx_csi_role.role_arn,
        )

        # 网络插件（VPC CNI 需要额外配置）
        self._create_addon(
            "VpcCniAddon",
            EKS_ADDON_NAMES.VPC_CNI,
            addon_version=addon_versions.vpc_cni,
            configuration_values=cdk.Fn.to_json_string(
                {
                    "env": {
                        "ENABLE_PREFIX_DELEGATION": "true",
                        "WARM_PREFIX_TARGET": "1",
                    }
                }
            ),
        )

        # 核心系统插件
        self._create_addon(
            "CoreDnsAddon",
            EKS_ADDON_NAMES.COREDNS,
            addon_version=addon_versions.coredns,
        )
        self._create_addon(
            "KubeProxyAddon",
            EKS_ADDON_NAMES.KUBE_PROXY,
            addon_version=addon_versions.kube_proxy,
        )

        # EKS Pod Identity Agent（HyperPod Training Operator IAM 认证前置条件）
        self._create_addon("PodIdentityAgentAddon", EKS_ADDON_NAMES.POD_IDENTITY_AGENT)

        # cert-manager community add-on（HyperPod Training Operator webhook 证书前置条件）
        self._cert_manager_addon = self._create_addon(
            "CertManagerAddon", EKS_ADDON_NAMES.CERT_MANAGER
        )

    def _install_hyperpod_helm_chart(self) -> None:
        """安装 HyperPod Helm Chart (监控、设备插件、训练 Operator 等)。

        Raises:
            FileNotFoundError: Helm Chart 不在预期路径时
        """
        if not HELM_CHART_PATH.exists():
            raise FileNotFoundError(
                f"HyperPod Helm Chart not found at {HELM_CHART_PATH}. "
                "Please run ./scripts/setup_helm_chart.sh first to download the Helm Chart."
            )

        helm_chart_asset = s3_assets.Asset(
            self,
            "HyperPodHelmChartAsset",
            path=str(HELM_CHART_PATH),
        )

        # 超时 15 分钟: 多组件 Chart 安装耗时较长
        hyperpod_chart = self._eks_cluster.add_helm_chart(
            "HyperPodDependencies",
            chart_asset=helm_chart_asset,
            namespace="kube-system",
            release="hyperpod-dependencies",
            wait=False,  # 集群无节点时无需等待 Pod 就绪
            timeout=cdk.Duration.minutes(15),
            skip_crds=True,
            values={
                "global": {
                    "region": self.env_config.region,
                },
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
                # cert-manager 已通过独立 EKS add-on 安装
                "cert-manager": {
                    "enabled": False,
                },
                "mlflow": {"enabled": False},
                "storage": {"enabled": False},  # 使用 EKS add-ons 管理存储
                "inferenceOperators": {"enabled": False},
                "gpu-operator": {"enabled": False},  # 使用 nvidia-device-plugin 替代
            },
        )

        # HyperPod Training Operator webhook 依赖 cert-manager 签发证书
        hyperpod_chart.node.add_dependency(self._cert_manager_addon)

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出用于跨 Stack 引用。"""
        prefix = self.env_config.resource_prefix
        cluster = self._eks_cluster

        # (output_id, value, description, export_name)
        outputs: list[tuple[str, str, str, str | None]] = [
            ("EksClusterName", cluster.cluster_name, "EKS cluster name", None),
            ("EksClusterArn", cluster.cluster_arn, "EKS cluster ARN", None),
            (
                "EksClusterEndpoint",
                cluster.cluster_endpoint,
                "EKS cluster API endpoint",
                f"{prefix}-eks-endpoint",
            ),
            (
                "EksClusterSecurityGroupId",
                cluster.cluster_security_group_id,
                "EKS cluster security group ID",
                f"{prefix}-eks-sg-id",
            ),
            (
                "EksOidcProviderArn",
                cluster.open_id_connect_provider.open_id_connect_provider_arn,
                "EKS OIDC provider ARN for IRSA",
                f"{prefix}-eks-oidc-arn",
            ),
            (
                "CertManagerAddonName",
                EKS_ADDON_NAMES.CERT_MANAGER,
                "cert-manager EKS add-on name",
                f"{prefix}-cert-manager-addon",
            ),
        ]
        for output_id, value, description, export_name in outputs:
            create_output(self, output_id, value, description, export_name=export_name)

        cdk.CfnOutput(
            self,
            "KubeconfigCommand",
            value=self.get_kubeconfig_command(),
            description="Command to configure kubectl",
        )

    @property
    def eks_cluster(self) -> eks.Cluster:
        return self._eks_cluster

    def get_kubeconfig_command(self) -> str:
        return (
            f"aws eks update-kubeconfig "
            f"--name {self._eks_cluster.cluster_name} "
            f"--region {self.env_config.region}"
        )
