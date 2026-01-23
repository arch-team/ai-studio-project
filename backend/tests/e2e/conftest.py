"""E2E test configuration - fixtures for full application testing."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from tests.shared.constants import TEST_API_BASE_URL


@pytest.fixture(scope="function")
async def app_client() -> AsyncGenerator[AsyncClient, None]:
    """Full application client for E2E testing.

    This fixture creates a client that tests the complete application
    including all middleware, dependencies, and integrations.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=TEST_API_BASE_URL,
        timeout=30.0,  # Longer timeout for E2E tests
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_client(app_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated client for E2E testing.

    Creates a test user and returns a client with valid authentication.
    """
    # TODO: Implement actual user creation and login flow
    # For now, this is a placeholder that uses a mock token
    app_client.headers["Authorization"] = "Bearer test-e2e-token"
    yield app_client
    app_client.headers.pop("Authorization", None)
