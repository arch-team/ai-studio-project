"""AWS Integration Test Configuration.

Provides fixtures and utilities for AWS integration testing.
"""

import os
from typing import Any

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "aws_integration: mark test as requiring AWS credentials")
    config.addinivalue_line("markers", "hyperpod: mark test as HyperPod-specific")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Skip AWS tests if credentials not available."""
    import boto3

    try:
        boto3.client("sts").get_caller_identity()
        aws_available = True
    except Exception:
        aws_available = False

    if not aws_available:
        skip_aws = pytest.mark.skip(reason="AWS credentials not available")
        for item in items:
            if "aws_integration" in item.keywords:
                item.add_marker(skip_aws)


@pytest.fixture(scope="session")
def aws_region() -> str:
    """Get AWS region from environment."""
    return os.environ.get("AWS_REGION", "us-west-2")


@pytest.fixture(scope="session")
def aws_account_id() -> str | None:
    """Get AWS account ID (for ARN validation)."""
    import boto3

    try:
        return boto3.client("sts").get_caller_identity()["Account"]
    except Exception:
        return None


@pytest.fixture(scope="session")
def s3_test_config() -> dict[str, Any]:
    """S3 test configuration from environment."""
    return {
        "bucket_name": os.environ.get("S3_TEST_BUCKET", "ai-training-platform-integration-test"),
        "kms_key_id": os.environ.get("S3_TEST_KMS_KEY_ID"),
        "prefix": os.environ.get("S3_TEST_PREFIX", "integration-tests/"),
    }


@pytest.fixture(scope="session")
def hyperpod_test_config() -> dict[str, Any]:
    """HyperPod test configuration from environment."""
    return {
        "cluster_name": os.environ.get("HYPERPOD_TEST_CLUSTER_NAME"),
        "enable_write_tests": os.environ.get("HYPERPOD_ENABLE_WRITE_TESTS", "false").lower() == "true",
    }
