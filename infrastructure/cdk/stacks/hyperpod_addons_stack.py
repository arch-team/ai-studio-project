"""
HyperPod Add-ons Stack for AI Training Platform.

This stack installs HyperPod-specific EKS add-ons using CDK eks.Addon:
- T008d-1: Training Operator (amazon-sagemaker-hyperpod-training-operator)
- T008d-1: Task Governance / Kueue (amazon-sagemaker-hyperpod-taskgovernance)
- T008d-2: Observability (amazon-sagemaker-hyperpod-observability)

Note: PriorityClass configuration is automatically provided by the Task Governance
add-on, so no manual PriorityClass creation is needed.

Note: Elastic Agent (checkpoint management, auto-resume) is NOT an EKS add-on.
It is a Python package installed in training container images via:
  pip install hyperpod-elastic-agent
See: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html

Reference:
- T008d-1: Training core components installation
- T008d-2: Monitoring components installation
- spec.md FR-004: Priority level numerical mapping (managed by Task Governance)
- spec.md FR-007/FR-016: Observability (Prometheus + Grafana via Amazon Managed Prometheus/Grafana)
- https://docs.aws.amazon.com/eks/latest/userguide/workloads-add-ons-available-eks.html
"""

import aws_cdk as cdk
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct


class HyperPodAddonsStack(cdk.Stack):
    """HyperPod Add-ons Stack.

    This stack installs HyperPod-specific add-ons:
    - Training Operator: Manages PyTorchJob, TensorFlowJob CRDs for distributed training
    - Task Governance: Kueue-based workload scheduling with Gang Scheduling support
      (includes automatic PriorityClass configuration per spec.md FR-004)
    - Observability: Prometheus + Grafana for cluster monitoring (spec.md FR-007/FR-016)

    Note: Elastic Agent is NOT an EKS add-on. It must be installed in training
    container images via `pip install hyperpod-elastic-agent`.

    Prerequisites:
    - EKS cluster must be deployed with HyperPod Helm Chart installed (EksStack)
    - SageMaker HyperPod cluster must be created (SagemakerHyperPodStack)

    Attributes:
        training_operator_addon: The Training Operator EKS add-on
        task_governance_addon: The Task Governance (Kueue) EKS add-on
        observability_addon: The Observability (Prometheus + Grafana) EKS add-on
    """

    # Official HyperPod EKS Add-on names
    # Reference: https://docs.aws.amazon.com/eks/latest/userguide/workloads-add-ons-available-eks.html
    TRAINING_OPERATOR_ADDON = "amazon-sagemaker-hyperpod-training-operator"
    TASK_GOVERNANCE_ADDON = "amazon-sagemaker-hyperpod-taskgovernance"  # Note: no hyphen
    OBSERVABILITY_ADDON = "amazon-sagemaker-hyperpod-observability"

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        eks_cluster: eks.ICluster,
        **kwargs,
    ) -> None:
        """Initialize the HyperPod Add-ons Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            eks_cluster: EKS cluster to install add-ons on
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._eks_cluster = eks_cluster

        # Create IAM role for Training Operator Pod Identity
        self._training_operator_role = self._create_training_operator_role()

        # T008d-1: Install Training Operator add-on
        self._training_operator_addon = self._install_training_operator()

        # Create Pod Identity Association for Training Operator
        self._training_operator_pod_identity = self._create_training_operator_pod_identity()

        # T008d-1: Install Task Governance (Kueue) add-on
        # Note: Task Governance automatically configures PriorityClass per spec.md FR-004
        self._task_governance_addon = self._install_task_governance()

        # T008d-2: Install Observability add-on (Prometheus + Grafana)
        # Note: Observability add-on was already installed and auto-creates its own Pod Identity
        # Uncomment to manage via CDK after removing existing add-on:
        # self._observability_addon = self._install_observability()
        self._observability_addon = None  # Already installed externally

        # Create outputs
        self._create_outputs()

    def _create_training_operator_role(self) -> iam.Role:
        """Create IAM role for Training Operator Pod Identity.

        This role is assumed by the Training Operator controller manager pod
        via EKS Pod Identity to access SageMaker APIs for node health checks.

        EKS Pod Identity requires trust policy with both sts:AssumeRole and sts:TagSession.

        Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html
        """
        # Create custom assume role policy for EKS Pod Identity
        # Must include both sts:AssumeRole and sts:TagSession actions
        assume_role_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("pods.eks.amazonaws.com")],
                    actions=["sts:AssumeRole", "sts:TagSession"],
                )
            ]
        )

        role = iam.Role(
            self,
            "TrainingOperatorRole",
            role_name=f"{self.env_config.resource_prefix}-training-operator-role",
            assumed_by=iam.ServicePrincipal("pods.eks.amazonaws.com"),  # Placeholder, overridden below
            description="IAM role for HyperPod Training Operator Pod Identity",
        )

        # Override the assume role policy with our custom one that includes sts:TagSession
        cfn_role = role.node.default_child
        cfn_role.assume_role_policy_document = assume_role_policy.to_json()

        # Attach the managed policy for Training Operator
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSageMakerHyperPodTrainingOperatorAccess"
            )
        )

        cdk.Tags.of(role).add(
            "Name", f"{self.env_config.resource_prefix}-training-operator-role"
        )

        return role

    def _create_training_operator_pod_identity(self) -> eks.CfnPodIdentityAssociation:
        """Create EKS Pod Identity Association for Training Operator.

        This associates the IAM role with the Training Operator's ServiceAccount,
        allowing the controller manager to access AWS APIs.
        """
        association = eks.CfnPodIdentityAssociation(
            self,
            "TrainingOperatorPodIdentity",
            cluster_name=self._eks_cluster.cluster_name,
            namespace="aws-hyperpod",
            service_account="hp-training-operator-controller-manager",
            role_arn=self._training_operator_role.role_arn,
        )

        # Ensure association is created after the add-on (which creates the ServiceAccount)
        association.add_dependency(self._training_operator_addon)

        cdk.Tags.of(association).add("Component", "training-operator")

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
        addon = eks.CfnAddon(
            self,
            "TrainingOperatorAddon",
            addon_name=self.TRAINING_OPERATOR_ADDON,
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
            tags=[
                cdk.CfnTag(key="Name", value=f"{self.env_config.resource_prefix}-training-operator"),
                cdk.CfnTag(key="Component", value="training-operator"),
                cdk.CfnTag(key="ManagedBy", value="cdk"),
            ],
        )

        # Add description tag
        cdk.Tags.of(addon).add(
            "Description",
            "HyperPod Training Operator for PyTorchJob/TFJob CRD management",
        )

        return addon

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
        addon = eks.CfnAddon(
            self,
            "TaskGovernanceAddon",
            addon_name=self.TASK_GOVERNANCE_ADDON,
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
            tags=[
                cdk.CfnTag(key="Name", value=f"{self.env_config.resource_prefix}-task-governance"),
                cdk.CfnTag(key="Component", value="task-governance"),
                cdk.CfnTag(key="ManagedBy", value="cdk"),
            ],
        )

        # Ensure Task Governance is installed after Training Operator
        # for proper CRD dependency resolution
        addon.add_dependency(self._training_operator_addon)

        cdk.Tags.of(addon).add(
            "Description",
            "HyperPod Task Governance - Kueue for workload scheduling and Gang Scheduling",
        )

        return addon

    def _install_observability(self) -> eks.CfnAddon:
        """Install HyperPod Observability add-on (T008d-2).

        Observability provides:
        - Node Exporter for system metrics
        - DCGM Exporter for GPU metrics
        - kube-state-metrics for K8s resource metrics
        - EFA Exporter for network metrics
        - Metrics forwarded to Amazon Managed Prometheus
        - Dashboards in Amazon Managed Grafana

        Reference:
        - spec.md FR-007/FR-016: Observability requirements
        - https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-observability-addon-setup.html
        """
        addon = eks.CfnAddon(
            self,
            "ObservabilityAddon",
            addon_name=self.OBSERVABILITY_ADDON,
            cluster_name=self._eks_cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
            tags=[
                cdk.CfnTag(key="Name", value=f"{self.env_config.resource_prefix}-observability"),
                cdk.CfnTag(key="Component", value="observability"),
                cdk.CfnTag(key="ManagedBy", value="cdk"),
            ],
        )

        # Ensure Observability is installed after Training Operator
        # for proper training job metrics collection
        addon.add_dependency(self._training_operator_addon)

        cdk.Tags.of(addon).add(
            "Description",
            "HyperPod Observability for cluster monitoring via Amazon Managed Prometheus/Grafana",
        )

        return addon

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        # T008d-1 outputs
        cdk.CfnOutput(
            self,
            "TrainingOperatorAddonName",
            value=self._training_operator_addon.addon_name,
            description="HyperPod Training Operator add-on name",
            export_name=f"{self.env_config.resource_prefix}-training-operator-addon",
        )

        cdk.CfnOutput(
            self,
            "TaskGovernanceAddonName",
            value=self._task_governance_addon.addon_name,
            description="HyperPod Task Governance add-on name - includes PriorityClass config",
            export_name=f"{self.env_config.resource_prefix}-task-governance-addon",
        )

        # T008d-2 outputs (only if Observability is enabled)
        if self._observability_addon is not None:
            cdk.CfnOutput(
                self,
                "ObservabilityAddonName",
                value=self._observability_addon.addon_name,
                description="HyperPod Observability add-on name - Amazon Managed Prometheus and Grafana",
                export_name=f"{self.env_config.resource_prefix}-observability-addon",
            )
        else:
            cdk.CfnOutput(
                self,
                "ObservabilityAddonStatus",
                value="Disabled - requires Amazon Managed Service for Prometheus workspace",
                description="Observability add-on status",
            )

    @property
    def training_operator_addon(self) -> eks.CfnAddon:
        """Get Training Operator add-on."""
        return self._training_operator_addon

    @property
    def task_governance_addon(self) -> eks.CfnAddon:
        """Get Task Governance add-on."""
        return self._task_governance_addon

    @property
    def observability_addon(self) -> eks.CfnAddon | None:
        """Get Observability add-on (may be None if managed externally)."""
        return self._observability_addon
