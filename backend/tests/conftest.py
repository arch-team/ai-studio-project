"""Pytest Configuration - Shared fixtures and configuration."""

import pytest
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing API endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
