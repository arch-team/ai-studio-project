"""Pytest Configuration - Global fixtures and configuration.

This is the root conftest.py that provides global fixtures available
to all test levels (unit, integration, e2e).

Test Structure:
    tests/
    ├── conftest.py              # This file - global config
    ├── shared/                  # Shared test infrastructure
    │   ├── fixtures/            # Reusable fixtures
    │   └── helpers/             # Test utilities
    ├── unit/                    # Unit tests (no external deps)
    │   └── modules/             # Organized by business module
    ├── integration/             # Integration tests
    │   └── modules/             # Organized by business module
    ├── e2e/                     # End-to-end tests
    ├── architecture/            # Architecture compliance tests
    └── performance/             # Performance tests
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# 确保所有 ORM 模型在测试前被加载
from src.shared.infrastructure.database import import_all_models

import_all_models()

from src.main import app  # noqa: E402  # 必须在 import_all_models() 之后

# =============================================================================
# Global Fixtures
# =============================================================================


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing API endpoints.

    This is the default client fixture available to all tests.
    For more specialized clients, use fixtures from tests/shared/fixtures/.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# =============================================================================
# Pytest Hooks
# =============================================================================


def pytest_collection_modifyitems(config, items):
    """Automatically add markers based on test location."""
    for item in items:
        # Add markers based on test path
        test_path = str(item.fspath)

        if "/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in test_path:
            item.add_marker(pytest.mark.e2e)
        elif "/architecture/" in test_path:
            item.add_marker(pytest.mark.architecture)
        elif "/performance/" in test_path:
            item.add_marker(pytest.mark.performance)

        # Add AWS marker for AWS-related tests
        # Only mark tests in /aws/ or /e2e/ directories that involve real AWS calls
        # Unit tests for HyperPod exceptions (test_exception_*) don't need AWS
        if "/aws/" in test_path:
            item.add_marker(pytest.mark.aws_integration)
        elif "/e2e/" in test_path and "hyperpod" in test_path.lower():
            item.add_marker(pytest.mark.aws_integration)
