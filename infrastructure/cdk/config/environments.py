"""
Environment configuration for AI Training Platform CDK Stacks.

This module provides strongly-typed configuration classes for multi-environment
deployments (dev, staging, prod) following AWS Well-Architected Framework best practices.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import aws_cdk as cdk

if TYPE_CHECKING:
    pass


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
        """Factory method for Kubernetes 1.33 compatible versions."""
        return cls(
            ebs_csi="v1.54.0-eksbuild.1",
            fsx_csi="v1.8.0-eksbuild.1",
            vpc_cni="v1.21.1-eksbuild.1",
            coredns="v1.12.4-eksbuild.1",
            kube_proxy="v1.33.5-eksbuild.2",
        )

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
class EksConfig:
    """EKS cluster configuration.

    Attributes:
        kubernetes_version: EKS Kubernetes version
        addon_versions: EKS Add-on versions compatible with kubernetes_version
        node_instance_types: List of GPU instance types for HyperPod
        min_nodes: Minimum nodes in auto-scaling group
        max_nodes: Maximum nodes in auto-scaling group
    """
    kubernetes_version: str = "1.33"
    addon_versions: EksAddonVersions = field(
        default_factory=EksAddonVersions.for_k8s_1_33
    )
    node_instance_types: tuple[str, ...] = ("p4d.24xlarge", "p5.48xlarge", "trn1.32xlarge")
    min_nodes: int = 2
    max_nodes: int = 100


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
        """Staging: moderate protection."""
        return cls(
            removal_policy=cdk.RemovalPolicy.SNAPSHOT,
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
    protection: ProtectionConfig = field(default_factory=ProtectionConfig)

    def to_cdk_environment(self) -> cdk.Environment:
        """Convert to CDK Environment for stack deployment."""
        return cdk.Environment(account=self.account, region=self.region)

    @property
    def resource_prefix(self) -> str:
        """Generate consistent resource naming prefix."""
        return f"ai-platform-{self.name.value}"

    @classmethod
    def for_dev(cls, account: str, region: str = "us-east-1") -> "EnvironmentConfig":
        """Factory method for development environment."""
        return cls(
            name=EnvironmentType.DEV,
            account=account,
            region=region,
            vpc=VpcConfig(
                deployment_mode=DeploymentMode.MULTI_AZ,  # Aurora requires at least 2 AZs
                nat_gateways=1,  # Single NAT for cost savings in dev
            ),
            database=DatabaseConfig(
                min_acu=0.5,  # Can pause when idle
                max_acu=8.0,
            ),
            storage=StorageConfig(
                fsx_storage_capacity_gib=10 * 1024,  # 10 TiB minimum
                fsx_throughput_per_tb=500,
            ),
            eks=EksConfig(
                min_nodes=1,
                max_nodes=10,
            ),
            protection=ProtectionConfig.for_dev(),
        )

    @classmethod
    def for_staging(cls, account: str, region: str = "us-east-1") -> "EnvironmentConfig":
        """Factory method for staging environment."""
        return cls(
            name=EnvironmentType.STAGING,
            account=account,
            region=region,
            vpc=VpcConfig(
                deployment_mode=DeploymentMode.MULTI_AZ,
                nat_gateways=2,
            ),
            database=DatabaseConfig(
                min_acu=1.0,
                max_acu=16.0,
            ),
            storage=StorageConfig(
                fsx_storage_capacity_gib=20 * 1024,  # 20 TiB
                fsx_throughput_per_tb=500,
            ),
            eks=EksConfig(
                min_nodes=2,
                max_nodes=50,
            ),
            protection=ProtectionConfig.for_staging(),
        )

    @classmethod
    def for_prod(cls, account: str, region: str = "us-east-1") -> "EnvironmentConfig":
        """Factory method for production environment."""
        return cls(
            name=EnvironmentType.PROD,
            account=account,
            region=region,
            vpc=VpcConfig(
                deployment_mode=DeploymentMode.HYBRID,  # Cost-optimized HA
                nat_gateways=2,
            ),
            database=DatabaseConfig(
                min_acu=2.0,  # Always warm for no cold start
                max_acu=16.0,
                backup_retention_days=14,
            ),
            storage=StorageConfig(
                fsx_storage_capacity_gib=100 * 1024,  # 100 TiB
                fsx_throughput_per_tb=500,  # Can upgrade to 1000 if needed
                checkpoint_retention_days=90,
            ),
            eks=EksConfig(
                min_nodes=2,
                max_nodes=100,
            ),
            protection=ProtectionConfig.for_prod(),
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
        raise ValueError(f"Invalid environment: {env_name}. Valid options: {valid_envs}")

    return factory_methods[env_name](account=account, region=region)
