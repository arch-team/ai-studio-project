"""
Observability Stack for AI Training Platform.

This stack creates the observability infrastructure:
- Amazon Managed Prometheus (AMP) Workspace for metrics storage
- HyperPod Observability EKS add-on (connects to AMP remote write)
- IAM roles (Pod Identity) for Prometheus remote write

Reference:
- spec.md FR-007/FR-016: Observability requirements
- https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-observability-addon-setup.html
"""

import aws_cdk as cdk
from aws_cdk import aws_aps as aps
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from config.constants import EKS_ADDON_NAMES
from constructs import Construct
from utils.iam_helpers import create_pod_identity_role
from utils.outputs import create_output
from utils.tagging import apply_component_tag, create_addon_tags


class ObservabilityStack(cdk.Stack):
    """可观测性 Stack.

    创建:
    - Amazon Managed Prometheus (AMP) Workspace
    - HyperPod Observability EKS Add-on (连接 AMP remote write)
    - IAM roles (Pod Identity) for Prometheus remote write

    Attributes:
        amp_workspace: AMP Workspace
        observability_addon: HyperPod Observability EKS add-on
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        eks_cluster: eks.ICluster,
        **kwargs,
    ) -> None:
        """Initialize the Observability Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            eks_cluster: EKS cluster for add-on installation
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._eks_cluster = eks_cluster

        # 创建 AMP Workspace
        self._amp_workspace: aps.CfnWorkspace | None = None
        if env_config.observability.enable_amp:
            self._amp_workspace = self._create_amp_workspace()

        # 创建 Observability 收集器的 Pod Identity Role
        self._collector_role = self._create_collector_role()

        # 安装 HyperPod Observability Add-on
        self._observability_addon = self._install_observability_addon()

        # 创建 Pod Identity Association
        self._pod_identity = self._create_pod_identity_association()

        # 创建输出
        self._create_outputs()

    def _create_amp_workspace(self) -> aps.CfnWorkspace:
        """创建 Amazon Managed Prometheus Workspace.

        AMP 提供:
        - Prometheus 兼容的指标存储
        - 可扩展的远程写入端点
        - 与 Grafana 无缝集成
        """
        workspace = aps.CfnWorkspace(
            self,
            "AmpWorkspace",
            alias=f"{self.env_config.resource_prefix}-amp",
            tags=[
                cdk.CfnTag(key="Name", value=f"{self.env_config.resource_prefix}-amp"),
                cdk.CfnTag(key="Environment", value=self.env_config.name.value),
                cdk.CfnTag(key="Component", value="observability"),
            ],
        )

        return workspace

    def _create_collector_role(self) -> iam.Role:
        """创建 Observability 收集器的 IAM Role (Pod Identity).

        此角色允许 Observability 收集器 Pod 通过 Pod Identity
        向 AMP 写入指标数据。
        """
        return create_pod_identity_role(
            scope=self,
            construct_id="ObservabilityCollectorRole",
            env_config=self.env_config,
            role_name_suffix="observability-collector-role",
            description="IAM role for HyperPod Observability collector Pod Identity",
            managed_policies=["AmazonPrometheusRemoteWriteAccess"],
        )

    def _install_observability_addon(self) -> eks.CfnAddon:
        """安装 HyperPod Observability EKS Add-on.

        Observability add-on 提供:
        - Node Exporter (系统指标)
        - DCGM Exporter (GPU 指标)
        - kube-state-metrics (K8s 资源指标)
        - EFA Exporter (网络指标)
        - 指标转发到 Amazon Managed Prometheus
        """
        # 构建 add-on 配置
        configuration: dict = {}
        if self._amp_workspace:
            configuration = {
                "ampWorkspaceArn": self._amp_workspace.attr_arn,
            }

        addon = eks.CfnAddon(
            self,
            "ObservabilityAddon",
            addon_name=EKS_ADDON_NAMES.OBSERVABILITY,
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
            configuration_values=(
                cdk.Fn.to_json_string(configuration) if configuration else None
            ),
            tags=create_addon_tags(self.env_config, "observability", "observability"),
        )

        cdk.Tags.of(addon).add(
            "Description",
            "HyperPod Observability for cluster monitoring via Amazon Managed Prometheus",
        )

        return addon

    def _create_pod_identity_association(self) -> eks.CfnPodIdentityAssociation:
        """创建 Observability 收集器的 Pod Identity Association."""
        association = eks.CfnPodIdentityAssociation(
            self,
            "ObservabilityCollectorPodIdentity",
            cluster_name=self._eks_cluster.cluster_name,
            namespace="hyperpod-observability",
            service_account="hyperpod-observability-operator-otel-collector",
            role_arn=self._collector_role.role_arn,
        )

        # 确保 association 在 add-on 之后创建
        association.add_dependency(self._observability_addon)

        apply_component_tag(association, "observability")

        return association

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出."""
        if self._amp_workspace:
            create_output(
                self,
                "AmpWorkspaceArn",
                self._amp_workspace.attr_arn,
                "Amazon Managed Prometheus workspace ARN",
            )
            create_output(
                self,
                "AmpWorkspaceId",
                self._amp_workspace.attr_workspace_id,
                "Amazon Managed Prometheus workspace ID",
            )
            # AMP remote write endpoint
            create_output(
                self,
                "AmpRemoteWriteEndpoint",
                f"https://aps-workspaces.{self.env_config.region}.amazonaws.com/workspaces/{self._amp_workspace.attr_workspace_id}/api/v1/remote_write",
                "AMP remote write endpoint for Prometheus",
            )

        create_output(
            self,
            "ObservabilityAddonName",
            self._observability_addon.addon_name,
            "HyperPod Observability add-on name",
        )

    @property
    def amp_workspace(self) -> aps.CfnWorkspace | None:
        """Get AMP Workspace."""
        return self._amp_workspace

    @property
    def observability_addon(self) -> eks.CfnAddon:
        """Get Observability add-on."""
        return self._observability_addon
