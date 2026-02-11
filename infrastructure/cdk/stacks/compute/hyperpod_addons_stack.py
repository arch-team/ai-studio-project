"""
HyperPod Add-ons Stack for AI Training Platform.

This stack installs HyperPod-specific EKS add-ons using CDK eks.Addon:
- T008d-1: Training Operator (amazon-sagemaker-hyperpod-training-operator)
- T008d-1: Task Governance / Kueue (amazon-sagemaker-hyperpod-taskgovernance)

Note: Observability (T008d-2) 已迁移到独立的 ObservabilityStack。
Note: PriorityClass configuration is automatically provided by the Task Governance
add-on, so no manual PriorityClass creation is needed.
Note: Elastic Agent (checkpoint management, auto-resume) is NOT an EKS add-on.
It is a Python package installed in training container images via:
  pip install hyperpod-elastic-agent

Reference:
- T008d-1: Training core components installation
- spec.md FR-004: Priority level numerical mapping (managed by Task Governance)
- https://docs.aws.amazon.com/eks/latest/userguide/workloads-add-ons-available-eks.html
"""

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
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._eks_cluster = eks_cluster

        # Create IAM role for Training Operator Pod Identity
        self._training_operator_role = self._create_training_operator_role()

        # T008d-1: Install Training Operator add-on
        self._training_operator_addon = self._install_training_operator()

        # Create Pod Identity Association for Training Operator
        self._training_operator_pod_identity = (
            self._create_training_operator_pod_identity()
        )

        # T008d-1: Install Task Governance (Kueue) add-on
        # Note: Task Governance automatically configures PriorityClass per spec.md FR-004
        self._task_governance_addon = self._install_task_governance()

        # Create outputs
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
        """Create IAM role for Training Operator Pod Identity.

        This role is assumed by the Training Operator controller manager pod
        via EKS Pod Identity to access SageMaker APIs for node health checks.

        Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html
        """
        return create_pod_identity_role(
            scope=self,
            construct_id="TrainingOperatorRole",
            env_config=self.env_config,
            role_name_suffix="training-operator-role",
            description="IAM role for HyperPod Training Operator Pod Identity",
            managed_policies=[MANAGED_POLICIES.HYPERPOD_TRAINING_OPERATOR],
        )

    def _create_training_operator_pod_identity(self) -> eks.CfnPodIdentityAssociation:
        """Create EKS Pod Identity Association for Training Operator.

        This associates the IAM role with the Training Operator's ServiceAccount,
        allowing the controller manager to access AWS APIs.
        """
        association = eks.CfnPodIdentityAssociation(
            self,
            "TrainingOperatorPodIdentity",
            cluster_name=self._eks_cluster.cluster_name,
            namespace=K8S_NAMESPACES.HYPERPOD,
            service_account=SERVICE_ACCOUNTS.TRAINING_OPERATOR,
            role_arn=self._training_operator_role.role_arn,
        )

        # Ensure association is created after the add-on (which creates the ServiceAccount)
        association.add_dependency(self._training_operator_addon)

        apply_component_tag(association, "training-operator")

        return association

    def _install_training_operator(self) -> eks.CfnAddon:
        """Install HyperPod Training Operator add-on.

        The Training Operator provides:
        - PyTorchJob and TFJob CRD support
        - PyTorch DDP/FSDP/DeepSpeed ZeRO framework support
        - Webhook validation for training job configurations
        - HyperPod Elastic Agent integration (via training container images)

        Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html
        """
        return self._create_addon(
            construct_id="TrainingOperatorAddon",
            addon_name=EKS_ADDON_NAMES.TRAINING_OPERATOR,
            component="training-operator",
            description="HyperPod Training Operator for PyTorchJob/TFJob CRD management",
        )

    def _install_task_governance(self) -> eks.CfnAddon:
        """Install HyperPod Task Governance (Kueue) add-on.

        Task Governance provides:
        - Kueue-based workload scheduling
        - Automatic ClusterQueue and LocalQueue creation
        - Gang Scheduling support (default 60s timeout)
        - Preemption policy management
        - PriorityClass configuration (automatically managed per spec.md FR-004)

        Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance-setup-task-governance.html
        """
        addon = self._create_addon(
            construct_id="TaskGovernanceAddon",
            addon_name=EKS_ADDON_NAMES.TASK_GOVERNANCE,
            component="task-governance",
            description="HyperPod Task Governance - Kueue for workload scheduling and Gang Scheduling",
        )

        # Ensure Task Governance is installed after Training Operator
        # for proper CRD dependency resolution
        addon.add_dependency(self._training_operator_addon)

        return addon

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        # T008d-1 outputs
        create_output(
            self,
            "TrainingOperatorAddonName",
            self._training_operator_addon.addon_name,
            "HyperPod Training Operator add-on name",
            export_name=f"{self.env_config.resource_prefix}-training-operator-addon",
        )

        create_output(
            self,
            "TaskGovernanceAddonName",
            self._task_governance_addon.addon_name,
            "HyperPod Task Governance add-on name - includes PriorityClass config",
            export_name=f"{self.env_config.resource_prefix}-task-governance-addon",
        )

    @property
    def training_operator_addon(self) -> eks.CfnAddon:
        return self._training_operator_addon

    @property
    def task_governance_addon(self) -> eks.CfnAddon:
        return self._task_governance_addon
