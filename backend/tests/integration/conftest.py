"""Integration Test Configuration - Shared fixtures for integration tests."""

from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.shared.infrastructure.config import get_settings
from src.shared.infrastructure.database import import_all_models
from src.shared.infrastructure.security.constants import PASSWORD_BCRYPT_COST
from src.shared.infrastructure.security.jwt import JWTManager
from src.shared.infrastructure.security.password import PasswordHasher

# 确保所有 ORM 模型在建立映射前已加载（跨模块 relationship 需要）
import_all_models()

# Note: client fixture is inherited from tests/conftest.py


# =============================================================================
# Real Database Session Fixture
# =============================================================================


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供真实 MySQL 会话，测试结束自动回滚。

    使用独立 engine + NullPool，避免与全局连接池/事件循环冲突
    （全局 engine 在导入时建池，pytest-asyncio 为每个测试创建独立事件循环，
    复用池中连接会触发 "Event loop is closed"）。

    前置条件: 可连接的 MySQL 且已 alembic upgrade head
      (docker compose up -d mysql && alembic upgrade head)。
    """
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        poolclass=NullPool,
    )
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()

    await engine.dispose()


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest.fixture
def jwt_manager() -> JWTManager:
    """JWTManager instance using test settings."""
    # JWTManager reads settings internally via get_settings()
    # We need to ensure proper settings are available
    return JWTManager()


@pytest.fixture
def password_hasher() -> PasswordHasher:
    """PasswordHasher for creating test user passwords."""
    return PasswordHasher(cost_factor=PASSWORD_BCRYPT_COST)


@pytest.fixture
def test_password() -> str:
    """Standard test password meeting all requirements."""
    return "TestP@ssw0rd123!"


@pytest.fixture
def test_password_hash(password_hasher: PasswordHasher, test_password: str) -> str:
    """Hashed version of test password."""
    return password_hasher.hash_password(test_password)


# =============================================================================
# Token Generation Fixtures
# =============================================================================


@pytest.fixture
def admin_access_token(jwt_manager: JWTManager) -> str:
    """Access token for admin user."""
    return jwt_manager.create_access_token(
        user_id=1,
        username="admin",
        email="admin@example.com",
        role="admin",
    )


@pytest.fixture
def engineer_access_token(jwt_manager: JWTManager) -> str:
    """Access token for engineer user."""
    return jwt_manager.create_access_token(
        user_id=3,
        username="engineer",
        email="engineer@example.com",
        role="engineer",
    )


@pytest.fixture
def viewer_access_token(jwt_manager: JWTManager) -> str:
    """Access token for viewer user."""
    return jwt_manager.create_access_token(
        user_id=4,
        username="viewer",
        email="viewer@example.com",
        role="viewer",
    )


@pytest.fixture
def expired_access_token(jwt_manager: JWTManager) -> str:
    """Expired access token for testing."""
    return jwt_manager.create_access_token(
        user_id=1,
        username="testuser",
        email="test@example.com",
        role="engineer",
        expires_delta=timedelta(seconds=-1),
    )


@pytest.fixture
def refresh_token(jwt_manager: JWTManager) -> str:
    """Valid refresh token for testing."""
    return jwt_manager.create_refresh_token(user_id=1)


@pytest.fixture
def expired_refresh_token(jwt_manager: JWTManager) -> str:
    """Expired refresh token for testing."""
    return jwt_manager.create_refresh_token(
        user_id=1,
        expires_delta=timedelta(seconds=-1),
    )


# =============================================================================
# Authorization Header Helpers
# =============================================================================


@pytest.fixture
def admin_auth_headers(admin_access_token: str) -> dict[str, str]:
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_access_token}"}


@pytest.fixture
def engineer_auth_headers(engineer_access_token: str) -> dict[str, str]:
    """Authorization headers for engineer user."""
    return {"Authorization": f"Bearer {engineer_access_token}"}


@pytest.fixture
def viewer_auth_headers(viewer_access_token: str) -> dict[str, str]:
    """Authorization headers for viewer user."""
    return {"Authorization": f"Bearer {viewer_access_token}"}


@pytest.fixture
def expired_auth_headers(expired_access_token: str) -> dict[str, str]:
    """Authorization headers with expired token."""
    return {"Authorization": f"Bearer {expired_access_token}"}


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def local_account_create_data() -> dict[str, Any]:
    """Data for creating a local account."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "NewUser@Pass123!",
        "display_name": "New User",
        "role": "engineer",
    }


@pytest.fixture
def login_request_data() -> dict[str, Any]:
    """Data for local login request."""
    return {
        "username": "testuser",
        "password": "TestP@ssw0rd123!",
    }


@pytest.fixture
def password_change_data() -> dict[str, Any]:
    """Data for password change request."""
    return {
        "current_password": "TestP@ssw0rd123!",
        "new_password": "NewP@ssw0rd456!",
    }


@pytest.fixture
def weak_password_data() -> dict[str, Any]:
    """Data with weak password for testing validation."""
    return {
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "weak",
        "display_name": "Weak Password User",
        "role": "engineer",
    }


# =============================================================================
# SSO Test Fixtures
# =============================================================================


@pytest.fixture
def sso_user_groups() -> dict[str, list]:
    """Sample SSO user groups for role mapping tests."""
    return {
        "admin_groups": ["AI-Platform-Admins", "General-Users"],
        "manager_groups": ["AI-Platform-ProjectManagers", "General-Users"],
        "engineer_groups": ["AI-Platform-Engineers", "General-Users"],
        "viewer_groups": ["AI-Platform-Viewers", "General-Users"],
        "no_mapping_groups": ["Other-Group", "Unknown-Group"],
        "multiple_groups": [
            "AI-Platform-Admins",
            "AI-Platform-Engineers",
        ],  # Should map to admin (highest)
    }


@pytest.fixture
def mock_sso_user_info() -> dict[str, Any]:
    """Mock SSO user info from IAM Identity Center."""
    return {
        "identity_id": "sso-user-123",
        "username": "sso_user",
        "email": "sso@example.com",
        "display_name": "SSO User",
        "groups": ["AI-Platform-Engineers"],
    }
