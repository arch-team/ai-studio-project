"""
Pytest fixtures for infrastructure tests.

Provides common fixtures for:
- CDK stack testing (App and environment setup)
- Infrastructure validation testing (Kubernetes, AWS resources)
- Mock configurations
- Snapshot testing utilities

Reference: tasks.md T008g - HyperPod 基础设施验证测试
"""

import os
import sys
from typing import Generator

import pytest

# Add CDK directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cdk"))

# CDK imports (may fail if CDK not installed)
try:
    import aws_cdk as cdk
    from config import EnvironmentConfig

    CDK_AVAILABLE = True
except ImportError:
    CDK_AVAILABLE = False
    cdk = None
    EnvironmentConfig = None

# Kubernetes client imports (may fail if not installed)
try:
    from kubernetes import client, config as k8s_config

    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    client = None
    k8s_config = None

# AWS SDK imports
try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None


# ============================================================================
# CDK Test Fixtures
# ============================================================================


@pytest.fixture
def app():
    """Create a CDK App for testing."""
    if not CDK_AVAILABLE:
        pytest.skip("aws-cdk-lib not installed")
    return cdk.App()


@pytest.fixture
def dev_env_config():
    """Create a development environment configuration for testing."""
    if not CDK_AVAILABLE:
        pytest.skip("aws-cdk-lib not installed")
    return EnvironmentConfig.for_dev(
        account="123456789012",
        region="us-east-1",
    )


@pytest.fixture
def staging_env_config():
    """Create a staging environment configuration for testing."""
    if not CDK_AVAILABLE:
        pytest.skip("aws-cdk-lib not installed")
    return EnvironmentConfig.for_staging(
        account="123456789012",
        region="us-east-1",
    )


@pytest.fixture
def prod_env_config():
    """Create a production environment configuration for testing."""
    if not CDK_AVAILABLE:
        pytest.skip("aws-cdk-lib not installed")
    return EnvironmentConfig.for_prod(
        account="123456789012",
        region="us-east-1",
    )


@pytest.fixture
def cdk_env(dev_env_config):
    """Create a CDK Environment from the dev configuration."""
    if not CDK_AVAILABLE:
        pytest.skip("aws-cdk-lib not installed")
    return dev_env_config.to_cdk_environment()


@pytest.fixture(autouse=True)
def reset_environment_variables() -> Generator[None, None, None]:
    """Reset environment variables between tests."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Infrastructure Validation Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def k8s_core_client():
    """Initialize Kubernetes CoreV1Api client."""
    if not K8S_AVAILABLE:
        pytest.skip("kubernetes Python client not installed")

    try:
        k8s_config.load_kube_config()
        return client.CoreV1Api()
    except Exception as e:
        pytest.skip(f"Cannot connect to Kubernetes cluster: {e}")


@pytest.fixture(scope="module")
def k8s_custom_client():
    """Initialize Kubernetes CustomObjectsApi client."""
    if not K8S_AVAILABLE:
        pytest.skip("kubernetes Python client not installed")

    try:
        k8s_config.load_kube_config()
        return client.CustomObjectsApi()
    except Exception as e:
        pytest.skip(f"Cannot connect to Kubernetes cluster: {e}")


@pytest.fixture(scope="module")
def k8s_apps_client():
    """Initialize Kubernetes AppsV1Api client."""
    if not K8S_AVAILABLE:
        pytest.skip("kubernetes Python client not installed")

    try:
        k8s_config.load_kube_config()
        return client.AppsV1Api()
    except Exception as e:
        pytest.skip(f"Cannot connect to Kubernetes cluster: {e}")


@pytest.fixture(scope="module")
def aws_session():
    """Initialize AWS boto3 session."""
    if not BOTO3_AVAILABLE:
        pytest.skip("boto3 not installed")

    try:
        return boto3.Session()
    except Exception as e:
        pytest.skip(f"Cannot initialize AWS session: {e}")


@pytest.fixture(scope="module")
def infra_config():
    """Infrastructure test configuration."""
    return {
        "cluster_name": os.environ.get("CLUSTER_NAME", "ai-platform-hyperpod"),
        "namespace_training": os.environ.get("NAMESPACE_TRAINING", "training-jobs"),
        "namespace_monitoring": os.environ.get(
            "NAMESPACE_MONITORING", "hyperpod-observability"
        ),
        "namespace_kueue": os.environ.get("NAMESPACE_KUEUE", "kueue-system"),
        "namespace_spaces": os.environ.get("NAMESPACE_SPACES", "sagemaker-spaces"),
        "aws_region": os.environ.get("AWS_REGION", "us-east-1"),
    }


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "infrastructure: marks tests as infrastructure validation tests"
    )
    config.addinivalue_line("markers", "cdk: marks tests as CDK stack tests")
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring live cluster"
    )
