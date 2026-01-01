"""RBAC授权框架单元测试"""

import pytest
from unittest.mock import Mock

from models.user import User, UserRole, UserStatus
from services.auth.rbac import (
    Permission,
    ROLE_PERMISSIONS,
    has_permission,
    has_any_permission,
    has_all_permissions,
    require_permission,
)


@pytest.fixture
def mock_admin_user():
    """模拟管理员用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "admin"
    user.role = UserRole.ADMIN
    user.is_superuser = False
    return user


@pytest.fixture
def mock_superuser():
    """模拟超级用户"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "superuser"
    user.role = UserRole.ADMIN
    user.is_superuser = True
    return user


@pytest.fixture
def mock_project_manager():
    """模拟项目经理"""
    user = Mock(spec=User)
    user.id = 3
    user.username = "pm"
    user.role = UserRole.PROJECT_MANAGER
    user.is_superuser = False
    return user


@pytest.fixture
def mock_algorithm_engineer():
    """模拟算法工程师"""
    user = Mock(spec=User)
    user.id = 4
    user.username = "engineer"
    user.role = UserRole.ALGORITHM_ENGINEER
    user.is_superuser = False
    return user


@pytest.fixture
def mock_data_engineer():
    """模拟数据工程师"""
    user = Mock(spec=User)
    user.id = 5
    user.username = "data_eng"
    user.role = UserRole.DATA_ENGINEER
    user.is_superuser = False
    return user


@pytest.fixture
def mock_viewer():
    """模拟查看者"""
    user = Mock(spec=User)
    user.id = 6
    user.username = "viewer"
    user.role = UserRole.VIEWER
    user.is_superuser = False
    return user


class TestRolePermissions:
    """测试角色权限映射"""

    def test_admin_has_all_permissions(self):
        """测试管理员拥有所有权限"""
        admin_perms = ROLE_PERMISSIONS["admin"]

        # 验证管理员拥有关键权限
        assert Permission.USER_CREATE in admin_perms
        assert Permission.USER_DELETE in admin_perms
        assert Permission.TEAM_CREATE in admin_perms
        assert Permission.TEAM_DELETE in admin_perms
        assert Permission.PROJECT_CREATE in admin_perms
        assert Permission.PROJECT_DELETE in admin_perms
        assert Permission.TRAINING_JOB_CREATE in admin_perms
        assert Permission.TRAINING_JOB_DELETE in admin_perms
        assert Permission.DATASET_CREATE in admin_perms
        assert Permission.DATASET_DELETE in admin_perms
        assert Permission.RESOURCE_QUOTA_CREATE in admin_perms
        assert Permission.RESOURCE_QUOTA_DELETE in admin_perms
        assert Permission.COST_ANALYZE in admin_perms
        assert Permission.DEV_ENV_CREATE in admin_perms

    def test_project_manager_permissions(self):
        """测试项目经理权限"""
        pm_perms = ROLE_PERMISSIONS["project_manager"]

        # 应该拥有的权限
        assert Permission.TEAM_CREATE in pm_perms
        assert Permission.TEAM_UPDATE in pm_perms
        assert Permission.TEAM_MANAGE_MEMBERS in pm_perms
        assert Permission.PROJECT_CREATE in pm_perms
        assert Permission.TRAINING_JOB_READ in pm_perms
        assert Permission.COST_ANALYZE in pm_perms

        # 不应该拥有的权限
        assert Permission.USER_CREATE not in pm_perms
        assert Permission.USER_DELETE not in pm_perms
        assert Permission.TEAM_DELETE not in pm_perms
        assert Permission.TRAINING_JOB_CREATE not in pm_perms
        assert Permission.DATASET_CREATE not in pm_perms

    def test_algorithm_engineer_permissions(self):
        """测试算法工程师权限"""
        eng_perms = ROLE_PERMISSIONS["algorithm_engineer"]

        # 应该拥有的权限
        assert Permission.TRAINING_JOB_CREATE in eng_perms
        assert Permission.TRAINING_JOB_READ in eng_perms
        assert Permission.TRAINING_JOB_START in eng_perms
        assert Permission.TRAINING_JOB_STOP in eng_perms
        assert Permission.DEV_ENV_CREATE in eng_perms
        assert Permission.DEV_ENV_USE in eng_perms

        # 不应该拥有的权限
        assert Permission.TRAINING_JOB_DELETE not in eng_perms
        assert Permission.DATASET_CREATE not in eng_perms
        assert Permission.TEAM_CREATE not in eng_perms
        assert Permission.COST_ANALYZE not in eng_perms

    def test_data_engineer_permissions(self):
        """测试数据工程师权限"""
        de_perms = ROLE_PERMISSIONS["data_engineer"]

        # 应该拥有的权限
        assert Permission.DATASET_CREATE in de_perms
        assert Permission.DATASET_READ in de_perms
        assert Permission.DATASET_UPDATE in de_perms
        assert Permission.DATASET_DELETE in de_perms
        assert Permission.DATASET_UPLOAD in de_perms

        # 不应该拥有的权限
        assert Permission.TRAINING_JOB_CREATE not in de_perms
        assert Permission.TRAINING_JOB_DELETE not in de_perms
        assert Permission.TEAM_CREATE not in de_perms
        assert Permission.DEV_ENV_CREATE not in de_perms

    def test_viewer_permissions(self):
        """测试查看者权限"""
        viewer_perms = ROLE_PERMISSIONS["viewer"]

        # 应该拥有的权限（只读）
        assert Permission.USER_READ in viewer_perms
        assert Permission.TEAM_READ in viewer_perms
        assert Permission.PROJECT_READ in viewer_perms
        assert Permission.TRAINING_JOB_READ in viewer_perms
        assert Permission.DATASET_READ in viewer_perms
        assert Permission.RESOURCE_MONITOR in viewer_perms
        assert Permission.COST_READ in viewer_perms

        # 不应该拥有的权限（任何写操作）
        assert Permission.USER_CREATE not in viewer_perms
        assert Permission.TEAM_CREATE not in viewer_perms
        assert Permission.PROJECT_CREATE not in viewer_perms
        assert Permission.TRAINING_JOB_CREATE not in viewer_perms
        assert Permission.DATASET_CREATE not in viewer_perms
        assert Permission.COST_ANALYZE not in viewer_perms


class TestHasPermission:
    """测试has_permission函数"""

    def test_superuser_has_all_permissions(self, mock_superuser):
        """测试超级用户拥有所有权限"""
        # 超级用户应该拥有任意权限
        assert has_permission(mock_superuser, Permission.USER_CREATE)
        assert has_permission(mock_superuser, Permission.USER_DELETE)
        assert has_permission(mock_superuser, Permission.TRAINING_JOB_DELETE)
        assert has_permission(mock_superuser, Permission.RESOURCE_QUOTA_DELETE)
        assert has_permission(mock_superuser, Permission.COST_ANALYZE)

    def test_admin_has_defined_permissions(self, mock_admin_user):
        """测试管理员拥有定义的权限"""
        assert has_permission(mock_admin_user, Permission.USER_CREATE)
        assert has_permission(mock_admin_user, Permission.TEAM_DELETE)
        assert has_permission(mock_admin_user, Permission.TRAINING_JOB_DELETE)
        assert has_permission(mock_admin_user, Permission.RESOURCE_QUOTA_CREATE)

    def test_project_manager_has_limited_permissions(self, mock_project_manager):
        """测试项目经理拥有有限权限"""
        # 应该拥有的权限
        assert has_permission(mock_project_manager, Permission.TEAM_CREATE)
        assert has_permission(mock_project_manager, Permission.PROJECT_CREATE)
        assert has_permission(mock_project_manager, Permission.TRAINING_JOB_READ)
        assert has_permission(mock_project_manager, Permission.COST_ANALYZE)

        # 不应该拥有的权限
        assert not has_permission(mock_project_manager, Permission.USER_CREATE)
        assert not has_permission(mock_project_manager, Permission.TEAM_DELETE)
        assert not has_permission(mock_project_manager, Permission.TRAINING_JOB_CREATE)
        assert not has_permission(mock_project_manager, Permission.DATASET_CREATE)

    def test_algorithm_engineer_training_permissions(self, mock_algorithm_engineer):
        """测试算法工程师训练任务权限"""
        # 应该拥有的训练权限
        assert has_permission(mock_algorithm_engineer, Permission.TRAINING_JOB_CREATE)
        assert has_permission(mock_algorithm_engineer, Permission.TRAINING_JOB_READ)
        assert has_permission(mock_algorithm_engineer, Permission.TRAINING_JOB_START)
        assert has_permission(mock_algorithm_engineer, Permission.TRAINING_JOB_STOP)
        assert has_permission(mock_algorithm_engineer, Permission.DEV_ENV_CREATE)

        # 不应该拥有的权限
        assert not has_permission(mock_algorithm_engineer, Permission.TRAINING_JOB_DELETE)
        assert not has_permission(mock_algorithm_engineer, Permission.DATASET_CREATE)
        assert not has_permission(mock_algorithm_engineer, Permission.TEAM_CREATE)

    def test_data_engineer_dataset_permissions(self, mock_data_engineer):
        """测试数据工程师数据集权限"""
        # 应该拥有的数据集权限
        assert has_permission(mock_data_engineer, Permission.DATASET_CREATE)
        assert has_permission(mock_data_engineer, Permission.DATASET_READ)
        assert has_permission(mock_data_engineer, Permission.DATASET_UPDATE)
        assert has_permission(mock_data_engineer, Permission.DATASET_DELETE)
        assert has_permission(mock_data_engineer, Permission.DATASET_UPLOAD)

        # 不应该拥有的权限
        assert not has_permission(mock_data_engineer, Permission.TRAINING_JOB_CREATE)
        assert not has_permission(mock_data_engineer, Permission.TEAM_CREATE)
        assert not has_permission(mock_data_engineer, Permission.DEV_ENV_CREATE)

    def test_viewer_only_read_permissions(self, mock_viewer):
        """测试查看者只有读取权限"""
        # 应该拥有的读取权限
        assert has_permission(mock_viewer, Permission.USER_READ)
        assert has_permission(mock_viewer, Permission.TEAM_READ)
        assert has_permission(mock_viewer, Permission.PROJECT_READ)
        assert has_permission(mock_viewer, Permission.TRAINING_JOB_READ)
        assert has_permission(mock_viewer, Permission.DATASET_READ)
        assert has_permission(mock_viewer, Permission.COST_READ)

        # 不应该拥有任何写权限
        assert not has_permission(mock_viewer, Permission.USER_CREATE)
        assert not has_permission(mock_viewer, Permission.TEAM_CREATE)
        assert not has_permission(mock_viewer, Permission.PROJECT_CREATE)
        assert not has_permission(mock_viewer, Permission.TRAINING_JOB_CREATE)
        assert not has_permission(mock_viewer, Permission.DATASET_CREATE)
        assert not has_permission(mock_viewer, Permission.COST_ANALYZE)


class TestHasAnyPermission:
    """测试has_any_permission函数"""

    def test_user_has_one_of_permissions(self, mock_algorithm_engineer):
        """测试用户拥有权限列表中的至少一个"""
        perms = [
            Permission.TRAINING_JOB_CREATE,
            Permission.DATASET_CREATE,
            Permission.TEAM_CREATE,
        ]
        # 算法工程师拥有TRAINING_JOB_CREATE,所以返回True
        assert has_any_permission(mock_algorithm_engineer, perms)

    def test_user_has_none_of_permissions(self, mock_viewer):
        """测试用户没有权限列表中的任何一个"""
        perms = [
            Permission.USER_CREATE,
            Permission.TEAM_DELETE,
            Permission.DATASET_CREATE,
        ]
        # 查看者没有任何写权限
        assert not has_any_permission(mock_viewer, perms)

    def test_superuser_has_any_permission(self, mock_superuser):
        """测试超级用户拥有任意权限"""
        perms = [
            Permission.USER_DELETE,
            Permission.TRAINING_JOB_DELETE,
            Permission.RESOURCE_QUOTA_DELETE,
        ]
        assert has_any_permission(mock_superuser, perms)


class TestHasAllPermissions:
    """测试has_all_permissions函数"""

    def test_user_has_all_permissions(self, mock_admin_user):
        """测试用户拥有权限列表中的所有权限"""
        perms = [
            Permission.USER_CREATE,
            Permission.TEAM_CREATE,
            Permission.PROJECT_CREATE,
        ]
        # 管理员拥有所有这些权限
        assert has_all_permissions(mock_admin_user, perms)

    def test_user_missing_some_permissions(self, mock_project_manager):
        """测试用户缺少权限列表中的某些权限"""
        perms = [
            Permission.TEAM_CREATE,  # 拥有
            Permission.PROJECT_CREATE,  # 拥有
            Permission.USER_CREATE,  # 没有
        ]
        # 项目经理缺少USER_CREATE权限
        assert not has_all_permissions(mock_project_manager, perms)

    def test_superuser_has_all_permissions(self, mock_superuser):
        """测试超级用户拥有所有权限"""
        perms = [
            Permission.USER_DELETE,
            Permission.TEAM_DELETE,
            Permission.TRAINING_JOB_DELETE,
            Permission.RESOURCE_QUOTA_DELETE,
        ]
        assert has_all_permissions(mock_superuser, perms)


class TestRequirePermission:
    """测试require_permission装饰器"""

    @pytest.mark.asyncio
    async def test_decorator_allows_with_permission(self, mock_admin_user):
        """测试装饰器允许有权限的用户"""
        @require_permission(Permission.USER_CREATE)
        async def create_user(current_user):
            return "User created"

        result = await create_user(current_user=mock_admin_user)
        assert result == "User created"

    @pytest.mark.asyncio
    async def test_decorator_denies_without_permission(self, mock_viewer):
        """测试装饰器拒绝无权限的用户"""
        @require_permission(Permission.USER_CREATE)
        async def create_user(current_user):
            return "User created"

        with pytest.raises(PermissionError) as exc_info:
            await create_user(current_user=mock_viewer)

        assert "Permission denied" in str(exc_info.value)
        assert "user:create" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_decorator_allows_superuser(self, mock_superuser):
        """测试装饰器允许超级用户"""
        @require_permission(Permission.TRAINING_JOB_DELETE)
        async def delete_job(current_user):
            return "Job deleted"

        result = await delete_job(current_user=mock_superuser)
        assert result == "Job deleted"

    @pytest.mark.asyncio
    async def test_decorator_raises_without_user(self):
        """测试装饰器在没有用户时抛出错误"""
        @require_permission(Permission.USER_CREATE)
        async def create_user():
            return "User created"

        with pytest.raises(ValueError) as exc_info:
            await create_user()

        assert "User not found" in str(exc_info.value)
