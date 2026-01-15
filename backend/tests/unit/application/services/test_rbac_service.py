"""RBAC Service Unit Tests."""

import pytest

from src.modules.auth.application.services.rbac_service import (
    K8S_RBAC_BINDINGS,
    ROLE_PERMISSIONS,
    Permission,
    RBACService,
    get_rbac_service,
)
from src.modules.auth.domain.exceptions import InsufficientPermissionsError


class TestRBACServicePermissions:
    """Tests for RBAC permission checks."""

    @pytest.fixture
    def rbac_service(self) -> RBACService:
        """Create RBACService instance."""
        return RBACService()

    def test_has_permission_admin_all(self, rbac_service: RBACService) -> None:
        """Test that admin has all permissions."""
        for permission in Permission:
            assert (
                rbac_service.has_permission("admin", permission) is True
            ), f"Admin should have {permission.name}"

    def test_has_permission_viewer_limited(self, rbac_service: RBACService) -> None:
        """Test that viewer has only view permissions."""
        # Viewer should have view permissions
        view_permissions = [
            Permission.USER_VIEW,
            Permission.TRAINING_JOB_VIEW,
            Permission.DATASET_VIEW,
            Permission.MODEL_VIEW,
            Permission.CLUSTER_VIEW,
            Permission.DEV_SPACE_VIEW,
            Permission.QUOTA_VIEW,
        ]
        for perm in view_permissions:
            assert (
                rbac_service.has_permission("viewer", perm) is True
            ), f"Viewer should have {perm.name}"

        # Viewer should not have create/update/delete permissions
        write_permissions = [
            Permission.USER_CREATE,
            Permission.TRAINING_JOB_CREATE,
            Permission.DATASET_DELETE,
            Permission.MODEL_DEPLOY,
            Permission.CLUSTER_SCALE,
        ]
        for perm in write_permissions:
            assert (
                rbac_service.has_permission("viewer", perm) is False
            ), f"Viewer should not have {perm.name}"

    def test_has_permission_invalid_role(self, rbac_service: RBACService) -> None:
        """Test that invalid role returns False."""
        assert (
            rbac_service.has_permission("invalid_role", Permission.USER_VIEW) is False
        )

    def test_has_permission_engineer_permissions(
        self, rbac_service: RBACService
    ) -> None:
        """Test engineer role permissions."""
        # Engineer should have these
        engineer_perms = [
            Permission.TRAINING_JOB_VIEW,
            Permission.TRAINING_JOB_CREATE,
            Permission.DATASET_VIEW,
            Permission.DATASET_CREATE,
            Permission.MODEL_VIEW,
            Permission.MODEL_CREATE,
        ]
        for perm in engineer_perms:
            assert (
                rbac_service.has_permission("engineer", perm) is True
            ), f"Engineer should have {perm.name}"

        # Engineer should not have admin permissions
        admin_only = [
            Permission.USER_CREATE,
            Permission.USER_DELETE,
            Permission.CLUSTER_CREATE,
            Permission.CLUSTER_DELETE,
            Permission.SYSTEM_CONFIG,
        ]
        for perm in admin_only:
            assert (
                rbac_service.has_permission("engineer", perm) is False
            ), f"Engineer should not have {perm.name}"

    def test_has_permission_project_manager_permissions(
        self, rbac_service: RBACService
    ) -> None:
        """Test project manager role permissions."""
        # PM should have management permissions
        pm_perms = [
            Permission.TRAINING_JOB_UPDATE,
            Permission.TRAINING_JOB_DELETE,
            Permission.DATASET_UPDATE,
            Permission.MODEL_UPDATE,
            Permission.SYSTEM_MONITOR,
        ]
        for perm in pm_perms:
            assert (
                rbac_service.has_permission("project_manager", perm) is True
            ), f"PM should have {perm.name}"


class TestRBACServiceRoleLevel:
    """Tests for RBAC role level checks."""

    @pytest.fixture
    def rbac_service(self) -> RBACService:
        """Create RBACService instance."""
        return RBACService()

    def test_has_role_level_admin_highest(self, rbac_service: RBACService) -> None:
        """Test that admin is highest role level."""
        assert rbac_service.has_role_level("admin", "admin") is True
        assert rbac_service.has_role_level("admin", "project_manager") is True
        assert rbac_service.has_role_level("admin", "engineer") is True
        assert rbac_service.has_role_level("admin", "viewer") is True

    def test_has_role_level_viewer_lowest(self, rbac_service: RBACService) -> None:
        """Test that viewer is lowest role level."""
        assert rbac_service.has_role_level("viewer", "viewer") is True
        assert rbac_service.has_role_level("viewer", "engineer") is False
        assert rbac_service.has_role_level("viewer", "project_manager") is False
        assert rbac_service.has_role_level("viewer", "admin") is False

    def test_has_role_level_engineer(self, rbac_service: RBACService) -> None:
        """Test engineer role level."""
        assert rbac_service.has_role_level("engineer", "engineer") is True
        assert rbac_service.has_role_level("engineer", "viewer") is True
        assert rbac_service.has_role_level("engineer", "project_manager") is False
        assert rbac_service.has_role_level("engineer", "admin") is False

    def test_has_role_level_project_manager(self, rbac_service: RBACService) -> None:
        """Test project manager role level."""
        assert rbac_service.has_role_level("project_manager", "project_manager") is True
        assert rbac_service.has_role_level("project_manager", "engineer") is True
        assert rbac_service.has_role_level("project_manager", "viewer") is True
        assert rbac_service.has_role_level("project_manager", "admin") is False

    def test_has_role_level_invalid_role(self, rbac_service: RBACService) -> None:
        """Test invalid user role returns False, invalid required role treated as level 0."""
        # Invalid user role always returns False (level 0 < required level)
        assert rbac_service.has_role_level("invalid", "viewer") is False
        # Invalid required role is treated as level 0, so admin (level 4) >= 0
        assert rbac_service.has_role_level("admin", "invalid") is True

    def test_role_hierarchy_transitivity(self, rbac_service: RBACService) -> None:
        """Test role hierarchy: admin(4) > pm(3) > engineer(2) > viewer(1)."""
        levels = rbac_service.get_role_level
        assert levels("admin") > levels("project_manager")
        assert levels("project_manager") > levels("engineer")
        assert levels("engineer") > levels("viewer")


class TestRBACServicePermissionSets:
    """Tests for getting permission sets."""

    @pytest.fixture
    def rbac_service(self) -> RBACService:
        """Create RBACService instance."""
        return RBACService()

    def test_get_permissions_admin(self, rbac_service: RBACService) -> None:
        """Test admin has all permissions."""
        admin_perms = rbac_service.get_permissions("admin")
        # Admin should have all permissions defined in enum
        assert len(admin_perms) == len(Permission)

    def test_get_permissions_engineer(self, rbac_service: RBACService) -> None:
        """Test engineer permission count."""
        engineer_perms = rbac_service.get_permissions("engineer")
        # Engineer has limited permissions
        assert len(engineer_perms) < len(Permission)
        assert len(engineer_perms) >= 10  # At least basic permissions

    def test_get_permissions_viewer(self, rbac_service: RBACService) -> None:
        """Test viewer has fewest permissions."""
        viewer_perms = rbac_service.get_permissions("viewer")
        engineer_perms = rbac_service.get_permissions("engineer")
        assert len(viewer_perms) < len(engineer_perms)

    def test_get_permissions_invalid_role(self, rbac_service: RBACService) -> None:
        """Test invalid role returns empty set."""
        perms = rbac_service.get_permissions("invalid_role")
        assert perms == set()


class TestRBACServiceK8sBinding:
    """Tests for Kubernetes RBAC bindings."""

    @pytest.fixture
    def rbac_service(self) -> RBACService:
        """Create RBACService instance."""
        return RBACService()

    def test_get_k8s_rbac_binding_admin(self, rbac_service: RBACService) -> None:
        """Test admin gets cluster-admin binding."""
        binding = rbac_service.get_k8s_rbac_binding("admin")

        assert binding is not None
        assert binding["cluster_role"] == "cluster-admin"
        assert binding["namespace_role"] == "admin"

    def test_get_k8s_rbac_binding_viewer(self, rbac_service: RBACService) -> None:
        """Test viewer gets view binding."""
        binding = rbac_service.get_k8s_rbac_binding("viewer")

        assert binding is not None
        assert binding["cluster_role"] == "view"
        assert binding["namespace_role"] == "view"

    def test_get_k8s_rbac_binding_engineer(self, rbac_service: RBACService) -> None:
        """Test engineer gets edit binding."""
        binding = rbac_service.get_k8s_rbac_binding("engineer")

        assert binding is not None
        assert binding["namespace_role"] == "edit"

    def test_get_k8s_rbac_binding_project_manager(
        self, rbac_service: RBACService
    ) -> None:
        """Test project manager gets edit binding."""
        binding = rbac_service.get_k8s_rbac_binding("project_manager")

        assert binding is not None
        assert binding["namespace_role"] == "edit"

    def test_get_k8s_rbac_binding_invalid_role(self, rbac_service: RBACService) -> None:
        """Test invalid role returns None."""
        binding = rbac_service.get_k8s_rbac_binding("invalid_role")
        assert binding is None


class TestRBACServiceCheckMethods:
    """Tests for check methods that raise exceptions."""

    @pytest.fixture
    def rbac_service(self) -> RBACService:
        """Create RBACService instance."""
        return RBACService()

    def test_check_permission_success(self, rbac_service: RBACService) -> None:
        """Test check_permission does not raise for valid permission."""
        # Should not raise
        rbac_service.check_permission("admin", Permission.USER_CREATE)

    def test_check_permission_raises(self, rbac_service: RBACService) -> None:
        """Test check_permission raises for missing permission."""
        with pytest.raises(InsufficientPermissionsError) as exc_info:
            rbac_service.check_permission("viewer", Permission.USER_CREATE)

        # The implementation uses permission.value (e.g., "user:create")
        assert exc_info.value.required_permission == Permission.USER_CREATE.value

    def test_check_role_level_success(self, rbac_service: RBACService) -> None:
        """Test check_role_level does not raise for sufficient level."""
        # Should not raise
        rbac_service.check_role_level("admin", "engineer")

    def test_check_role_level_raises(self, rbac_service: RBACService) -> None:
        """Test check_role_level raises for insufficient level."""
        with pytest.raises(InsufficientPermissionsError):
            rbac_service.check_role_level("viewer", "admin")


class TestRBACServiceHelpers:
    """Tests for RBAC helper methods."""

    @pytest.fixture
    def rbac_service(self) -> RBACService:
        """Create RBACService instance."""
        return RBACService()

    def test_get_role_level_values(self, rbac_service: RBACService) -> None:
        """Test get_role_level returns correct values."""
        assert rbac_service.get_role_level("admin") == 4
        assert rbac_service.get_role_level("project_manager") == 3
        assert rbac_service.get_role_level("engineer") == 2
        assert rbac_service.get_role_level("viewer") == 1

    def test_get_role_level_invalid(self, rbac_service: RBACService) -> None:
        """Test get_role_level returns 0 for invalid role."""
        assert rbac_service.get_role_level("invalid") == 0

    def test_get_allowed_roles_for_permission(self, rbac_service: RBACService) -> None:
        """Test getting roles allowed for a permission."""
        # USER_CREATE should be admin only (based on RBAC design)
        roles = rbac_service.get_allowed_roles_for_permission(Permission.USER_CREATE)
        assert "admin" in roles
        assert "viewer" not in roles

    def test_get_allowed_roles_for_view_permission(
        self, rbac_service: RBACService
    ) -> None:
        """Test getting roles for a view permission."""
        roles = rbac_service.get_allowed_roles_for_permission(
            Permission.TRAINING_JOB_VIEW
        )
        # All roles should be able to view
        assert "admin" in roles
        assert "project_manager" in roles
        assert "engineer" in roles
        assert "viewer" in roles


class TestRBACServiceSingleton:
    """Tests for RBACService singleton."""

    def test_get_rbac_service_returns_same_instance(self) -> None:
        """Test that get_rbac_service returns the same instance."""
        service1 = get_rbac_service()
        service2 = get_rbac_service()

        assert service1 is service2

    def test_get_rbac_service_is_functional(self) -> None:
        """Test that singleton service works correctly."""
        service = get_rbac_service()

        assert service.has_permission("admin", Permission.USER_CREATE) is True
        assert service.has_role_level("admin", "viewer") is True


class TestPermissionEnum:
    """Tests for Permission enum."""

    def test_permission_enum_values(self) -> None:
        """Test Permission enum has expected values."""
        # User permissions
        assert Permission.USER_VIEW.value == "user:view"
        assert Permission.USER_CREATE.value == "user:create"
        assert Permission.USER_UPDATE.value == "user:update"
        assert Permission.USER_DELETE.value == "user:delete"

        # Training job permissions
        assert Permission.TRAINING_JOB_VIEW.value == "training_job:view"
        assert Permission.TRAINING_JOB_CREATE.value == "training_job:create"

    def test_permission_enum_count(self) -> None:
        """Test Permission enum has expected count."""
        # Should have permissions for: users, training_jobs, datasets, models,
        # clusters, quotas, dev_spaces, audit, system
        assert len(Permission) >= 26  # Based on plan


class TestRolePermissionsMapping:
    """Tests for ROLE_PERMISSIONS constant."""

    def test_role_permissions_has_all_roles(self) -> None:
        """Test ROLE_PERMISSIONS has all four roles."""
        assert "admin" in ROLE_PERMISSIONS
        assert "project_manager" in ROLE_PERMISSIONS
        assert "engineer" in ROLE_PERMISSIONS
        assert "viewer" in ROLE_PERMISSIONS

    def test_role_permissions_admin_superset(self) -> None:
        """Test admin permissions are superset of all others."""
        admin_perms = ROLE_PERMISSIONS["admin"]
        for role in ["project_manager", "engineer", "viewer"]:
            role_perms = ROLE_PERMISSIONS[role]
            assert role_perms.issubset(admin_perms), f"{role} perms not in admin"


class TestK8sRBACBindings:
    """Tests for K8S_RBAC_BINDINGS constant."""

    def test_k8s_bindings_has_all_roles(self) -> None:
        """Test K8S_RBAC_BINDINGS has all four roles."""
        assert "admin" in K8S_RBAC_BINDINGS
        assert "project_manager" in K8S_RBAC_BINDINGS
        assert "engineer" in K8S_RBAC_BINDINGS
        assert "viewer" in K8S_RBAC_BINDINGS

    def test_k8s_bindings_structure(self) -> None:
        """Test K8S_RBAC_BINDINGS has correct structure."""
        for role, binding in K8S_RBAC_BINDINGS.items():
            assert "cluster_role" in binding, f"{role} missing cluster_role"
            assert "namespace_role" in binding, f"{role} missing namespace_role"
