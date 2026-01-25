"""Async testing utilities."""

import asyncio
from collections.abc import Awaitable
from typing import Any, TypeVar
from unittest.mock import AsyncMock

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    """Run an async function synchronously.

    Useful for testing async code in synchronous contexts.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    return asyncio.get_event_loop().run_until_complete(coro)


def async_return(value: T) -> AsyncMock:
    """Create an AsyncMock that returns the given value.

    Args:
        value: The value to return from the mock

    Returns:
        AsyncMock configured to return the value
    """
    mock = AsyncMock(return_value=value)
    return mock


def async_raise(exception: Exception) -> AsyncMock:
    """Create an AsyncMock that raises the given exception.

    Args:
        exception: The exception to raise

    Returns:
        AsyncMock configured to raise the exception
    """
    mock = AsyncMock(side_effect=exception)
    return mock


async def async_list(items: list[T]) -> list[T]:
    """Async wrapper for returning a list.

    Useful for mocking async iterators or queries.

    Args:
        items: The list to return

    Returns:
        The same list (awaitable)
    """
    return items


class AsyncContextManagerMock:
    """Mock for async context managers.

    Usage:
        mock_cm = AsyncContextManagerMock(return_value=some_value)
        async with mock_cm as value:
            assert value == some_value
    """

    def __init__(
        self,
        return_value: Any = None,
        enter_exception: Exception | None = None,
        exit_exception: Exception | None = None,
    ):
        self.return_value = return_value
        self.enter_exception = enter_exception
        self.exit_exception = exit_exception
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> Any:
        self.entered = True
        if self.enter_exception:
            raise self.enter_exception
        return self.return_value

    async def __aexit__(self, *args: Any) -> None:
        self.exited = True
        if self.exit_exception:
            raise self.exit_exception
