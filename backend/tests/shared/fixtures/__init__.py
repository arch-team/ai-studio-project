"""Shared fixtures for all test levels."""

from tests.shared.fixtures.auth import (
    admin_user_data,
    engineer_user_data,
    fast_password_hasher,
    jwt_manager,
    mock_jwt_manager,
    password_hasher,
    password_validator,
    sample_token_payload,
    sample_user_data,
    viewer_user_data,
)
from tests.shared.fixtures.database import mock_async_session_maker, mock_session
from tests.shared.fixtures.mocks import (
    mock_repository,
    mock_settings,
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
