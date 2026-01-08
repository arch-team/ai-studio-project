"""
Tests for environment configuration module.

Validates that environment configurations are correctly generated
for dev, staging, and production environments.
"""

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cdk"))

from config import (
    DatabaseConfig,
    DeploymentMode,
    EksConfig,
    EnvironmentConfig,
    EnvironmentType,
    StorageConfig,
    VpcConfig,
    get_environment_config,
)


class TestVpcConfig:
    """Tests for VpcConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default VPC configuration values."""
        config = VpcConfig()
        assert config.cidr == "10.0.0.0/16"
        assert config.max_azs == 3
        assert config.nat_gateways == 2
        assert config.deployment_mode == DeploymentMode.MULTI_AZ

    def test_custom_values(self) -> None:
        """Test custom VPC configuration values."""
        config = VpcConfig(
            cidr="192.168.0.0/16",
            max_azs=2,
            nat_gateways=1,
            deployment_mode=DeploymentMode.SINGLE_AZ,
        )
        assert config.cidr == "192.168.0.0/16"
        assert config.max_azs == 2
        assert config.nat_gateways == 1
        assert config.deployment_mode == DeploymentMode.SINGLE_AZ


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default database configuration values."""
        config = DatabaseConfig()
        assert config.min_acu == 0.5
        assert config.max_acu == 16.0
        assert config.backup_retention_days == 7
        assert config.enable_proxy is True

    def test_prod_values(self) -> None:
        """Test production-like database configuration."""
        config = DatabaseConfig(
            min_acu=2.0,
            max_acu=16.0,
            backup_retention_days=14,
            enable_proxy=True,
        )
        assert config.min_acu == 2.0
        assert config.backup_retention_days == 14


class TestStorageConfig:
    """Tests for StorageConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default storage configuration values."""
        config = StorageConfig()
        assert config.fsx_storage_capacity_gib == 10 * 1024  # 10 TiB
        assert config.fsx_throughput_per_tb == 500
        assert config.checkpoint_retention_days == 90
        assert config.checkpoint_ia_transition_days == 30


class TestEksConfig:
    """Tests for EksConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default EKS configuration values."""
        config = EksConfig()
        assert config.kubernetes_version == "1.32"
        assert "p4d.24xlarge" in config.node_instance_types
        assert "p5.48xlarge" in config.node_instance_types
        assert "trn1.32xlarge" in config.node_instance_types
        assert config.min_nodes == 2
        assert config.max_nodes == 100


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig dataclass."""

    def test_dev_environment(self) -> None:
        """Test development environment configuration."""
        config = EnvironmentConfig.for_dev(
            account="123456789012",
            region="us-east-1",
        )
        assert config.name == EnvironmentType.DEV
        assert config.account == "123456789012"
        assert config.region == "us-east-1"
        assert config.vpc.deployment_mode == DeploymentMode.SINGLE_AZ
        assert config.vpc.nat_gateways == 1
        assert config.database.min_acu == 0.5
        assert config.eks.max_nodes == 10

    def test_staging_environment(self) -> None:
        """Test staging environment configuration."""
        config = EnvironmentConfig.for_staging(
            account="123456789012",
            region="us-east-1",
        )
        assert config.name == EnvironmentType.STAGING
        assert config.vpc.deployment_mode == DeploymentMode.MULTI_AZ
        assert config.vpc.nat_gateways == 2
        assert config.database.min_acu == 1.0
        assert config.eks.max_nodes == 50

    def test_prod_environment(self) -> None:
        """Test production environment configuration."""
        config = EnvironmentConfig.for_prod(
            account="123456789012",
            region="us-east-1",
        )
        assert config.name == EnvironmentType.PROD
        assert config.vpc.deployment_mode == DeploymentMode.HYBRID
        assert config.database.min_acu == 2.0
        assert config.database.backup_retention_days == 14
        assert config.storage.fsx_storage_capacity_gib == 100 * 1024  # 100 TiB
        assert config.eks.max_nodes == 100

    def test_resource_prefix(self) -> None:
        """Test resource prefix generation."""
        dev_config = EnvironmentConfig.for_dev(account="123456789012")
        assert dev_config.resource_prefix == "ai-platform-dev"

        prod_config = EnvironmentConfig.for_prod(account="123456789012")
        assert prod_config.resource_prefix == "ai-platform-prod"

    def test_to_cdk_environment(self) -> None:
        """Test CDK Environment conversion."""
        config = EnvironmentConfig.for_dev(
            account="123456789012",
            region="eu-west-1",
        )
        cdk_env = config.to_cdk_environment()
        assert cdk_env.account == "123456789012"
        assert cdk_env.region == "eu-west-1"


class TestGetEnvironmentConfig:
    """Tests for get_environment_config function."""

    def test_get_dev_config(self) -> None:
        """Test getting dev configuration by name."""
        config = get_environment_config("dev", account="123456789012")
        assert config.name == EnvironmentType.DEV

    def test_get_staging_config(self) -> None:
        """Test getting staging configuration by name."""
        config = get_environment_config("staging", account="123456789012")
        assert config.name == EnvironmentType.STAGING

    def test_get_prod_config(self) -> None:
        """Test getting production configuration by name."""
        config = get_environment_config("prod", account="123456789012")
        assert config.name == EnvironmentType.PROD

    def test_invalid_environment_raises_error(self) -> None:
        """Test that invalid environment name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_environment_config("invalid")
        assert "Invalid environment" in str(exc_info.value)
        assert "dev" in str(exc_info.value)
        assert "staging" in str(exc_info.value)
        assert "prod" in str(exc_info.value)

    def test_default_region(self) -> None:
        """Test default region is us-east-1."""
        config = get_environment_config("dev", account="123456789012")
        assert config.region == "us-east-1"

    def test_custom_region(self) -> None:
        """Test custom region configuration."""
        config = get_environment_config(
            "dev",
            account="123456789012",
            region="ap-northeast-1",
        )
        assert config.region == "ap-northeast-1"
