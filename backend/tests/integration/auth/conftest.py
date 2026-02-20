"""Auth Integration Tests - Fixtures and configuration."""

from unittest.mock import AsyncMock

import pytest

from src.main import app
from src.modules.auth.api.dependencies import (
    get_account_service,
    get_auth_service,
    get_password_service,
)
from src.modules.auth.application.services import (
    AccountService,
    AuthService,
    PasswordService,
)
from src.modules.auth.domain.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
)


@pytest.fixture
def mock_auth_service() -> AsyncMock:
    """Mock AuthService for integration tests."""
    service = AsyncMock(spec=AuthService)

    # 默认行为: 认证失败抛出 InvalidCredentialsError
    service.local_login.side_effect = InvalidCredentialsError("Invalid credentials")
    service.refresh_access_token.side_effect = InvalidTokenError("Invalid token")
    service.get_user_by_id.return_value = None

    return service


@pytest.fixture
def mock_account_service() -> AsyncMock:
    """Mock AccountService for integration tests."""
    service = AsyncMock(spec=AccountService)
    return service


@pytest.fixture
def mock_password_service() -> AsyncMock:
    """Mock PasswordService for integration tests."""
    service = AsyncMock(spec=PasswordService)

    # 密码重置请求: 始终返回 None (不泄露用户存在性)
    service.request_password_reset.return_value = None

    # 密码重置确认: 默认 token 无效
    service.confirm_password_reset.side_effect = InvalidTokenError("Invalid or expired reset token")

    return service


@pytest.fixture(autouse=True)
def override_auth_dependencies(
    mock_auth_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_password_service: AsyncMock,
) -> None:
    """自动覆盖 auth 模块的依赖注入 (每个测试方法生效)."""
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_account_service] = lambda: mock_account_service
    app.dependency_overrides[get_password_service] = lambda: mock_password_service

    yield

    # 清理: 测试后恢复依赖
    app.dependency_overrides.clear()
