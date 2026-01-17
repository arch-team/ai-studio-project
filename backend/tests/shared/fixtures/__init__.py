"""Shared fixtures for all test levels."""

from tests.shared.fixtures.database import mock_session, mock_async_session_maker
from tests.shared.fixtures.auth import (
    jwt_manager,
    mock_jwt_manager,
    password_hasher,
    fast_password_hasher,
    password_validator,
    sample_user_data,
    admin_user_data,
    engineer_user_data,
    viewer_user_data,
    sample_token_payload,
)
from tests.shared.fixtures.mocks import (
    mock_settings,
    mock_repository,
)

__all__ = [
    # Database
    "mock_session",
    "mock_async_session_maker",
    # Auth
    "jwt_manager",
    "mock_jwt_manager",
    "password_hasher",
    "fast_password_hasher",
    "password_validator",
    "sample_user_data",
    "admin_user_data",
    "engineer_user_data",
    "viewer_user_data",
    "sample_token_payload",
    # Mocks
    "mock_settings",
    "mock_repository",
]
