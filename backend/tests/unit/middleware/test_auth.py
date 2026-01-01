"""JWT认证中间件单元测试"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.middleware.auth import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_current_superuser,
)
from models.user import User, UserRole, UserStatus
from services.auth.security import create_access_token


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_active_user():
    """模拟活跃用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = UserRole.ALGORITHM_ENGINEER
    user.status = UserStatus.ACTIVE
    user.is_active = True
    user.is_admin = False
    user.is_superuser = False
    user.is_deleted = False
    return user


@pytest.fixture
def mock_admin_user():
    """模拟管理员用户"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.status = UserStatus.ACTIVE
    user.is_active = True
    user.is_admin = True
    user.is_superuser = False
    user.is_deleted = False
    return user


@pytest.fixture
def mock_superuser():
    """模拟超级用户"""
    user = Mock(spec=User)
    user.id = 3
    user.username = "superuser"
    user.email = "superuser@example.com"
    user.role = UserRole.ADMIN
    user.status = UserStatus.ACTIVE
    user.is_active = True
    user.is_admin = True
    user.is_superuser = True
    user.is_deleted = False
    return user


@pytest.fixture
def mock_inactive_user():
    """模拟未激活用户"""
    user = Mock(spec=User)
    user.id = 4
    user.username = "inactive"
    user.email = "inactive@example.com"
    user.role = UserRole.VIEWER
    user.status = UserStatus.INACTIVE
    user.is_active = False
    user.is_admin = False
    user.is_superuser = False
    user.is_deleted = False
    return user


@pytest.fixture
def mock_deleted_user():
    """模拟已删除用户"""
    user = Mock(spec=User)
    user.id = 5
    user.username = "deleted"
    user.email = "deleted@example.com"
    user.role = UserRole.VIEWER
    user.status = UserStatus.ACTIVE
    user.is_active = True
    user.is_admin = False
    user.is_superuser = False
    user.is_deleted = True
    return user


class TestGetCurrentUser:
    """测试get_current_user函数"""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, mock_db_session, mock_active_user):
        """测试有效令牌返回用户"""
        # 创建有效的访问令牌
        token = create_access_token({"sub": str(mock_active_user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # 模拟数据库查询
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_active_user
        mock_db_session.execute.return_value = mock_result

        # 调用函数
        user = await get_current_user(credentials, mock_db_session)

        # 验证
        assert user == mock_active_user
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self, mock_db_session):
        """测试无效令牌抛出401错误"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self, mock_db_session):
        """测试过期令牌抛出401错误"""
        # 创建过期的令牌
        token = create_access_token(
            {"sub": "1"},
            expires_delta=timedelta(seconds=-1)  # 已过期
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_without_sub_raises_401(self, mock_db_session):
        """测试没有sub字段的令牌抛出401错误"""
        # 创建没有sub字段的令牌
        token = create_access_token({"username": "test"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found_raises_401(self, mock_db_session):
        """测试用户不存在抛出401错误"""
        token = create_access_token({"sub": "999"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # 模拟数据库查询返回None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self, mock_db_session, mock_inactive_user):
        """测试未激活用户抛出403错误"""
        token = create_access_token({"sub": str(mock_inactive_user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # 模拟数据库查询
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_inactive_user
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db_session)

        assert exc_info.value.status_code == 403
        assert "inactive or deleted" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_deleted_user_raises_403(self, mock_db_session, mock_deleted_user):
        """测试已删除用户抛出403错误"""
        token = create_access_token({"sub": str(mock_deleted_user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # 模拟数据库查询
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_deleted_user
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db_session)

        assert exc_info.value.status_code == 403


class TestGetCurrentActiveUser:
    """测试get_current_active_user函数"""

    @pytest.mark.asyncio
    async def test_active_user_passes(self, mock_active_user):
        """测试活跃用户通过验证"""
        user = await get_current_active_user(mock_active_user)
        assert user == mock_active_user

    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self, mock_inactive_user):
        """测试未激活用户抛出403错误"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_inactive_user)

        assert exc_info.value.status_code == 403
        assert "not active" in exc_info.value.detail


class TestGetCurrentAdminUser:
    """测试get_current_admin_user函数"""

    @pytest.mark.asyncio
    async def test_admin_user_passes(self, mock_admin_user):
        """测试管理员用户通过验证"""
        user = await get_current_admin_user(mock_admin_user)
        assert user == mock_admin_user

    @pytest.mark.asyncio
    async def test_non_admin_user_raises_403(self, mock_active_user):
        """测试非管理员用户抛出403错误"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(mock_active_user)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail


class TestGetCurrentSuperuser:
    """测试get_current_superuser函数"""

    @pytest.mark.asyncio
    async def test_superuser_passes(self, mock_superuser):
        """测试超级用户通过验证"""
        user = await get_current_superuser(mock_superuser)
        assert user == mock_superuser

    @pytest.mark.asyncio
    async def test_non_superuser_raises_403(self, mock_admin_user):
        """测试非超级用户抛出403错误"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_superuser(mock_admin_user)

        assert exc_info.value.status_code == 403
        assert "Superuser access required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_regular_user_raises_403(self, mock_active_user):
        """测试普通用户抛出403错误"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_superuser(mock_active_user)

        assert exc_info.value.status_code == 403
