"""Database fixtures for testing."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock AsyncSession for database operations.

    Use this fixture when testing code that uses SQLAlchemy async sessions
    without needing actual database connectivity.
    """
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def mock_async_session_maker(mock_session: AsyncMock) -> MagicMock:
    """Mock async session maker for dependency injection.

    Use this to mock the get_db dependency in FastAPI endpoints.
    """
    session_maker = MagicMock()
    session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    return session_maker


@pytest.fixture
def mock_result() -> MagicMock:
    """Mock database result for query operations."""
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalars = MagicMock()
    result.scalars.return_value.all = MagicMock(return_value=[])
    result.scalars.return_value.first = MagicMock(return_value=None)
    return result
