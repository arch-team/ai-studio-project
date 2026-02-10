"""
Environment configuration for AI Training Platform CDK Stacks.

This module provides strongly-typed configuration classes for multi-environment
deployments (dev, staging, prod) following AWS Well-Architected Framework best practices.
"""

from dataclasses import dataclass, field
from enum import Enum

import aws_cdk as cdk


class DeploymentMode(str, Enum):
    """VPC deployment mode for cost vs availability trade-off.

    Attributes:
        SINGLE_AZ: Single AZ deployment for dev/test (lowest cost, no HA)
        MULTI_AZ: Multi-AZ deployment for production (full HA)
        HYBRID: Hybrid mode - compute multi-AZ, data layer single AZ (cost optimized)
    """

    SINGLE_AZ = "single-az"
    MULTI_AZ = "multi-az"
    HYBRID = "hybrid"


class EnvironmentType(str, Enum):
    """Environment types for the platform."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass(frozen=True)
class VpcConfig:
    """VPC configuration with sensible defaults.

    Attributes:
        cidr: VPC CIDR block (default: 10.0.0.0/16, supports ~1200 nodes)
        max_azs: Maximum number of AZs to use
        nat_gateways: Number of NAT Gateways (2 for cost-optimized HA)
        deployment_mode: Deployment mode for AZ strategy
    """

    cidr: str = "10.0.0.0/16"
    max_azs: int = 3
    nat_gateways: int = 2
    deployment_mode: DeploymentMode = DeploymentMode.MULTI_AZ


@dataclass(frozen=True)
class DatabaseConfig:
    """Aurora Serverless v2 configuration.

    Attributes:
        min_acu: Minimum Aurora Capacity Units (0.5 allows pause in dev)
        max_acu: Maximum Aurora Capacity Units
        backup_retention_days: Backup retention period
        enable_proxy: Enable RDS Proxy for connection pooling
    """

    min_acu: float = 0.5
    max_acu: float = 16.0
    backup_retention_days: int = 7
    enable_proxy: bool = True


@dataclass(frozen=True)
class StorageConfig:
    """Storage configuration for S3 and FSx.

    Attributes:
        fsx_storage_capacity_gib: FSx for Lustre storage capacity in GiB
        fsx_throughput_per_tb: FSx throughput tier (500 or 1000 MB/s/TiB)
        checkpoint_retention_days: Cold checkpoint retention period
        checkpoint_ia_transition_days: Days before transition to Standard-IA
    """

    fsx_storage_capacity_gib: int = 10 * 1024  # 10 TiB default
    fsx_throughput_per_tb: int = 500  # Cost-optimized default
    checkpoint_retention_days: int = 90
    checkpoint_ia_transition_days: int = 30


@dataclass(frozen=True)
class EksAddonVersions:
    """EKS Add-on versions compatible with specific Kubernetes versions.

    These versions are validated for compatibility with EKS.
    Update these when upgrading Kubernetes version.

    Reference: https://docs.aws.amazon.com/eks/latest/userguide/managing-add-ons.html

    Attributes:
        ebs_csi: Amazon EBS CSI Driver version
        fsx_csi: Amazon FSx CSI Driver version
        vpc_cni: Amazon VPC CNI version
        coredns: CoreDNS version
        kube_proxy: kube-proxy version
    """

    ebs_csi: str = "v1.54.0-eksbuild.1"
    fsx_csi: str = "v1.8.0-eksbuild.1"
    vpc_cni: str = "v1.21.1-eksbuild.1"
    coredns: str = "v1.12.4-eksbuild.1"
    kube_proxy: str = "v1.33.5-eksbuild.2"

    @classmethod
    def for_k8s_1_33(cls) -> "EksAddonVersions":
        """Factory method for Kubernetes 1.33 compatible versions.

        注意: 版本号与类默认值保持一致，更新时需同步修改。
        """
        return cls()

    @classmethod
    def for_k8s_1_32(cls) -> "EksAddonVersions":
        """Factory method for Kubernetes 1.32 compatible versions."""
        return cls(
            ebs_csi="v1.52.0-eksbuild.1",
            fsx_csi="v1.8.0-eksbuild.1",
            vpc_cni="v1.19.2-eksbuild.1",
            coredns="v1.11.4-eksbuild.2",
            kube_proxy="v1.32.3-eksbuild.2",
        )


@dataclass(frozen=True)
class GpuInstanceGroupConfig:
    """GPU 实例组配置.

    Attributes:
        instance_type: GPU 实例类型 (e.g., ml.g5.2xlarge)
        instance_count: 实例数量
        enabled: 是否启用 GPU 实例组
    """

    instance_type: str = "ml.g5.2xlarge"
    instance_count: int = 1
    enabled: bool = True


@dataclass(frozen=True)
class EksConfig:
    """EKS cluster configuration.

    Attributes:
        kubernetes_version: EKS Kubernetes version
        addon_versions: EKS Add-on versions compatible with kubernetes_version
        node_instance_types: List of GPU instance types for HyperPod
        min_nodes: Minimum nodes in auto-scaling group
        max_nodes: Maximum nodes in auto-scaling group
        gpu_instance_group: GPU 实例组配置 (ml.g5.2xlarge)
    """

    kubernetes_version: str = "1.33"
    addon_versions: EksAddonVersions = field(
        default_factory=EksAddonVersions.for_k8s_1_33
    )
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
    """可观测性配置.

    Attributes:
        enable_amp: 是否启用 Amazon Managed Prometheus
        amp_retention_days: AMP 指标保留天数
    """

    enable_amp: bool = True
    amp_retention_days: int = 150


@dataclass(frozen=True)
class ProtectionConfig:
    """Resource protection configuration for different environments.

    Attributes:
        removal_policy: CDK RemovalPolicy for stateful resources (databases, buckets)
        enable_deletion_protection: Enable deletion protection for databases
        retain_on_delete: Whether to retain resources when stack is deleted
    """

    removal_policy: cdk.RemovalPolicy = cdk.RemovalPolicy.DESTROY
    enable_deletion_protection: bool = False
    retain_on_delete: bool = False

    @classmethod
    def for_dev(cls) -> "ProtectionConfig":
        """Development: allow easy cleanup."""
        return cls(
            removal_policy=cdk.RemovalPolicy.DESTROY,
            enable_deletion_protection=False,
            retain_on_delete=False,
        )

    @classmethod
    def for_staging(cls) -> "ProtectionConfig":
        """Staging: moderate protection - same as dev for resource lifecycle."""
        return cls(
            removal_policy=cdk.RemovalPolicy.DESTROY,
            enable_deletion_protection=True,
            retain_on_delete=False,
        )

    @classmethod
    def for_prod(cls) -> "ProtectionConfig":
        """Production: maximum protection - retain all stateful resources."""
        return cls(
            removal_policy=cdk.RemovalPolicy.RETAIN,
            enable_deletion_protection=True,
            retain_on_delete=True,
        )


@dataclass(frozen=True)
class EnvironmentConfig:
    """Complete environment configuration.

    This class aggregates all configuration for a specific environment
    and provides factory methods for standard configurations.
    """

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
        """Convert to CDK Environment for stack deployment."""
        return cdk.Environment(account=self.account, region=self.region)

    @property
    def resource_prefix(self) -> str:
        """Generate consistent resource naming prefix."""
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
        """通用的环境配置创建方法。

        Args:
            name: 环境类型
            account: AWS 账户 ID
            region: AWS 区域
            vpc_nat_gateways: NAT Gateway 数量
            vpc_deployment_mode: VPC 部署模式
            db_min_acu: 数据库最小 ACU
            db_max_acu: 数据库最大 ACU
            db_backup_days: 备份保留天数
            fsx_storage_gib: FSx 存储容量 (GiB)
            fsx_throughput: FSx 吞吐量 (MB/s/TiB)
            eks_min_nodes: EKS 最小节点数
            eks_max_nodes: EKS 最大节点数
            gpu_instance_count: GPU 实例数量
            gpu_enabled: 是否启用 GPU 实例组

        Returns:
            配置好的 EnvironmentConfig 实例
        """
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
            protection=getattr(ProtectionConfig, f"for_{name.value}")(),
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
    """Get environment configuration by name.

    Args:
        env_name: Environment name (dev, staging, prod)
        account: AWS account ID (optional, uses CDK default if not provided)
        region: AWS region (optional, defaults to us-east-1)

    Returns:
        EnvironmentConfig for the specified environment

    Raises:
        ValueError: If env_name is not a valid environment type
    """
    # Use default values if not provided
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
