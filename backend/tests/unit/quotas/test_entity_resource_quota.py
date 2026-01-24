"""Unit tests for ResourceQuota domain entity.

Tests cover:
- ResourceQuota creation with defaults
- Status and validity checks
- Resource allocation validation
- Job submission validation
"""

from datetime import timedelta

import pytest

from src.modules.quotas.domain.entities.resource_quota import ResourceQuota
from src.modules.quotas.domain.value_objects import QuotaStatus, QuotaType
from src.shared.utils import utc_now


class TestQuotaStatusEnum:
    """Tests for QuotaStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all required statuses are defined."""
        expected_statuses = {"ACTIVE", "SUSPENDED", "EXPIRED"}
        actual_statuses = {s.name for s in QuotaStatus}
        assert actual_statuses == expected_statuses


class TestQuotaTypeEnum:
    """Tests for QuotaType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all required types are defined."""
        expected_types = {"USER", "PROJECT", "TEAM"}
        actual_types = {t.name for t in QuotaType}
        assert actual_types == expected_types


class TestResourceQuotaCreation:
    """Tests for ResourceQuota entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating quota with only required fields."""
        quota = ResourceQuota(id=1, name="default-quota")
        assert quota.id == 1
        assert quota.name == "default-quota"

    def test_default_status_is_active(self) -> None:
        """Test default status is ACTIVE."""
        quota = ResourceQuota(id=1, name="test-quota")
        assert quota.status == QuotaStatus.ACTIVE

    def test_default_quota_type_is_user(self) -> None:
        """Test default quota_type is USER."""
        quota = ResourceQuota(id=1, name="test-quota")
        assert quota.quota_type == QuotaType.USER

    def test_default_resource_limits_are_zero(self) -> None:
        """Test default resource limits are 0."""
        quota = ResourceQuota(id=1, name="test-quota")
        assert quota.max_cpu_cores == 0
        assert quota.max_gpu_count == 0
        assert quota.max_memory_gb == 0

    def test_create_with_all_fields(self) -> None:
        """Test creating quota with all fields."""
        quota = ResourceQuota(
            id=1,
            name="project-quota",
            quota_type=QuotaType.PROJECT,
            description="Project resource quota",
            max_cpu_cores=256,
            max_gpu_count=16,
            max_memory_gb=1024,
            max_storage_gb=5000,
            max_concurrent_jobs=10,
            gpu_types=["A100", "H100"],
        )
        assert quota.quota_type == QuotaType.PROJECT
        assert quota.max_cpu_cores == 256
        assert quota.max_gpu_count == 16
        assert quota.gpu_types == ["A100", "H100"]


class TestResourceQuotaStatusMethods:
    """Tests for ResourceQuota status-related methods."""

    @pytest.fixture
    def quota(self) -> ResourceQuota:
        """Create a basic quota for testing."""
        return ResourceQuota(
            id=1,
            name="test-quota",
            max_gpu_count=8,
            max_cpu_cores=64,
            max_memory_gb=256,
        )

    def test_is_active_when_active(self, quota: ResourceQuota) -> None:
        """Test is_active returns True for ACTIVE status."""
        assert quota.is_active()

    def test_is_active_when_suspended(self, quota: ResourceQuota) -> None:
        """Test is_active returns False for SUSPENDED status."""
        quota.suspend()
        assert not quota.is_active()

    def test_is_active_when_not_yet_valid(self, quota: ResourceQuota) -> None:
        """Test is_active returns False before valid_from."""
        quota.valid_from = utc_now() + timedelta(days=1)
        assert not quota.is_active()

    def test_is_active_when_expired(self, quota: ResourceQuota) -> None:
        """Test is_active returns False after valid_until."""
        quota.valid_until = utc_now() - timedelta(days=1)
        assert not quota.is_active()

    def test_is_expired_when_no_expiration(self, quota: ResourceQuota) -> None:
        """Test is_expired returns False when no valid_until set."""
        assert not quota.is_expired()

    def test_is_expired_when_expired(self, quota: ResourceQuota) -> None:
        """Test is_expired returns True after valid_until."""
        quota.valid_until = utc_now() - timedelta(hours=1)
        assert quota.is_expired()

    def test_suspend_changes_status(self, quota: ResourceQuota) -> None:
        """Test suspend changes status to SUSPENDED."""
        quota.suspend()
        assert quota.status == QuotaStatus.SUSPENDED

    def test_activate_changes_status(self, quota: ResourceQuota) -> None:
        """Test activate changes status to ACTIVE."""
        quota.suspend()
        quota.activate()
        assert quota.status == QuotaStatus.ACTIVE


class TestResourceQuotaAllocationMethods:
    """Tests for ResourceQuota allocation validation methods."""

    @pytest.fixture
    def quota(self) -> ResourceQuota:
        """Create a quota with specific limits for testing."""
        return ResourceQuota(
            id=1,
            name="limited-quota",
            max_gpu_count=8,
            max_cpu_cores=64,
            max_memory_gb=256,
            max_storage_gb=1000,
            gpu_types=["A100", "H100"],
        )

    def test_can_allocate_gpu_within_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_gpu returns True within limit."""
        assert quota.can_allocate_gpu(4)
        assert quota.can_allocate_gpu(8)

    def test_can_allocate_gpu_exceeds_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_gpu returns False when exceeding limit."""
        assert not quota.can_allocate_gpu(9)
        assert not quota.can_allocate_gpu(16)

    def test_can_allocate_cpu_within_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_cpu returns True within limit."""
        assert quota.can_allocate_cpu(32)
        assert quota.can_allocate_cpu(64)

    def test_can_allocate_cpu_exceeds_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_cpu returns False when exceeding limit."""
        assert not quota.can_allocate_cpu(65)

    def test_can_allocate_memory_within_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_memory returns True within limit."""
        assert quota.can_allocate_memory(128)
        assert quota.can_allocate_memory(256)

    def test_can_allocate_memory_exceeds_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_memory returns False when exceeding limit."""
        assert not quota.can_allocate_memory(257)

    def test_can_allocate_storage_within_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_storage returns True within limit."""
        assert quota.can_allocate_storage(500)
        assert quota.can_allocate_storage(1000)

    def test_can_allocate_storage_exceeds_limit(self, quota: ResourceQuota) -> None:
        """Test can_allocate_storage returns False when exceeding limit."""
        assert not quota.can_allocate_storage(1001)

    def test_can_allocate_storage_unlimited(self) -> None:
        """Test can_allocate_storage returns True when no limit set."""
        quota = ResourceQuota(id=1, name="unlimited-storage")
        assert quota.max_storage_gb is None
        assert quota.can_allocate_storage(999999)

    def test_is_gpu_type_allowed_when_in_list(self, quota: ResourceQuota) -> None:
        """Test is_gpu_type_allowed returns True for allowed types."""
        assert quota.is_gpu_type_allowed("A100")
        assert quota.is_gpu_type_allowed("H100")

    def test_is_gpu_type_not_allowed(self, quota: ResourceQuota) -> None:
        """Test is_gpu_type_allowed returns False for disallowed types."""
        assert not quota.is_gpu_type_allowed("V100")
        assert not quota.is_gpu_type_allowed("T4")

    def test_is_gpu_type_allowed_when_no_restriction(self) -> None:
        """Test is_gpu_type_allowed returns True when no restrictions."""
        quota = ResourceQuota(id=1, name="any-gpu")
        assert quota.gpu_types == []
        assert quota.is_gpu_type_allowed("any_type")


class TestResourceQuotaJobValidation:
    """Tests for ResourceQuota job submission validation."""

    @pytest.fixture
    def quota(self) -> ResourceQuota:
        """Create a quota for job validation testing."""
        return ResourceQuota(
            id=1,
            name="job-quota",
            max_gpu_count=8,
            max_cpu_cores=64,
            max_memory_gb=256,
            max_concurrent_jobs=5,
            gpu_types=["A100"],
        )

    def test_validate_job_submission_success(self, quota: ResourceQuota) -> None:
        """Test validate_job_submission returns True for valid job."""
        is_valid, error = quota.validate_job_submission(
            cpu_cores=32,
            gpu_count=4,
            memory_gb=128,
            current_running_jobs=2,
            gpu_type="A100",
        )
        assert is_valid is True
        assert error is None

    def test_validate_job_submission_inactive_quota(self, quota: ResourceQuota) -> None:
        """Test validate_job_submission fails for inactive quota."""
        quota.suspend()
        is_valid, error = quota.validate_job_submission(
            cpu_cores=32,
            gpu_count=4,
            memory_gb=128,
            current_running_jobs=0,
        )
        assert is_valid is False
        assert "not active" in error

    def test_validate_job_submission_cpu_exceeded(self, quota: ResourceQuota) -> None:
        """Test validate_job_submission fails when CPU exceeds quota."""
        is_valid, error = quota.validate_job_submission(
            cpu_cores=128,
            gpu_count=4,
            memory_gb=128,
            current_running_jobs=0,
        )
        assert is_valid is False
        assert "CPU" in error

    def test_validate_job_submission_gpu_exceeded(self, quota: ResourceQuota) -> None:
        """Test validate_job_submission fails when GPU exceeds quota."""
        is_valid, error = quota.validate_job_submission(
            cpu_cores=32,
            gpu_count=16,
            memory_gb=128,
            current_running_jobs=0,
        )
        assert is_valid is False
        assert "GPU" in error

    def test_validate_job_submission_memory_exceeded(
        self, quota: ResourceQuota
    ) -> None:
        """Test validate_job_submission fails when memory exceeds quota."""
        is_valid, error = quota.validate_job_submission(
            cpu_cores=32,
            gpu_count=4,
            memory_gb=512,
            current_running_jobs=0,
        )
        assert is_valid is False
        assert "Memory" in error

    def test_validate_job_submission_gpu_type_not_allowed(
        self, quota: ResourceQuota
    ) -> None:
        """Test validate_job_submission fails for disallowed GPU type."""
        is_valid, error = quota.validate_job_submission(
            cpu_cores=32,
            gpu_count=4,
            memory_gb=128,
            current_running_jobs=0,
            gpu_type="V100",
        )
        assert is_valid is False
        assert "GPU type" in error

    def test_validate_job_submission_concurrent_limit_reached(
        self, quota: ResourceQuota
    ) -> None:
        """Test validate_job_submission fails when concurrent limit reached."""
        is_valid, error = quota.validate_job_submission(
            cpu_cores=32,
            gpu_count=4,
            memory_gb=128,
            current_running_jobs=5,
        )
        assert is_valid is False
        assert "Concurrent job limit" in error
