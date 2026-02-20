"""HyperPod Add-ons Stack — Training Operator + Task Governance。

Observability 已迁移到 ObservabilityStack。
Elastic Agent 不是 EKS add-on，需在训练容器镜像中 pip install。

参考: spec.md FR-004 (PriorityClass 由 Task Governance 自动管理)
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from config.constants import (
    EKS_ADDON_NAMES,
    K8S_NAMESPACES,
    MANAGED_POLICIES,
    SERVICE_ACCOUNTS,
)
from constructs import Construct
from utils.eks_helpers import create_eks_addon
from utils.iam_helpers import create_pod_identity_role
from utils.outputs import create_output
from utils.tagging import apply_component_tag, create_addon_tags


class HyperPodAddonsStack(cdk.Stack):
    """HyperPod Add-ons Stack。

    安装 Training Operator 和 Task Governance (Kueue) 两个 HyperPod 专用 Add-on。
    Observability 已迁移到独立的 ObservabilityStack。
    Elastic Agent 不是 EKS Add-on，需在训练容器镜像中通过 pip 安装。
    """

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

        self._training_operator_role = self._create_training_operator_role()
        self._training_operator_addon = self._install_training_operator()

        self._training_operator_pod_identity = (
            self._create_training_operator_pod_identity()
        )

        self._task_governance_addon = self._install_task_governance()
        self._create_outputs()

    def _create_addon(
        self,
        construct_id: str,
        addon_name: str,
        component: str,
        description: str,
        addon_version: str | None = None,
    ) -> eks.CfnAddon:
        """创建带标签的 HyperPod EKS Add-on。

        addon_version 为 None 则使用 AWS 默认版本。
        建议在生产环境中锁定版本以确保可重复部署。
        查询可用版本: aws eks describe-addon-versions --addon-name <name>
        """
        addon = create_eks_addon(
            self,
            construct_id,
            addon_name=addon_name,
            cluster_name=self._eks_cluster.cluster_name,
            addon_version=addon_version,
            tags=create_addon_tags(self.env_config, component, component),
        )

        cdk.Tags.of(addon).add("Description", description)

        return addon

    def _create_training_operator_role(self) -> iam.Role:
        """创建 Training Operator Pod Identity 角色 (SageMaker API 访问)。"""
        return create_pod_identity_role(
            scope=self,
            construct_id="TrainingOperatorRole",
            env_config=self.env_config,
            role_name_suffix="training-operator-role",
            description="IAM role for HyperPod Training Operator Pod Identity",
            managed_policies=[MANAGED_POLICIES.HYPERPOD_TRAINING_OPERATOR],
        )

    def _create_training_operator_pod_identity(self) -> eks.CfnPodIdentityAssociation:
        """创建 Training Operator 的 Pod Identity Association。"""
        association = eks.CfnPodIdentityAssociation(
            self,
            "TrainingOperatorPodIdentity",
            cluster_name=self._eks_cluster.cluster_name,
            namespace=K8S_NAMESPACES.HYPERPOD,
            service_account=SERVICE_ACCOUNTS.TRAINING_OPERATOR,
            role_arn=self._training_operator_role.role_arn,
        )

        # add-on 创建 ServiceAccount 后才能关联 Pod Identity
        association.add_dependency(self._training_operator_addon)

        apply_component_tag(association, "training-operator")

        return association

    def _install_training_operator(self) -> eks.CfnAddon:
        """安装 Training Operator (PyTorchJob/TFJob CRD, DDP/FSDP/DeepSpeed 支持)。"""
        return self._create_addon(
            construct_id="TrainingOperatorAddon",
            addon_name=EKS_ADDON_NAMES.TRAINING_OPERATOR,
            component="training-operator",
            description="HyperPod Training Operator for PyTorchJob/TFJob CRD management",
        )

    def _install_task_governance(self) -> eks.CfnAddon:
        """安装 Task Governance (Kueue 调度, Gang Scheduling, PriorityClass)。"""
        addon = self._create_addon(
            construct_id="TaskGovernanceAddon",
            addon_name=EKS_ADDON_NAMES.TASK_GOVERNANCE,
            component="task-governance",
            description="HyperPod Task Governance - Kueue for workload scheduling and Gang Scheduling",
        )

        # Training Operator CRD 是 Task Governance 的前置条件
        addon.add_dependency(self._training_operator_addon)

        return addon

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出。"""
        prefix = self.env_config.resource_prefix
        outputs = [
            (
                "TrainingOperatorAddonName",
                self._training_operator_addon.addon_name,
                "HyperPod Training Operator add-on name",
                f"{prefix}-training-operator-addon",
            ),
            (
                "TaskGovernanceAddonName",
                self._task_governance_addon.addon_name,
                "HyperPod Task Governance add-on name",
                f"{prefix}-task-governance-addon",
            ),
        ]
        for output_id, value, description, export_name in outputs:
            create_output(self, output_id, value, description, export_name=export_name)

    @property
    def training_operator_addon(self) -> eks.CfnAddon:
        return self._training_operator_addon

    @property
    def task_governance_addon(self) -> eks.CfnAddon:
        return self._task_governance_addon
