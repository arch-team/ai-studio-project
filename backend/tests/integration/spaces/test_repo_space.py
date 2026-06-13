"""Space Repository Integration Tests - HyperPod backend fields persistence.

验证 Space 实体新字段 (backend, namespace, queue_name, workspace_template)
能正确持久化到 development_spaces 表并往返读取。

注意: 本测试需要真实 MySQL 数据库。如无数据库连接,测试将被跳过。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.modules.auth.infrastructure.models import UserModel
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.value_objects import (
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.modules.spaces.infrastructure.repositories import SpaceRepository
from src.shared.infrastructure.config import get_settings


@pytest.fixture
async def session() -> AsyncSession:
    """创建测试用数据库 session,如果无法连接则跳过测试。"""
    settings = get_settings()
    try:
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        # 测试连接
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))

        # 创建 session
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session_maker() as session:
            yield session
            await session.rollback()

        await engine.dispose()
    except Exception as e:
        pytest.skip(f"无法连接到数据库,跳过集成测试: {e}")


@pytest.fixture
async def test_user(session: AsyncSession) -> UserModel:
    """创建测试用户用于外键关联。"""
    user = UserModel(
        username="testuser_space",
        email="testuser_space@example.com",
        password_hash="dummy_hash",
        display_name="Test User for Space",
        role="engineer",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def space_repository(session: AsyncSession) -> SpaceRepository:
    """Space 仓储实例。"""
    return SpaceRepository(session)


class TestSpaceRepositoryHyperPodFields:
    """测试 HyperPod 后端字段的持久化。"""

    @pytest.mark.asyncio
    async def test_create_hyperpod_space_persists_all_fields(
        self,
        space_repository: SpaceRepository,
        test_user: UserModel,
    ) -> None:
        """创建 HyperPod Space,验证 backend/namespace/queue_name/workspace_template 字段正确存储。"""
        # Arrange: 创建 HyperPod Space 实体
        space_entity = Space(
            id=None,
            space_name="hyperpod-dev-1",
            owner_id=test_user.id,
            instance_type=SpaceInstanceType.ML_G5_XLARGE,
            space_type=SpaceType.JUPYTER,
            status=SpaceStatus.PENDING,
            storage_size_gb=50,
            backend=SpaceBackend.HYPERPOD,
            namespace="training-team-a",
            queue_name="team-a-dev-queue",
            workspace_template="jupyterlab-gpu-template",
            lifecycle_config_arn=None,
            sagemaker_space_arn=None,
        )

        # Act: 持久化
        created = await space_repository.create(space_entity)
        space_id = created.id

        # Assert: 验证持久化成功且返回的实体包含新字段
        assert created.backend == SpaceBackend.HYPERPOD
        assert created.namespace == "training-team-a"
        assert created.queue_name == "team-a-dev-queue"
        assert created.workspace_template == "jupyterlab-gpu-template"

        # Act: 从数据库重新读取
        retrieved = await space_repository.get_by_id(space_id)

        # Assert: 验证往返一致性
        assert retrieved is not None
        assert retrieved.backend == SpaceBackend.HYPERPOD
        assert retrieved.namespace == "training-team-a"
        assert retrieved.queue_name == "team-a-dev-queue"
        assert retrieved.workspace_template == "jupyterlab-gpu-template"
        assert retrieved.space_name == "hyperpod-dev-1"
        assert retrieved.owner_id == test_user.id

    @pytest.mark.asyncio
    async def test_create_studio_space_defaults_to_studio_backend(
        self,
        space_repository: SpaceRepository,
        test_user: UserModel,
    ) -> None:
        """创建 Studio Space(不显式设 backend),验证默认值 STUDIO。"""
        # Arrange: 不设 backend(Entity 默认 STUDIO)
        space_entity = Space(
            id=None,
            space_name="studio-dev-1",
            owner_id=test_user.id,
            instance_type=SpaceInstanceType.ML_T3_MEDIUM,
            space_type=SpaceType.VSCODE,
            status=SpaceStatus.PENDING,
            storage_size_gb=20,
            # backend 默认 STUDIO (Entity 定义)
            namespace=None,
            queue_name=None,
            workspace_template=None,
            lifecycle_config_arn=None,
            sagemaker_space_arn=None,
        )

        # Act
        created = await space_repository.create(space_entity)

        # Assert: 默认值应为 STUDIO
        assert created.backend == SpaceBackend.STUDIO
        assert created.namespace is None
        assert created.queue_name is None
        assert created.workspace_template is None

    @pytest.mark.asyncio
    async def test_update_space_backend_fields(
        self,
        space_repository: SpaceRepository,
        test_user: UserModel,
    ) -> None:
        """测试 backend 等字段可通过 update 修改。"""
        # Arrange: 创建初始 Studio Space
        space_entity = Space(
            id=None,
            space_name="updatable-space",
            owner_id=test_user.id,
            instance_type=SpaceInstanceType.ML_T3_MEDIUM,
            space_type=SpaceType.JUPYTER,
            status=SpaceStatus.PENDING,
            storage_size_gb=20,
            backend=SpaceBackend.STUDIO,
            namespace=None,
            queue_name=None,
            workspace_template=None,
            lifecycle_config_arn=None,
            sagemaker_space_arn=None,
        )
        created = await space_repository.create(space_entity)

        # Act: 更新为 HyperPod 后端
        created.backend = SpaceBackend.HYPERPOD
        created.namespace = "updated-namespace"
        created.queue_name = "updated-queue"
        created.workspace_template = "updated-template"
        updated = await space_repository.update(created)

        # Assert: 更新生效
        assert updated.backend == SpaceBackend.HYPERPOD
        assert updated.namespace == "updated-namespace"
        assert updated.queue_name == "updated-queue"
        assert updated.workspace_template == "updated-template"

        # 再次读取验证
        retrieved = await space_repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.backend == SpaceBackend.HYPERPOD
