"""Performance test configuration."""

import pytest


@pytest.fixture
def benchmark_iterations() -> int:
    """Number of iterations for performance benchmarks."""
    return 100


@pytest.fixture
def concurrent_users() -> int:
    """Number of concurrent users for load testing."""
    return 10
