"""
Pytest configuration and shared fixtures for CDK tests.

This module provides common fixtures used across all test modules,
including CDK App instances and environment configurations.
"""

import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template

from config import EnvironmentConfig, EnvironmentType


# =============================================================================
# Environment Configuration Fixtures
# =============================================================================


@pytest.fixture
def test_account() -> str:
    """Test AWS account ID."""
    return "123456789012"


@pytest.fixture
def test_region() -> str:
    """Test AWS region."""
    return "us-east-1"


@pytest.fixture
def dev_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """Development environment configuration."""
    return EnvironmentConfig.for_dev(account=test_account, region=test_region)


@pytest.fixture
def staging_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """Staging environment configuration."""
    return EnvironmentConfig.for_staging(account=test_account, region=test_region)


@pytest.fixture
def prod_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """Production environment configuration."""
    return EnvironmentConfig.for_prod(account=test_account, region=test_region)


# =============================================================================
# CDK App Fixtures
# =============================================================================


@pytest.fixture
def cdk_app() -> cdk.App:
    """Create a fresh CDK App for each test."""
    return cdk.App()


@pytest.fixture
def cdk_env(test_account: str, test_region: str) -> cdk.Environment:
    """CDK Environment for stack deployment."""
    return cdk.Environment(account=test_account, region=test_region)


# =============================================================================
# Helper Functions
# =============================================================================


def get_template(stack: cdk.Stack) -> Template:
    """Synthesize a stack and return its CloudFormation template for assertions.

    Args:
        stack: CDK Stack to synthesize

    Returns:
        Template object for making assertions
    """
    return Template.from_stack(stack)


def assert_resource_count(template: Template, resource_type: str, count: int) -> None:
    """Assert that a template contains exactly the specified number of resources.

    Args:
        template: CloudFormation template
        resource_type: AWS resource type (e.g., "AWS::S3::Bucket")
        count: Expected number of resources
    """
    template.resource_count_is(resource_type, count)


def assert_resource_properties(
    template: Template,
    resource_type: str,
    properties: dict,
) -> None:
    """Assert that a resource exists with the specified properties.

    Args:
        template: CloudFormation template
        resource_type: AWS resource type
        properties: Expected resource properties
    """
    template.has_resource_properties(resource_type, properties)
