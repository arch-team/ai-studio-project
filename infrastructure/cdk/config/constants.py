"""
Constants for AI Training Platform CDK.

This module centralizes all hardcoded values and magic strings
to improve maintainability and reduce duplication.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


@dataclass(frozen=True)
class EksAddonNames:
    """EKS Add-on name constants."""

    # HyperPod Add-ons
    TRAINING_OPERATOR: str = "amazon-sagemaker-hyperpod-training-operator"
    TASK_GOVERNANCE: str = "amazon-sagemaker-hyperpod-taskgovernance"
    OBSERVABILITY: str = "amazon-sagemaker-hyperpod-observability"

    # Core EKS Add-ons
    EBS_CSI_DRIVER: str = "aws-ebs-csi-driver"
    FSX_CSI_DRIVER: str = "aws-fsx-csi-driver"
    VPC_CNI: str = "vpc-cni"
    COREDNS: str = "coredns"
    KUBE_PROXY: str = "kube-proxy"
    POD_IDENTITY_AGENT: str = "eks-pod-identity-agent"

    # Community Add-ons
    CERT_MANAGER: str = "cert-manager"


@dataclass(frozen=True)
class KubernetesNamespaces:
    """Kubernetes namespace constants."""

    KUBE_SYSTEM: str = "kube-system"
    CERT_MANAGER: str = "cert-manager"
    HYPERPOD: str = "aws-hyperpod"
    HYPERPOD_OBSERVABILITY: str = "hyperpod-observability"
    KUEUE_SYSTEM: str = "kueue-system"


@dataclass(frozen=True)
class HelmChartConfig:
    """Helm chart configuration constants."""

    # cert-manager
    CERT_MANAGER_VERSION: str = "v1.17.2"
    CERT_MANAGER_REPOSITORY: str = "https://charts.jetstack.io"
    CERT_MANAGER_RELEASE: str = "cert-manager"

    # HyperPod dependencies
    HYPERPOD_DEPENDENCIES_RELEASE: str = "hyperpod-dependencies"


@dataclass(frozen=True)
class SageMakerInstanceTypes:
    """SageMaker HyperPod instance type constants."""

    # Controller/System instances
    CONTROLLER: str = "ml.m5.xlarge"
    SYSTEM: str = "ml.m5.4xlarge"

    # GPU instances
    GPU_P4D: str = "ml.p4d.24xlarge"
    GPU_P5: str = "ml.p5.48xlarge"
    GPU_G5: str = "ml.g5.xlarge"
    GPU_G5_2XLARGE: str = "ml.g5.2xlarge"


@dataclass(frozen=True)
class Timeouts:
    """CDK Duration constants (in minutes)."""

    HELM_CHART: int = 15
    CERT_MANAGER: int = 15
    EKS_CLUSTER: int = 30


@dataclass(frozen=True)
class ServiceAccountNames:
    """Kubernetes ServiceAccount name constants."""

    # EKS CSI drivers
    EBS_CSI_CONTROLLER: str = "ebs-csi-controller-sa"
    FSX_CSI_CONTROLLER: str = "fsx-csi-controller-sa"

    # HyperPod
    TRAINING_OPERATOR: str = "hp-training-operator-controller-manager"
    OBSERVABILITY_COLLECTOR: str = "hyperpod-observability-operator-otel-collector"


@dataclass(frozen=True)
class InstanceGroupNames:
    """HyperPod instance group name constants."""

    CONTROLLER: str = "controller-group"
    SYSTEM: str = "system-group"
    GPU_TRAINING: str = "gpu-training-group"


@dataclass(frozen=True)
class ManagedPolicyNames:
    """AWS Managed Policy name constants."""

    # EKS
    EKS_WORKER_NODE: str = "AmazonEKSWorkerNodePolicy"
    EKS_CNI: str = "AmazonEKS_CNI_Policy"
    ECR_READ_ONLY: str = "AmazonEC2ContainerRegistryReadOnly"
    SSM_MANAGED_INSTANCE: str = "AmazonSSMManagedInstanceCore"
    EBS_CSI_DRIVER: str = "service-role/AmazonEBSCSIDriverPolicy"
    FSX_FULL_ACCESS: str = "AmazonFSxFullAccess"

    # SageMaker
    SAGEMAKER_CLUSTER_INSTANCE: str = "AmazonSageMakerClusterInstanceRolePolicy"
    HYPERPOD_TRAINING_OPERATOR: str = "AmazonSageMakerHyperPodTrainingOperatorAccess"


@dataclass(frozen=True)
class TagKeys:
    """Standard tag key constants."""

    NAME: str = "Name"
    ENVIRONMENT: str = "Environment"
    MANAGED_BY: str = "ManagedBy"
    COMPONENT: str = "Component"
    SAGEMAKER: str = "SageMaker"

    # Kubernetes tags
    K8S_CLUSTER_TYPE: str = "kubernetes.io/cluster-type"
    K8S_CLUSTER_AUTOSCALER: str = "k8s.io/cluster-autoscaler/enabled"


@dataclass(frozen=True)
class ProjectPaths:
    """项目路径常量.

    集中管理所有硬编码路径，避免各模块使用 Path(__file__) 计算相对路径。
    """

    CDK_ROOT: ClassVar[Path] = Path(__file__).parent.parent
    RESOURCES_DIR: ClassVar[Path] = CDK_ROOT / "resources"
    HELM_CHARTS_DIR: ClassVar[Path] = RESOURCES_DIR / "helm_charts"
    HYPERPOD_HELM_CHART: ClassVar[Path] = HELM_CHARTS_DIR / "HyperPodHelmChart"
    SCRIPTS_DIR: ClassVar[Path] = RESOURCES_DIR / "scripts"
    ASSETS_DIR: ClassVar[Path] = CDK_ROOT / "assets"


# Singleton instances for easy access
EKS_ADDON_NAMES = EksAddonNames()
K8S_NAMESPACES = KubernetesNamespaces()
HELM_CONFIG = HelmChartConfig()
SAGEMAKER_INSTANCES = SageMakerInstanceTypes()
TIMEOUTS = Timeouts()
SERVICE_ACCOUNTS = ServiceAccountNames()
INSTANCE_GROUPS = InstanceGroupNames()
MANAGED_POLICIES = ManagedPolicyNames()
TAG_KEYS = TagKeys()
