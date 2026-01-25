"""Shared conftest - exports common fixtures for all test levels.

Import fixtures from this file in test-level conftest.py files:
    from tests.shared.conftest import *
"""


# Re-export all fixtures from fixture modules
from tests.shared.fixtures.auth import (
    admin_user_data,
    engineer_user_data,
    expired_token_payload,
    fast_password_hasher,
    inactive_user_data,
    jwt_manager,
    jwt_secret_key,
    locked_user_data,
    mock_jwt_manager,
    mock_settings,
    password_hasher,
    password_validator,
    project_manager_user_data,
    sample_token_payload,
    sample_user_data,
    viewer_user_data,
)
from tests.shared.fixtures.database import (
    mock_async_session_maker,
    mock_result,
    mock_session,
)
from tests.shared.fixtures.mocks import (
    mock_event_bus,
    mock_http_client,
    mock_repository,
)

# Make fixtures available via pytest_plugins
__all__ = [
    # Database
    "mock_session",
    "mock_async_session_maker",
    "mock_result",
    # Auth
    "jwt_secret_key",
    "mock_settings",
    "jwt_manager",
    "mock_jwt_manager",
    "password_hasher",
    "fast_password_hasher",
    "password_validator",
    "sample_user_data",
    "admin_user_data",
    "project_manager_user_data",
    "engineer_user_data",
    "viewer_user_data",
    "locked_user_data",
    "inactive_user_data",
    "sample_token_payload",
    "expired_token_payload",
    # Mocks
    "mock_repository",
    "mock_event_bus",
    "mock_http_client",
]
