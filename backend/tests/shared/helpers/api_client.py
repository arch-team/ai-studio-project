"""API test client helpers."""

from collections.abc import AsyncGenerator
from typing import Any

from httpx import ASGITransport, AsyncClient

from tests.shared.constants import TEST_API_BASE_URL


async def create_test_client(app: Any) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing API endpoints.

    Args:
        app: The FastAPI application instance

    Yields:
        AsyncClient configured for testing
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=TEST_API_BASE_URL,
    ) as client:
        yield client


class AuthenticatedClient:
    """Wrapper for AsyncClient with authentication support.

    Usage:
        async with AuthenticatedClient(app, token="...") as client:
            response = await client.get("/api/v1/users/me")
    """

    def __init__(
        self,
        app: Any,
        token: str | None = None,
        user_id: int | None = None,
    ):
        self.app = app
        self.token = token
        self.user_id = user_id
        self._client: AsyncClient | None = None

    async def __aenter__(self) -> "AuthenticatedClient":
        self._client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url=TEST_API_BASE_URL,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def headers(self) -> dict[str, str]:
        """Get authentication headers."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    async def get(self, url: str, **kwargs: Any) -> Any:
        """Send authenticated GET request."""
        assert self._client is not None
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return await self._client.get(url, headers=headers, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Any:
        """Send authenticated POST request."""
        assert self._client is not None
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return await self._client.post(url, headers=headers, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Any:
        """Send authenticated PUT request."""
        assert self._client is not None
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return await self._client.put(url, headers=headers, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> Any:
        """Send authenticated PATCH request."""
        assert self._client is not None
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return await self._client.patch(url, headers=headers, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Any:
        """Send authenticated DELETE request."""
        assert self._client is not None
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return await self._client.delete(url, headers=headers, **kwargs)
