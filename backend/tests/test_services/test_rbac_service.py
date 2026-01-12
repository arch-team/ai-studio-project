"""Test RBAC Service."""

import pytest

from src.services.rbac_service import (
    Action,
    ResourceType,
    Role,
    RBACService,
    get_rbac_service,
)


class TestRBACService:
    """Test RBAC service functionality."""

    def setup_method(self):
        """Set up test."""
        self.service = RBACService()

    def test_get_role_level(self):
        """Test role level retrieval."""
        # 测试有效角色
        assert self.service.get_role_level("admin") == 4
        assert self.service.get_role_level("project_manager") == 3
        assert self.service.get_role_level("engineer") == 2
        assert self.service.get_role_level("viewer") == 1

        # 测试无效角色
        assert self.service.get_role_level("invalid_role") == 0
        assert self.service.get_role_level("") == 0

    def test_has_minimum_role(self):
        """Test minimum role checking."""
        # Admin 可以访问所有级别
        assert self.service.has_minimum_role("admin", Role.VIEWER)
        assert self.service.has_minimum_role("admin", Role.ENGINEER)
        assert self.service.has_minimum_role("admin", Role.PROJECT_MANAGER)
        assert self.service.has_minimum_role("admin", Role.ADMIN)

        # Engineer 只能访问 engineer 和 viewer 级别
        assert self.service.has_minimum_role("engineer", Role.VIEWER)
        assert self.service.has_minimum_role("engineer", Role.ENGINEER)
        assert not self.service.has_minimum_role("engineer", Role.PROJECT_MANAGER)
        assert not self.service.has_minimum_role("engineer", Role.ADMIN)

        # 无效角色没有权限
        assert not self.service.has_minimum_role("invalid", Role.VIEWER)

    def test_check_permission_basic(self):
        """Test basic permission checking."""
        # Admin 可以创建用户
        result = self.service.check_permission(
            user_role="admin",
            resource_type=ResourceType.USER,
            action=Action.CREATE,
        )
        assert result.allowed is True

        # Engineer 不能创建用户
        result = self.service.check_permission(
            user_role="engineer",
            resource_type=ResourceType.USER,
            action=Action.CREATE,
        )
        assert result.allowed is False
        assert "Insufficient permissions" in result.reason

    def test_check_permission_owner_override(self):
        """Test owner override permissions."""
        # 所有者可以更新自己的训练任务
        result = self.service.check_permission(
            user_role="engineer",
            resource_type=ResourceType.TRAINING_JOB,
            action=Action.UPDATE,
            resource_owner_id=123,
            user_id=123,
        )
        assert result.allowed is True
        assert result.reason == "Owner access granted"

        # 非所有者的 engineer 也可以更新训练任务
        result = self.service.check_permission(
            user_role="engineer",
            resource_type=ResourceType.TRAINING_JOB,
            action=Action.UPDATE,
            resource_owner_id=123,
            user_id=456,
        )
        assert result.allowed is True  # Engineer 有更新权限

        # Viewer 不能更新训练任务，即使是所有者
        result = self.service.check_permission(
            user_role="viewer",
            resource_type=ResourceType.TRAINING_JOB,
            action=Action.UPDATE,
            resource_owner_id=123,
            user_id=456,
        )
        assert result.allowed is False

    def test_check_permission_invalid_resource(self):
        """Test permission check with invalid resource."""
        # 使用 mock 的无效资源类型
        result = self.service.check_permission(
            user_role="admin",
            resource_type="invalid_resource",  # type: ignore
            action=Action.CREATE,
        )
        assert result.allowed is False
        assert "Unknown resource type" in result.reason

    def test_check_permission_invalid_action(self):
        """Test permission check with invalid action."""
        # 系统资源没有 CREATE 操作
        result = self.service.check_permission(
            user_role="admin",
            resource_type=ResourceType.SYSTEM,
            action=Action.CREATE,
        )
        assert result.allowed is False
        assert "Unknown action" in result.reason

    def test_get_allowed_actions(self):
        """Test getting allowed actions."""
        # Admin 可以执行所有操作
        actions = self.service.get_allowed_actions(
            user_role="admin",
            resource_type=ResourceType.TRAINING_JOB,
        )
        assert Action.CREATE in actions
        assert Action.READ in actions
        assert Action.UPDATE in actions
        assert Action.DELETE in actions
        assert Action.EXECUTE in actions

        # Viewer 只能读取和列出
        actions = self.service.get_allowed_actions(
            user_role="viewer",
            resource_type=ResourceType.TRAINING_JOB,
        )
        assert Action.READ in actions
        assert Action.LIST in actions
        assert Action.CREATE not in actions
        assert Action.DELETE not in actions

        # 所有者可以执行更多操作
        actions = self.service.get_allowed_actions(
            user_role="viewer",
            resource_type=ResourceType.TRAINING_JOB,
            is_owner=True,
        )
        assert Action.READ in actions
        assert Action.UPDATE in actions  # Owner override
        assert Action.DELETE in actions  # Owner override
        assert Action.EXECUTE in actions  # Owner override

    def test_get_kubernetes_role_binding(self):
        """Test Kubernetes role binding generation."""
        # Admin 映射到 cluster-admin
        binding = self.service.get_kubernetes_role_binding("admin", "namespace-1")
        assert binding["kind"] == "RoleBinding"
        assert binding["roleRef"]["name"] == "cluster-admin"
        assert binding["metadata"]["namespace"] == "namespace-1"

        # Engineer 映射到 edit
        binding = self.service.get_kubernetes_role_binding("engineer", "namespace-2")
        assert binding["roleRef"]["name"] == "edit"

        # 无效角色默认映射到 view
        binding = self.service.get_kubernetes_role_binding("invalid", "namespace-3")
        assert binding["roleRef"]["name"] == "view"

    def test_singleton_service(self):
        """Test singleton service pattern."""
        service1 = get_rbac_service()
        service2 = get_rbac_service()
        assert service1 is service2

    def test_performance_optimization(self):
        """Test that performance optimizations work correctly."""
        # 验证预计算的集合和映射
        assert hasattr(self.service, "_valid_roles")
        assert hasattr(self.service, "_role_enum_map")

        # 验证预计算的值是否正确
        assert "admin" in self.service._valid_roles
        assert "engineer" in self.service._valid_roles
        assert self.service._role_enum_map["admin"] == Role.ADMIN
        assert self.service._role_enum_map["engineer"] == Role.ENGINEER

        # 多次调用应该使用缓存的值（不会引发异常）
        for _ in range(100):
            level = self.service.get_role_level("admin")
            assert level == 4