"""S3 Integration Tests - Real AWS environment validation.

These tests require actual AWS credentials and S3 bucket access.
Run with: pytest -m aws_integration tests/integration/aws/test_s3_integration.py -v

NOTE: Tests are skipped because S3StorageClient has not been migrated to the
new modular architecture yet. This module will be re-enabled once the S3 storage
functionality is migrated to src/shared/infrastructure/storage/.
"""

import pytest

# Skip entire module - implementation not yet migrated
pytestmark = [
    pytest.mark.skip(reason="S3StorageClient not migrated to modules/ structure yet"),
    pytest.mark.aws_integration,
    pytest.mark.slow,
]


class TestS3StorageClientIntegration:
    """Placeholder for S3 integration tests."""

    def test_placeholder(self) -> None:
        """Placeholder test - will be replaced when S3 client is migrated."""
        pass
