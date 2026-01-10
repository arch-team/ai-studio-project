"""
Unit tests for environment configuration module.

Tests cover:
- Environment factory methods (for_dev, for_staging, for_prod)
- Configuration validation
- Resource prefix generation
- CDK Environment conversion
"""

import pytest

import aws_cdk as cdk

from config import (
    DatabaseConfig,
    DeploymentMode,
    EksAddonVersions,
    EksConfig,
    EnvironmentConfig,
    EnvironmentType,
    ProtectionConfig,
    StorageConfig,
    VpcConfig,
    get_environment_config,
)


class TestEnvironmentType:
    """Tests for EnvironmentType enum."""

    def test_environment_types_exist(self) -> None:
        """Verify all expected environment types are defined."""
        assert EnvironmentType.DEV.value == "dev"
        assert EnvironmentType.STAGING.value == "staging"
        assert EnvironmentType.PROD.value == "prod"


class TestDeploymentMode:
    """Tests for DeploymentMode enum."""

    def test_deployment_modes_exist(self) -> None:
        """Verify all deployment modes are defined."""
        assert DeploymentMode.SINGLE_AZ.value == "single-az"
        assert DeploymentMode.MULTI_AZ.value == "multi-az"
        assert DeploymentMode.HYBRID.value == "hybrid"


class TestVpcConfig:
    """Tests for VPC configuration."""

    def test_default_values(self) -> None:
        """Verify default VPC configuration values."""
        config = VpcConfig()
        assert config.cidr == "10.0.0.0/16"
        assert config.max_azs == 3
        assert config.nat_gateways == 2
        assert config.deployment_mode == DeploymentMode.MULTI_AZ

    def test_custom_values(self) -> None:
        """Verify custom VPC configuration."""
        config = VpcConfig(
            cidr="172.16.0.0/16",
            max_azs=2,
            nat_gateways=1,
            deployment_mode=DeploymentMode.SINGLE_AZ,
        )
        assert config.cidr == "172.16.0.0/16"
        assert config.max_azs == 2
        assert config.nat_gateways == 1


class TestDatabaseConfig:
    """Tests for database configuration."""

    def test_default_values(self) -> None:
        """Verify default database configuration."""
        config = DatabaseConfig()
        assert config.min_acu == 0.5
        assert config.max_acu == 16.0
        assert config.backup_retention_days == 7
        assert config.enable_proxy is True

    def test_dev_acu_can_pause(self) -> None:
        """Verify dev environment can use 0.5 ACU (pause capability)."""
        config = DatabaseConfig(min_acu=0.5)
        assert config.min_acu == 0.5


class TestStorageConfig:
    """Tests for storage configuration."""

    def test_default_values(self) -> None:
        """Verify default storage configuration."""
        config = StorageConfig()
        assert config.fsx_storage_capacity_gib == 10 * 1024  # 10 TiB
        assert config.fsx_throughput_per_tb == 500
        assert config.checkpoint_retention_days == 90
        assert config.checkpoint_ia_transition_days == 30


class TestEksConfig:
    """Tests for EKS configuration."""

    def test_default_values(self) -> None:
        """Verify default EKS configuration."""
        config = EksConfig()
        assert config.kubernetes_version == "1.33"
        assert "p4d.24xlarge" in config.node_instance_types
        assert "p5.48xlarge" in config.node_instance_types
        assert config.min_nodes == 2
        assert config.max_nodes == 100

    def test_addon_versions_included(self) -> None:
        """Verify addon versions are included in EKS config."""
        config = EksConfig()
        assert config.addon_versions is not None
        assert config.addon_versions.ebs_csi.startswith("v")
        assert config.addon_versions.vpc_cni.startswith("v")


class TestEksAddonVersions:
    """Tests for EKS Add-on versions configuration."""

    def test_default_values(self) -> None:
        """Verify default addon versions."""
        versions = EksAddonVersions()
        assert versions.ebs_csi == "v1.54.0-eksbuild.1"
        assert versions.fsx_csi == "v1.8.0-eksbuild.1"
        assert versions.vpc_cni == "v1.21.1-eksbuild.1"
        assert versions.coredns == "v1.12.4-eksbuild.1"
        assert versions.kube_proxy == "v1.33.5-eksbuild.2"

    def test_k8s_133_factory(self) -> None:
        """Verify K8s 1.33 factory method returns correct versions."""
        versions = EksAddonVersions.for_k8s_1_33()
        assert "1.33" in versions.kube_proxy or "v1.33" in versions.kube_proxy
        assert versions.ebs_csi.startswith("v1.5")

    def test_k8s_132_factory(self) -> None:
        """Verify K8s 1.32 factory method returns correct versions."""
        versions = EksAddonVersions.for_k8s_1_32()
        assert "1.32" in versions.kube_proxy or "v1.32" in versions.kube_proxy
        assert versions.ebs_csi.startswith("v1.5")

    def test_version_format(self) -> None:
        """Verify all versions follow expected format."""
        versions = EksAddonVersions()
        for attr in ["ebs_csi", "fsx_csi", "vpc_cni", "coredns", "kube_proxy"]:
            version = getattr(versions, attr)
            # Format: vX.Y.Z-eksbuild.N
            assert version.startswith("v"), f"{attr} should start with 'v'"
            assert "eksbuild" in version, f"{attr} should contain 'eksbuild'"


class TestProtectionConfig:
    """Tests for resource protection configuration."""

    def test_default_values(self) -> None:
        """Verify default protection configuration (dev-like)."""
        config = ProtectionConfig()
        assert config.removal_policy == cdk.RemovalPolicy.DESTROY
        assert config.enable_deletion_protection is False
        assert config.retain_on_delete is False

    def test_dev_factory(self) -> None:
        """Verify dev protection allows easy cleanup."""
        config = ProtectionConfig.for_dev()
        assert config.removal_policy == cdk.RemovalPolicy.DESTROY
        assert config.enable_deletion_protection is False
        assert config.retain_on_delete is False

    def test_staging_factory(self) -> None:
        """Verify staging protection has moderate safeguards."""
        config = ProtectionConfig.for_staging()
        assert config.removal_policy == cdk.RemovalPolicy.SNAPSHOT
        assert config.enable_deletion_protection is True
        assert config.retain_on_delete is False

    def test_prod_factory(self) -> None:
        """Verify production protection has maximum safeguards."""
        config = ProtectionConfig.for_prod()
        assert config.removal_policy == cdk.RemovalPolicy.RETAIN
        assert config.enable_deletion_protection is True
        assert config.retain_on_delete is True

    def test_environment_configs_have_correct_protection(self) -> None:
        """Verify each environment factory sets correct protection."""
        dev = EnvironmentConfig.for_dev("123456789012")
        staging = EnvironmentConfig.for_staging("123456789012")
        prod = EnvironmentConfig.for_prod("123456789012")

        # Dev: destroyable
        assert dev.protection.removal_policy == cdk.RemovalPolicy.DESTROY
        assert dev.protection.enable_deletion_protection is False

        # Staging: snapshot on delete
        assert staging.protection.removal_policy == cdk.RemovalPolicy.SNAPSHOT
        assert staging.protection.enable_deletion_protection is True

        # Prod: retain everything
        assert prod.protection.removal_policy == cdk.RemovalPolicy.RETAIN
        assert prod.protection.enable_deletion_protection is True
        assert prod.protection.retain_on_delete is True


class TestEnvironmentConfig:
    """Tests for environment configuration."""

    def test_resource_prefix(
        self, dev_config: EnvironmentConfig, prod_config: EnvironmentConfig
    ) -> None:
        """Verify resource prefix generation."""
        assert dev_config.resource_prefix == "ai-platform-dev"
        assert prod_config.resource_prefix == "ai-platform-prod"

    def test_to_cdk_environment(
        self, dev_config: EnvironmentConfig, test_account: str, test_region: str
    ) -> None:
        """Verify CDK Environment conversion."""
        cdk_env = dev_config.to_cdk_environment()
        assert cdk_env.account == test_account
        assert cdk_env.region == test_region


class TestEnvironmentFactoryMethods:
    """Tests for environment factory methods."""

    def test_for_dev(self, test_account: str, test_region: str) -> None:
        """Verify dev environment configuration."""
        config = EnvironmentConfig.for_dev(account=test_account, region=test_region)

        assert config.name == EnvironmentType.DEV
        assert config.account == test_account
        assert config.region == test_region
        # Dev uses single NAT for cost savings
        assert config.vpc.nat_gateways == 1
        # Dev can pause (0.5 ACU)
        assert config.database.min_acu == 0.5
        assert config.database.max_acu == 8.0
        # Dev has smaller node limits
        assert config.eks.min_nodes == 1
        assert config.eks.max_nodes == 10

    def test_for_staging(self, test_account: str, test_region: str) -> None:
        """Verify staging environment configuration."""
        config = EnvironmentConfig.for_staging(account=test_account, region=test_region)

        assert config.name == EnvironmentType.STAGING
        # Staging uses Multi-AZ
        assert config.vpc.deployment_mode == DeploymentMode.MULTI_AZ
        assert config.vpc.nat_gateways == 2
        # Staging has moderate scaling
        assert config.database.min_acu == 1.0
        assert config.eks.max_nodes == 50

    def test_for_prod(self, test_account: str, test_region: str) -> None:
        """Verify production environment configuration."""
        config = EnvironmentConfig.for_prod(account=test_account, region=test_region)

        assert config.name == EnvironmentType.PROD
        # Prod uses HYBRID for cost-optimized HA
        assert config.vpc.deployment_mode == DeploymentMode.HYBRID
        # Prod always warm (no cold start)
        assert config.database.min_acu == 2.0
        # Prod has longer backup retention
        assert config.database.backup_retention_days == 14
        # Prod has largest storage
        assert config.storage.fsx_storage_capacity_gib == 100 * 1024  # 100 TiB
        # Prod has highest node limits
        assert config.eks.max_nodes == 100


class TestGetEnvironmentConfig:
    """Tests for get_environment_config helper function."""

    def test_valid_environments(self, test_account: str, test_region: str) -> None:
        """Verify all valid environment names work."""
        for env_name in ["dev", "staging", "prod"]:
            config = get_environment_config(
                env_name=env_name, account=test_account, region=test_region
            )
            assert config.name.value == env_name

    def test_invalid_environment_raises(self) -> None:
        """Verify invalid environment name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_environment_config(env_name="invalid", account="123", region="us-east-1")

        assert "Invalid environment" in str(exc_info.value)
        assert "dev" in str(exc_info.value)
        assert "staging" in str(exc_info.value)
        assert "prod" in str(exc_info.value)

    def test_default_values(self) -> None:
        """Verify default account and region handling."""
        config = get_environment_config(env_name="dev")
        assert config.account == ""
        assert config.region == "us-east-1"
