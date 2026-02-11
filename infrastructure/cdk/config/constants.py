"""CDK 常量 — 集中管理硬编码值和魔术字符串。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EksAddonNames:
    """EKS Add-on 名称常量。"""

    # HyperPod Add-ons
    TRAINING_OPERATOR: str = "amazon-sagemaker-hyperpod-training-operator"
    TASK_GOVERNANCE: str = "amazon-sagemaker-hyperpod-taskgovernance"
    OBSERVABILITY: str = "amazon-sagemaker-hyperpod-observability"

    # 核心 EKS Add-ons
    EBS_CSI_DRIVER: str = "aws-ebs-csi-driver"
    FSX_CSI_DRIVER: str = "aws-fsx-csi-driver"
    VPC_CNI: str = "vpc-cni"
    COREDNS: str = "coredns"
    KUBE_PROXY: str = "kube-proxy"
    POD_IDENTITY_AGENT: str = "eks-pod-identity-agent"

    # 社区 Add-ons
    CERT_MANAGER: str = "cert-manager"


@dataclass(frozen=True)
class KubernetesNamespaces:
    """Kubernetes 命名空间常量。"""

    KUBE_SYSTEM: str = "kube-system"
    CERT_MANAGER: str = "cert-manager"
    HYPERPOD: str = "aws-hyperpod"
    HYPERPOD_OBSERVABILITY: str = "hyperpod-observability"
    KUEUE_SYSTEM: str = "kueue-system"


@dataclass(frozen=True)
class HelmChartConfig:
    """Helm Chart 配置常量。"""

    # cert-manager
    CERT_MANAGER_VERSION: str = "v1.17.2"
    CERT_MANAGER_REPOSITORY: str = "https://charts.jetstack.io"
    CERT_MANAGER_RELEASE: str = "cert-manager"

    # HyperPod dependencies
    HYPERPOD_DEPENDENCIES_RELEASE: str = "hyperpod-dependencies"


@dataclass(frozen=True)
class SageMakerInstanceTypes:
    """SageMaker HyperPod 实例类型常量。"""

    CONTROLLER: str = "ml.m5.xlarge"
    SYSTEM: str = "ml.m5.4xlarge"

    # GPU 实例
    GPU_P4D: str = "ml.p4d.24xlarge"
    GPU_P5: str = "ml.p5.48xlarge"
    GPU_G5: str = "ml.g5.xlarge"
    GPU_G5_2XLARGE: str = "ml.g5.2xlarge"


@dataclass(frozen=True)
class Timeouts:
    """CDK Duration 常量 (分钟)。"""

    HELM_CHART: int = 15
    CERT_MANAGER: int = 15
    EKS_CLUSTER: int = 30


@dataclass(frozen=True)
class ServiceAccountNames:
    """Kubernetes ServiceAccount 名称常量。"""

    EBS_CSI_CONTROLLER: str = "ebs-csi-controller-sa"
    FSX_CSI_CONTROLLER: str = "fsx-csi-controller-sa"

    # HyperPod
    TRAINING_OPERATOR: str = "hp-training-operator-controller-manager"
    OBSERVABILITY_COLLECTOR: str = "hyperpod-observability-operator-otel-collector"


@dataclass(frozen=True)
class InstanceGroupNames:
    """HyperPod 实例组名称常量。"""

    CONTROLLER: str = "controller-group"
    SYSTEM: str = "system-group"
    GPU_TRAINING: str = "gpu-training-group"


@dataclass(frozen=True)
class ManagedPolicyNames:
    """AWS 托管策略名称常量。"""

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
    """标准标签键常量。"""

    NAME: str = "Name"
    ENVIRONMENT: str = "Environment"
    MANAGED_BY: str = "ManagedBy"
    COMPONENT: str = "Component"
    SAGEMAKER: str = "SageMaker"

    # Kubernetes 标签
    K8S_CLUSTER_TYPE: str = "kubernetes.io/cluster-type"
    K8S_CLUSTER_AUTOSCALER: str = "k8s.io/cluster-autoscaler/enabled"


class ProjectPaths:
    """项目路径常量.

    集中管理所有硬编码路径，避免各模块使用 Path(__file__) 计算相对路径。
    所有字段为类级常量，无需实例化。
    """

    CDK_ROOT: Path = Path(__file__).parent.parent
    RESOURCES_DIR: Path = CDK_ROOT / "resources"
    HELM_CHARTS_DIR: Path = RESOURCES_DIR / "helm_charts"
    HYPERPOD_HELM_CHART: Path = HELM_CHARTS_DIR / "HyperPodHelmChart"
    SCRIPTS_DIR: Path = RESOURCES_DIR / "scripts"
    ASSETS_DIR: Path = CDK_ROOT / "assets"
    LIFECYCLE_SCRIPTS_DIR: Path = ASSETS_DIR / "lifecycle-scripts"


# 单例实例
EKS_ADDON_NAMES = EksAddonNames()
K8S_NAMESPACES = KubernetesNamespaces()
HELM_CONFIG = HelmChartConfig()
SAGEMAKER_INSTANCES = SageMakerInstanceTypes()
TIMEOUTS = Timeouts()
SERVICE_ACCOUNTS = ServiceAccountNames()
INSTANCE_GROUPS = InstanceGroupNames()
MANAGED_POLICIES = ManagedPolicyNames()
TAG_KEYS = TagKeys()
