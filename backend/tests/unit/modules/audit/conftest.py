"""Audit module test fixtures."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_audit_log_repository() -> AsyncMock:
    """Mock IAuditLogRepository for testing audit services."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_user_id = AsyncMock(return_value=[])
    repo.get_by_entity = AsyncMock(return_value=[])
    repo.get_by_action = AsyncMock(return_value=[])
    repo.get_by_date_range = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    return repo
