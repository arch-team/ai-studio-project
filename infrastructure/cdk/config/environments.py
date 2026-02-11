"""多环境部署配置 (dev/staging/prod)。"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

import aws_cdk as cdk


class DeploymentMode(str, Enum):
    """VPC 部署模式：成本与可用性的权衡。"""

    SINGLE_AZ = "single-az"
    MULTI_AZ = "multi-az"
    HYBRID = "hybrid"


class EnvironmentType(str, Enum):
    """平台环境类型。"""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass(frozen=True)
class VpcConfig:
    """VPC 配置。"""

    cidr: str = "10.0.0.0/16"
    max_azs: int = 3
    nat_gateways: int = 2
    deployment_mode: DeploymentMode = DeploymentMode.MULTI_AZ


@dataclass(frozen=True)
class DatabaseConfig:
    """Aurora Serverless v2 配置。"""

    min_acu: float = 0.5
    max_acu: float = 16.0
    backup_retention_days: int = 7
    enable_proxy: bool = True


@dataclass(frozen=True)
class StorageConfig:
    """S3 和 FSx 存储配置。"""

    fsx_storage_capacity_gib: int = 10 * 1024  # 10 TiB default
    fsx_throughput_per_tb: int = 500  # Cost-optimized default
    checkpoint_retention_days: int = 90
    checkpoint_ia_transition_days: int = 30


@dataclass(frozen=True)
class EksAddonVersions:
    """EKS Add-on 版本配置，与特定 Kubernetes 版本兼容。

    升级 K8s 版本时需同步更新。
    Reference: https://docs.aws.amazon.com/eks/latest/userguide/managing-add-ons.html
    """

    ebs_csi: str = "v1.54.0-eksbuild.1"
    fsx_csi: str = "v1.8.0-eksbuild.1"
    vpc_cni: str = "v1.21.1-eksbuild.1"
    coredns: str = "v1.12.4-eksbuild.1"
    kube_proxy: str = "v1.33.5-eksbuild.2"
    gpu_ami_type: str = "AL2023_x86_64_NVIDIA"
    neuron_ami_type: str = "AL2023_x86_64_NEURON"

    @classmethod
    def for_k8s_1_32(cls) -> "EksAddonVersions":
        """K8s 1.32 兼容版本 (AL2 系列 AMI)。"""
        return cls(
            ebs_csi="v1.52.0-eksbuild.1",
            fsx_csi="v1.8.0-eksbuild.1",
            vpc_cni="v1.19.2-eksbuild.1",
            coredns="v1.11.4-eksbuild.2",
            kube_proxy="v1.32.3-eksbuild.2",
            gpu_ami_type="AL2_x86_64_GPU",
            neuron_ami_type="AL2_x86_64_GPU",
        )


@dataclass(frozen=True)
class GpuInstanceGroupConfig:
    """GPU 实例组配置。"""

    instance_type: str = "ml.g5.2xlarge"
    instance_count: int = 1
    enabled: bool = True


@dataclass(frozen=True)
class EksConfig:
    """EKS 集群配置。"""

    kubernetes_version: str = "1.33"
    # 默认值 = K8s 1.33 兼容版本（即 EksAddonVersions 的类默认值）
    addon_versions: EksAddonVersions = field(default_factory=EksAddonVersions)
    node_instance_types: tuple[str, ...] = (
        "p4d.24xlarge",
        "p5.48xlarge",
        "trn1.32xlarge",
    )
    min_nodes: int = 2
    max_nodes: int = 100
    gpu_instance_group: GpuInstanceGroupConfig = field(
        default_factory=GpuInstanceGroupConfig
    )


@dataclass(frozen=True)
class ObservabilityConfig:
    """可观测性配置。"""

    enable_amp: bool = True
    amp_retention_days: int = 150


@dataclass(frozen=True)
class ProtectionConfig:
    """资源保护配置（按环境区分删除策略）。"""

    removal_policy: cdk.RemovalPolicy = cdk.RemovalPolicy.DESTROY
    enable_deletion_protection: bool = False
    retain_on_delete: bool = False

    @classmethod
    def for_dev(cls) -> "ProtectionConfig":
        """开发环境: 允许轻松清理。"""
        return cls(
            removal_policy=cdk.RemovalPolicy.DESTROY,
            enable_deletion_protection=False,
            retain_on_delete=False,
        )

    @classmethod
    def for_staging(cls) -> "ProtectionConfig":
        """预发布环境: 适度保护。"""
        return cls(
            removal_policy=cdk.RemovalPolicy.DESTROY,
            enable_deletion_protection=True,
            retain_on_delete=False,
        )

    @classmethod
    def for_prod(cls) -> "ProtectionConfig":
        """生产环境: 最大保护，保留所有有状态资源。"""
        return cls(
            removal_policy=cdk.RemovalPolicy.RETAIN,
            enable_deletion_protection=True,
            retain_on_delete=True,
        )


# EnvironmentType → ProtectionConfig 工厂方法的显式映射
# 避免使用 getattr + 字符串拼接的脆弱模式
_PROTECTION_FACTORY: dict[EnvironmentType, Callable[[], ProtectionConfig]] = {
    EnvironmentType.DEV: ProtectionConfig.for_dev,
    EnvironmentType.STAGING: ProtectionConfig.for_staging,
    EnvironmentType.PROD: ProtectionConfig.for_prod,
}


@dataclass(frozen=True)
class EnvironmentConfig:
    """完整的环境配置，提供 dev/staging/prod 工厂方法。"""

    name: EnvironmentType
    account: str
    region: str
    vpc: VpcConfig = field(default_factory=VpcConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    eks: EksConfig = field(default_factory=EksConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    protection: ProtectionConfig = field(default_factory=ProtectionConfig)

    def to_cdk_environment(self) -> cdk.Environment:
        """转换为 CDK Environment。"""
        return cdk.Environment(account=self.account, region=self.region)

    @property
    def resource_prefix(self) -> str:
        """生成统一的资源命名前缀。"""
        return f"ai-platform-{self.name.value}"

    @classmethod
    def _create_environment(
        cls,
        name: EnvironmentType,
        account: str,
        region: str,
        *,
        vpc_nat_gateways: int,
        vpc_deployment_mode: DeploymentMode,
        db_min_acu: float,
        db_max_acu: float,
        db_backup_days: int,
        fsx_storage_gib: int,
        fsx_throughput: int,
        eks_min_nodes: int,
        eks_max_nodes: int,
        gpu_instance_count: int = 1,
        gpu_enabled: bool = True,
    ) -> "EnvironmentConfig":
        return cls(
            name=name,
            account=account,
            region=region,
            vpc=VpcConfig(
                deployment_mode=vpc_deployment_mode,
                nat_gateways=vpc_nat_gateways,
            ),
            database=DatabaseConfig(
                min_acu=db_min_acu,
                max_acu=db_max_acu,
                backup_retention_days=db_backup_days,
            ),
            storage=StorageConfig(
                fsx_storage_capacity_gib=fsx_storage_gib,
                fsx_throughput_per_tb=fsx_throughput,
            ),
            eks=EksConfig(
                min_nodes=eks_min_nodes,
                max_nodes=eks_max_nodes,
                gpu_instance_group=GpuInstanceGroupConfig(
                    instance_count=gpu_instance_count,
                    enabled=gpu_enabled,
                ),
            ),
            protection=_PROTECTION_FACTORY[name](),
        )

    @classmethod
    def for_dev(cls, account: str, region: str = "us-east-1") -> "EnvironmentConfig":
        """开发环境的工厂方法 - 成本优化配置。"""
        return cls._create_environment(
            name=EnvironmentType.DEV,
            account=account,
            region=region,
            vpc_nat_gateways=1,  # 单 NAT 节省成本
            vpc_deployment_mode=DeploymentMode.MULTI_AZ,  # Aurora 需要至少 2 个 AZ
            db_min_acu=0.5,  # 可暂停节省成本
            db_max_acu=8.0,
            db_backup_days=7,
            fsx_storage_gib=12000,  # ~11.7 TiB (匹配已部署 dev 环境容量，避免缩容触发 replacement)
            fsx_throughput=500,
            eks_min_nodes=1,
            eks_max_nodes=10,
            gpu_instance_count=1,  # 开发环境: 1 个 GPU 实例
        )

    @classmethod
    def for_staging(
        cls, account: str, region: str = "us-east-1"
    ) -> "EnvironmentConfig":
        """预发布环境的工厂方法 - 中等规模配置。"""
        return cls._create_environment(
            name=EnvironmentType.STAGING,
            account=account,
            region=region,
            vpc_nat_gateways=2,
            vpc_deployment_mode=DeploymentMode.MULTI_AZ,
            db_min_acu=1.0,
            db_max_acu=16.0,
            db_backup_days=7,
            fsx_storage_gib=20 * 1024,  # 20 TiB
            fsx_throughput=500,
            eks_min_nodes=2,
            eks_max_nodes=50,
            gpu_instance_count=2,  # 预发布环境: 2 个 GPU 实例
        )

    @classmethod
    def for_prod(cls, account: str, region: str = "us-east-1") -> "EnvironmentConfig":
        """生产环境的工厂方法 - 高可用和性能优化配置。"""
        return cls._create_environment(
            name=EnvironmentType.PROD,
            account=account,
            region=region,
            vpc_nat_gateways=2,
            vpc_deployment_mode=DeploymentMode.HYBRID,  # 成本优化的高可用
            db_min_acu=2.0,  # 始终保持温暖，无冷启动
            db_max_acu=16.0,
            db_backup_days=14,
            fsx_storage_gib=20 * 1024,  # 20 TiB (初始容量，FSx 支持在线扩容)
            fsx_throughput=500,  # 可根据需要升级到 1000
            eks_min_nodes=2,
            eks_max_nodes=100,
            gpu_instance_count=4,  # 生产环境: 4 个 GPU 实例
        )


def get_environment_config(
    env_name: str,
    account: str | None = None,
    region: str | None = None,
) -> EnvironmentConfig:
    """按环境名获取配置。

    Raises:
        ValueError: env_name 不是有效的环境类型时
    """
    account = account or ""
    region = region or "us-east-1"

    factory_methods = {
        "dev": EnvironmentConfig.for_dev,
        "staging": EnvironmentConfig.for_staging,
        "prod": EnvironmentConfig.for_prod,
    }

    if env_name not in factory_methods:
        valid_envs = ", ".join(factory_methods.keys())
        raise ValueError(
            f"Invalid environment: {env_name}. Valid options: {valid_envs}"
        )

    return factory_methods[env_name](account=account, region=region)
