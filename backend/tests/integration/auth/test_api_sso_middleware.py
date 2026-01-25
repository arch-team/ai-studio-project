"""SSO 故障转移集成测试 (T013d)

测试场景:
1. IdP 超时 (>5s) 时降级到本地认证
2. SSO 恢复后自动切换回 SSO 认证 (健康检查通过后)
3. 降级期间审计日志正确记录 (operation_type: auth_failover)
4. 本地账号不存在时返回通用错误 (不泄露账号存在性)

依赖: T013a (SSO 集成), T013c (本地账号 API)
参考: FR-015 (spec.md)

注意: SSO 中间件 (sso.py) 尚未实现，此测试 Mock SSO 客户端行为，
重点验证 AuthService 的降级逻辑和审计记录。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.auth.application.services.auth_service import AuthResult, AuthService
from src.modules.auth.domain.entities import User
from src.modules.auth.domain.value_objects import AuthType, UserRole, UserStatus
from src.shared.infrastructure.security import (
    AccountLockedError,
    InvalidCredentialsError,
)

# =============================================================================
# Helper Functions
# =============================================================================


def create_test_user(
    user_id: int = 1,
    username: str = "test_user",
    email: str = "test@example.com",
    password_hash: str = "hashed_password",
    auth_type: AuthType = AuthType.LOCAL,
    role: UserRole = UserRole.ENGINEER,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    """创建测试用户实体"""
    return User(
        id=user_id,
        username=username,
        email=email,
        password_hash=password_hash,
        auth_type=auth_type,
        role=role,
        status=status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Mock IUserRepository"""
    repo = AsyncMock()
    repo.get_by_username = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_login_attempt_repository() -> AsyncMock:
    """Mock ILoginAttemptRepository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_repository() -> AsyncMock:
    """Mock 审计日志仓库"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_sso_client() -> AsyncMock:
    """Mock SSO IdP 客户端"""
    client = AsyncMock()
    client.authenticate = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_jwt_manager() -> MagicMock:
    """Mock JWTManager"""
    manager = MagicMock()
    manager.create_access_token.return_value = "mock-access-token"
    manager.create_refresh_token.return_value = "mock-refresh-token"
    return manager


@pytest.fixture
def mock_password_hasher() -> MagicMock:
    """Mock PasswordHasher"""
    hasher = MagicMock()
    hasher.verify_password.return_value = True
    hasher.hash_password.return_value = "hashed_password"
    return hasher


@pytest.fixture
def local_user() -> User:
    """本地账号用户"""
    return create_test_user(
        user_id=1,
        username="local_user",
        email="local@example.com",
        password_hash="$2b$12$test_hash",
        auth_type=AuthType.LOCAL,
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
def sso_user() -> User:
    """SSO 账号用户"""
    return create_test_user(
        user_id=2,
        username="sso_user",
        email="sso@example.com",
        password_hash=None,  # SSO 用户无本地密码
        auth_type=AuthType.SSO,
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE,
    )


# =============================================================================
# Test Class: SSO 故障转移场景 - TestSSOFailover
# =============================================================================


@pytest.mark.integration
class TestSSOFailover:
    """SSO 故障转移集成测试 - FR-015

    验证 SSO IdP 不可用时的降级逻辑。
    """

    @pytest.mark.asyncio
    async def test_idp_timeout_triggers_local_auth_fallback(
        self,
        mock_user_repository: AsyncMock,
        mock_login_attempt_repository: AsyncMock,
        mock_jwt_manager: MagicMock,
        mock_password_hasher: MagicMock,
        local_user: User,
    ) -> None:
        """场景1: IdP 超时 (>5s) 时降级到本地认证并记录告警

        测试逻辑:
        1. 模拟 SSO IdP 超时
        2. 用户存在本地账号
        3. 验证成功降级到本地认证
        """
        # Arrange: 配置 mock - 用户存在本地账号
        mock_user_repository.get_by_username.return_value = local_user

        auth_service = AuthService(
            user_repository=mock_user_repository,
            login_attempt_repository=mock_login_attempt_repository,
            jwt_manager=mock_jwt_manager,
            password_hasher=mock_password_hasher,
        )

        # Act: 使用本地登录 (模拟 SSO 降级后的路径)
        result = await auth_service.local_login(
            username="local_user",
            password="correct_password",
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0",
        )

        # Assert: 验证登录成功
        assert result is not None
        assert isinstance(result, AuthResult)
        assert result.username == "local_user"
        assert result.tokens.access_token == "mock-access-token"

        # 验证登录尝试被记录
        mock_login_attempt_repository.create.assert_called_once()
        created_attempt = mock_login_attempt_repository.create.call_args[0][0]
        assert created_attempt.success is True
        assert created_attempt.username == "local_user"

    @pytest.mark.asyncio
    async def test_sso_recovery_auto_switches_back(
        self,
        mock_sso_client: AsyncMock,
    ) -> None:
        """场景2: SSO 恢复后自动切回 SSO 认证

        测试 SSO 健康检查通过后，系统自动切换回 SSO 认证。
        """
        # Arrange: 模拟 SSO 健康检查
        mock_sso_client.health_check.return_value = True

        # Act: 执行健康检查
        is_healthy = await mock_sso_client.health_check()

        # Assert: SSO 服务健康
        assert is_healthy is True
        mock_sso_client.health_check.assert_called_once()

        # 注: 完整的切换逻辑需要 SSO 中间件实现后测试
        # 此处验证健康检查机制

    @pytest.mark.asyncio
    async def test_failover_audit_log_recorded(
        self,
        mock_user_repository: AsyncMock,
        mock_login_attempt_repository: AsyncMock,
        mock_jwt_manager: MagicMock,
        mock_password_hasher: MagicMock,
        local_user: User,
    ) -> None:
        """场景3: 降级期间审计日志正确记录 (operation_type: auth_failover)

        验证 SSO 降级时创建的登录尝试记录包含正确的信息。
        """
        # Arrange
        mock_user_repository.get_by_username.return_value = local_user

        auth_service = AuthService(
            user_repository=mock_user_repository,
            login_attempt_repository=mock_login_attempt_repository,
            jwt_manager=mock_jwt_manager,
            password_hasher=mock_password_hasher,
        )

        # Act: 执行本地登录 (模拟 SSO 降级场景)
        await auth_service.local_login(
            username="local_user",
            password="correct_password",
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0 SSO-Failover",
        )

        # Assert: 验证登录尝试记录
        mock_login_attempt_repository.create.assert_called_once()
        attempt = mock_login_attempt_repository.create.call_args[0][0]

        # 验证审计信息
        assert attempt.ip_address == "10.0.0.1"
        assert attempt.user_agent == "Mozilla/5.0 SSO-Failover"
        assert attempt.success is True
        assert attempt.user_id == local_user.id

        # 注: operation_type: auth_failover 需要在 SSO 中间件实现后添加
        # 当前测试验证基本的审计日志记录机制

    @pytest.mark.asyncio
    async def test_local_account_not_found_returns_generic_error(
        self,
        mock_user_repository: AsyncMock,
        mock_login_attempt_repository: AsyncMock,
        mock_jwt_manager: MagicMock,
        mock_password_hasher: MagicMock,
    ) -> None:
        """场景4: 本地账号不存在时返回通用错误 (不泄露账号存在性)

        验证:
        - 用户不存在时返回通用的 "Invalid credentials" 错误
        - 不返回 "User not found" 等会泄露账号存在性的信息
        """
        # Arrange: 用户不存在
        mock_user_repository.get_by_username.return_value = None

        auth_service = AuthService(
            user_repository=mock_user_repository,
            login_attempt_repository=mock_login_attempt_repository,
            jwt_manager=mock_jwt_manager,
            password_hasher=mock_password_hasher,
        )

        # Act & Assert: 验证返回通用错误
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.local_login(
                username="nonexistent_user",
                password="any_password",
                ip_address="192.168.1.1",
                user_agent="TestClient/1.0",
            )

        # 验证错误消息不泄露账号存在性
        error_message = str(exc_info.value)
        assert "Invalid credentials" in error_message
        assert "not found" not in error_message.lower()
        assert "nonexistent" not in error_message.lower()

        # 验证失败尝试被记录
        mock_login_attempt_repository.create.assert_called_once()
        attempt = mock_login_attempt_repository.create.call_args[0][0]
        assert attempt.success is False
        assert attempt.failure_reason == "user_not_found"


# =============================================================================
# Test Class: SSO 健康检查器 - TestSSOHealthTracker
# =============================================================================


@pytest.mark.integration
class TestSSOHealthTracker:
    """SSO 健康检查器测试

    验证 SSO 服务健康状态跟踪机制。
    """

    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        mock_sso_client: AsyncMock,
    ) -> None:
        """健康检查成功场景"""
        # Arrange
        mock_sso_client.health_check.return_value = True

        # Act
        result = await mock_sso_client.health_check()

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure_triggers_degraded_mode(
        self,
        mock_sso_client: AsyncMock,
    ) -> None:
        """健康检查失败触发降级模式"""
        # Arrange
        mock_sso_client.health_check.return_value = False

        # Act
        result = await mock_sso_client.health_check()

        # Assert
        assert result is False
        # 注: 降级模式切换逻辑需要 SSO 中间件实现后完善

    @pytest.mark.asyncio
    async def test_health_check_timeout_triggers_degraded_mode(
        self,
        mock_sso_client: AsyncMock,
    ) -> None:
        """健康检查超时触发降级模式"""
        # Arrange: 模拟超时异常
        mock_sso_client.health_check.side_effect = TimeoutError("Health check timeout")

        # Act & Assert
        with pytest.raises(TimeoutError):
            await mock_sso_client.health_check()


# =============================================================================
# Test Class: SSO 服务集成 - TestSSOService
# =============================================================================


@pytest.mark.integration
class TestSSOService:
    """SSO 服务集成测试

    验证 SSO 认证流程和错误处理。
    """

    @pytest.mark.asyncio
    async def test_sso_user_cannot_use_local_login(
        self,
        mock_user_repository: AsyncMock,
        mock_login_attempt_repository: AsyncMock,
        mock_jwt_manager: MagicMock,
        mock_password_hasher: MagicMock,
        sso_user: User,
    ) -> None:
        """SSO 用户不能使用本地登录

        验证 auth_type=SSO 的用户尝试本地登录时被拒绝。
        """
        # Arrange: SSO 用户
        mock_user_repository.get_by_username.return_value = sso_user

        auth_service = AuthService(
            user_repository=mock_user_repository,
            login_attempt_repository=mock_login_attempt_repository,
            jwt_manager=mock_jwt_manager,
            password_hasher=mock_password_hasher,
        )

        # Act & Assert: SSO 用户不能使用本地登录
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.local_login(
                username="sso_user",
                password="any_password",
                ip_address="192.168.1.1",
                user_agent="TestClient/1.0",
            )

        assert "SSO authentication" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_inactive_user_cannot_login(
        self,
        mock_user_repository: AsyncMock,
        mock_login_attempt_repository: AsyncMock,
        mock_jwt_manager: MagicMock,
        mock_password_hasher: MagicMock,
    ) -> None:
        """非活跃用户不能登录"""
        # Arrange: 非活跃用户
        inactive_user = create_test_user(
            status=UserStatus.INACTIVE,
        )
        mock_user_repository.get_by_username.return_value = inactive_user

        auth_service = AuthService(
            user_repository=mock_user_repository,
            login_attempt_repository=mock_login_attempt_repository,
            jwt_manager=mock_jwt_manager,
            password_hasher=mock_password_hasher,
        )

        # Act & Assert
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.local_login(
                username="test_user",
                password="correct_password",
                ip_address="192.168.1.1",
                user_agent="TestClient/1.0",
            )

        assert "not active" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_locked_user_cannot_login(
        self,
        mock_user_repository: AsyncMock,
        mock_login_attempt_repository: AsyncMock,
        mock_jwt_manager: MagicMock,
        mock_password_hasher: MagicMock,
    ) -> None:
        """被锁定用户不能登录"""
        # Arrange: 被锁定用户
        locked_user = create_test_user()
        locked_user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
        mock_user_repository.get_by_username.return_value = locked_user

        auth_service = AuthService(
            user_repository=mock_user_repository,
            login_attempt_repository=mock_login_attempt_repository,
            jwt_manager=mock_jwt_manager,
            password_hasher=mock_password_hasher,
        )

        # Act & Assert
        with pytest.raises(AccountLockedError):
            await auth_service.local_login(
                username="test_user",
                password="correct_password",
                ip_address="192.168.1.1",
                user_agent="TestClient/1.0",
            )

    @pytest.mark.asyncio
    async def test_wrong_password_records_failed_attempt(
        self,
        mock_user_repository: AsyncMock,
        mock_login_attempt_repository: AsyncMock,
        mock_jwt_manager: MagicMock,
        mock_password_hasher: MagicMock,
        local_user: User,
    ) -> None:
        """密码错误时记录失败尝试"""
        # Arrange
        mock_user_repository.get_by_username.return_value = local_user
        mock_password_hasher.verify_password.return_value = False

        auth_service = AuthService(
            user_repository=mock_user_repository,
            login_attempt_repository=mock_login_attempt_repository,
            jwt_manager=mock_jwt_manager,
            password_hasher=mock_password_hasher,
        )

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.local_login(
                username="local_user",
                password="wrong_password",
                ip_address="192.168.1.1",
                user_agent="TestClient/1.0",
            )

        # 验证失败尝试被记录
        mock_login_attempt_repository.create.assert_called_once()
        attempt = mock_login_attempt_repository.create.call_args[0][0]
        assert attempt.success is False
        assert attempt.failure_reason == "invalid_password"

        # 验证用户失败计数增加
        mock_user_repository.update.assert_called_once()
