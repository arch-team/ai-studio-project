"""
Configuration module for AI Training Platform CDK Stacks.

This module exports environment configuration classes for multi-environment deployments.
"""

from .environments import (
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

__all__ = [
    "DatabaseConfig",
    "DeploymentMode",
    "EksAddonVersions",
    "EksConfig",
    "EnvironmentConfig",
    "EnvironmentType",
    "ProtectionConfig",
    "StorageConfig",
    "VpcConfig",
    "get_environment_config",
]
