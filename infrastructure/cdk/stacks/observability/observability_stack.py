"""Observability Stack — AMP + HyperPod 可观测性 Add-on。

创建 Amazon Managed Prometheus Workspace、HyperPod Observability EKS Add-on
和 Pod Identity IAM 角色。

参考: spec.md FR-007/FR-016 (可观测性需求)
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_aps as aps
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from config.constants import EKS_ADDON_NAMES, K8S_NAMESPACES, SERVICE_ACCOUNTS
from constructs import Construct
from utils.eks_helpers import create_eks_addon
from utils.iam_helpers import create_pod_identity_role
from utils.outputs import create_output
from utils.tagging import apply_component_tag, create_addon_tags, create_cfn_tags


class ObservabilityStack(cdk.Stack):
    """Observability Stack — AMP + HyperPod 可观测性 Add-on。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        eks_cluster: eks.ICluster,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._eks_cluster = eks_cluster

        self._amp_workspace: aps.CfnWorkspace | None = None
        if env_config.observability.enable_amp:
            self._amp_workspace = self._create_amp_workspace()

        self._collector_role = self._create_collector_role()
        self._observability_addon = self._install_observability_addon()
        self._pod_identity = self._create_pod_identity_association()
        self._create_outputs()

    def _amp_endpoint_base(self) -> str:
        """AMP Workspace 端点基础 URL (复用于 add-on 配置和输出)。"""
        assert self._amp_workspace is not None
        return (
            f"https://aps-workspaces.{self.env_config.region}.amazonaws.com"
            f"/workspaces/{self._amp_workspace.attr_workspace_id}"
        )

    def _create_amp_workspace(self) -> aps.CfnWorkspace:
        """创建 Amazon Managed Prometheus Workspace。"""
        return aps.CfnWorkspace(
            self,
            "AmpWorkspace",
            alias=f"{self.env_config.resource_prefix}-amp",
            tags=create_cfn_tags(
                self.env_config,
                "amp",
                additional_tags={"Component": "observability"},
            ),
        )

    def _create_collector_role(self) -> iam.Role:
        """创建 Observability 收集器 Pod Identity 角色 (AMP remote write)。"""
        return create_pod_identity_role(
            scope=self,
            construct_id="ObservabilityCollectorRole",
            env_config=self.env_config,
            role_name_suffix="observability-collector-role",
            description="IAM role for HyperPod Observability collector Pod Identity",
            managed_policies=["AmazonPrometheusRemoteWriteAccess"],
        )

    def _install_observability_addon(self) -> eks.CfnAddon:
        """安装 HyperPod Observability EKS Add-on (Node/DCGM/EFA Exporter + kube-state-metrics)。"""
        configuration: dict = {}
        if self._amp_workspace:
            configuration = {
                "ampWorkspace": {
                    "arn": self._amp_workspace.attr_arn,
                    "prometheusEndpoint": self._amp_endpoint_base(),
                },
            }

        addon = create_eks_addon(
            self,
            "ObservabilityAddon",
            addon_name=EKS_ADDON_NAMES.OBSERVABILITY,
            cluster_name=self._eks_cluster.cluster_name,
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
        """创建 Observability 收集器的 Pod Identity Association。"""
        association = eks.CfnPodIdentityAssociation(
            self,
            "ObservabilityCollectorPodIdentity",
            cluster_name=self._eks_cluster.cluster_name,
            namespace=K8S_NAMESPACES.HYPERPOD_OBSERVABILITY,
            service_account=SERVICE_ACCOUNTS.OBSERVABILITY_COLLECTOR,
            role_arn=self._collector_role.role_arn,
        )

        # 注意: 不添加对 addon 的依赖，避免循环等待:
        # addon 等待 collector healthy → collector 需要 PodIdentity 凭证 → PodIdentity 等待 addon
        # PodIdentityAssociation 与 addon 并行创建，确保 collector 启动时能获取凭证

        apply_component_tag(association, "observability")

        return association

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出。"""
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
            create_output(
                self,
                "AmpRemoteWriteEndpoint",
                f"{self._amp_endpoint_base()}/api/v1/remote_write",
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
        return self._amp_workspace

    @property
    def observability_addon(self) -> eks.CfnAddon:
        return self._observability_addon
