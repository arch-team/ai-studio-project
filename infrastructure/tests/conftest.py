"""
Pytest fixtures for infrastructure tests.

Provides common fixtures for CDK stack testing including:
- App and environment setup
- Mock configurations
- Snapshot testing utilities
"""

import os
from typing import Generator

import aws_cdk as cdk
import pytest

# Add CDK directory to path for imports
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cdk"))

from config import EnvironmentConfig, EnvironmentType


@pytest.fixture
def app() -> cdk.App:
    """Create a CDK App for testing."""
    return cdk.App()


@pytest.fixture
def dev_env_config() -> EnvironmentConfig:
    """Create a development environment configuration for testing."""
    return EnvironmentConfig.for_dev(
        account="123456789012",
        region="us-east-1",
    )


@pytest.fixture
def staging_env_config() -> EnvironmentConfig:
    """Create a staging environment configuration for testing."""
    return EnvironmentConfig.for_staging(
        account="123456789012",
        region="us-east-1",
    )


@pytest.fixture
def prod_env_config() -> EnvironmentConfig:
    """Create a production environment configuration for testing."""
    return EnvironmentConfig.for_prod(
        account="123456789012",
        region="us-east-1",
    )


@pytest.fixture
def cdk_env(dev_env_config: EnvironmentConfig) -> cdk.Environment:
    """Create a CDK Environment from the dev configuration."""
    return dev_env_config.to_cdk_environment()


@pytest.fixture(autouse=True)
def reset_environment_variables() -> Generator[None, None, None]:
    """Reset environment variables between tests."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
