"""Pytest配置和共享fixtures"""

import pytest
import pytest_asyncio
import tempfile
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from models.base import Base
from config.database import get_db
from main import app
from models.user import User, UserRole, UserStatus, Team, Project, ProjectStatus
from services.auth.security import get_password_hash


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """创建测试数据库引擎

    使用临时文件数据库,避免内存数据库的多连接问题
    StaticPool确保所有连接共享同一个数据库实例
    """
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    test_db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # StaticPool确保连接复用
        echo=False,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    await engine.dispose()

    # 关闭文件描述符并删除临时文件
    os.close(db_fd)
    os.unlink(db_path)


@pytest_asyncio.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话

    每个测试函数使用独立的session,共享同一个engine
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,  # 防止commit后对象过期,保持已加载的关系
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine, test_db_session):
    """创建FastAPI异步测试客户端

    注意:依赖test_engine确保表已创建
    """

    async def override_get_db():
        # 为每个API请求创建新session,确保能看到已commit的数据
        async_session = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_engine, test_db_session) -> User:
    """创建测试用户"""
    # 确保依赖test_engine,表已创建
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        role=UserRole.ALGORITHM_ENGINEER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_superuser=False,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(test_engine, test_db_session) -> User:
    """创建测试管理员"""
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_superuser=False,
    )
    test_db_session.add(admin)
    await test_db_session.commit()
    await test_db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_inactive_user(test_engine, test_db_session) -> User:
    """创建未激活测试用户"""
    user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("inactivepass123"),
        full_name="Inactive User",
        role=UserRole.VIEWER,
        status=UserStatus.INACTIVE,
        is_active=False,
        is_superuser=False,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_team(test_engine, test_db_session, test_user) -> Team:
    """创建测试团队"""
    team = Team(
        name="test-team",
        description="Test Team",
        owner_id=test_user.id,
    )
    test_db_session.add(team)
    await test_db_session.commit()
    await test_db_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def test_project(test_engine, test_db_session, test_user, test_team) -> Project:
    """创建测试项目"""
    project = Project(
        name="test-project",
        description="Test Project",
        status=ProjectStatus.ACTIVE,
        owner_id=test_user.id,
        team_id=test_team.id,
        namespace=f"ai-training-{test_team.id}",
    )
    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)
    return project
