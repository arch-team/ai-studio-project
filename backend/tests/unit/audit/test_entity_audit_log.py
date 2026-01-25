"""Unit tests for AuditLog domain entity.

Tests cover:
- AuditLog creation with defaults
- Expiration logic
- Factory methods
- Serialization
"""

from datetime import timedelta

from src.modules.audit.domain.entities.audit_log import (
    AUDIT_LOG_RETENTION_DAYS,
    AuditLog,
)
from src.modules.audit.domain.value_objects import (
    AuditStatus,
    OperationType,
    ResourceType,
)
from src.shared.utils import utc_now


class TestAuditStatusEnum:
    """Tests for AuditStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all required statuses are defined."""
        expected_statuses = {"SUCCESS", "FAILED"}
        actual_statuses = {s.name for s in AuditStatus}
        assert actual_statuses == expected_statuses


class TestOperationTypeEnum:
    """Tests for OperationType enum."""

    def test_common_operations_defined(self) -> None:
        """Verify common operations are defined."""
        assert hasattr(OperationType, "CREATE")
        assert hasattr(OperationType, "UPDATE")
        assert hasattr(OperationType, "DELETE")
        assert hasattr(OperationType, "LOGIN")
        assert hasattr(OperationType, "LOGOUT")


class TestResourceTypeEnum:
    """Tests for ResourceType enum."""

    def test_common_resources_defined(self) -> None:
        """Verify common resource types are defined."""
        assert hasattr(ResourceType, "USER")
        assert hasattr(ResourceType, "TRAINING_JOB")


class TestAuditLogCreation:
    """Tests for AuditLog entity creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating audit log with required fields."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.CREATE,
            resource_type=ResourceType.TRAINING_JOB,
        )
        assert log.id == 1
        assert log.operation_type == OperationType.CREATE
        assert log.resource_type == ResourceType.TRAINING_JOB

    def test_default_status_is_success(self) -> None:
        """Test default status is SUCCESS."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.USER,
        )
        assert log.status == AuditStatus.SUCCESS

    def test_expires_at_set_automatically(self) -> None:
        """Test expires_at is set automatically based on retention policy."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.USER,
        )
        expected_expiration = log.created_at + timedelta(days=AUDIT_LOG_RETENTION_DAYS)
        # Allow 1 second tolerance
        assert abs((log.expires_at - expected_expiration).total_seconds()) < 1

    def test_create_with_all_fields(self) -> None:
        """Test creating audit log with all fields."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.TRAINING_JOB,
            status=AuditStatus.FAILED,
            user_id=42,
            resource_id="job-123",
            request_data={"name": "new-name"},
            response_data={"error": "Permission denied"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert log.user_id == 42
        assert log.resource_id == "job-123"
        assert log.request_data == {"name": "new-name"}
        assert log.ip_address == "192.168.1.1"


class TestAuditLogExpirationMethods:
    """Tests for AuditLog expiration methods."""

    def test_is_expired_when_not_expired(self) -> None:
        """Test is_expired returns False when not expired."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.USER,
        )
        assert not log.is_expired()

    def test_is_expired_when_expired(self) -> None:
        """Test is_expired returns True when expired."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.USER,
        )
        # Set expires_at to past
        log.expires_at = utc_now() - timedelta(hours=1)
        assert log.is_expired()

    def test_days_until_expiration_when_not_expired(self) -> None:
        """Test days_until_expiration returns positive days."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.USER,
        )
        days = log.days_until_expiration()
        assert days > 0
        assert days <= AUDIT_LOG_RETENTION_DAYS

    def test_days_until_expiration_when_expired(self) -> None:
        """Test days_until_expiration returns 0 when expired."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.USER,
        )
        log.expires_at = utc_now() - timedelta(days=10)
        assert log.days_until_expiration() == 0


class TestAuditLogStatusMethods:
    """Tests for AuditLog status methods."""

    def test_mark_as_failed(self) -> None:
        """Test mark_as_failed changes status."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.CREATE,
            resource_type=ResourceType.USER,
        )
        assert log.status == AuditStatus.SUCCESS
        log.mark_as_failed()
        assert log.status == AuditStatus.FAILED

    def test_mark_as_failed_with_error_message(self) -> None:
        """Test mark_as_failed sets error message in response_data."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.CREATE,
            resource_type=ResourceType.USER,
        )
        log.mark_as_failed("Database connection failed")
        assert log.status == AuditStatus.FAILED
        assert log.response_data is not None
        assert log.response_data["error"] == "Database connection failed"

    def test_mark_as_failed_preserves_existing_response_data(self) -> None:
        """Test mark_as_failed adds error to existing response_data."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.CREATE,
            resource_type=ResourceType.USER,
            response_data={"original": "data"},
        )
        log.mark_as_failed("Error occurred")
        assert log.response_data["original"] == "data"
        assert log.response_data["error"] == "Error occurred"


class TestAuditLogFactoryMethods:
    """Tests for AuditLog factory methods."""

    def test_create_login_log_success(self) -> None:
        """Test create_login_log for successful login."""
        log = AuditLog.create_login_log(
            user_id=42,
            ip_address="10.0.0.1",
            user_agent="Chrome",
            success=True,
        )
        assert log.operation_type == OperationType.LOGIN
        assert log.resource_type == ResourceType.USER
        assert log.status == AuditStatus.SUCCESS
        assert log.user_id == 42
        assert log.resource_id == "42"
        assert log.ip_address == "10.0.0.1"

    def test_create_login_log_failure(self) -> None:
        """Test create_login_log for failed login."""
        log = AuditLog.create_login_log(
            user_id=42,
            ip_address="10.0.0.1",
            success=False,
        )
        assert log.status == AuditStatus.FAILED

    def test_create_resource_log(self) -> None:
        """Test create_resource_log factory method."""
        log = AuditLog.create_resource_log(
            operation=OperationType.CREATE,
            resource_type=ResourceType.TRAINING_JOB,
            resource_id="job-456",
            user_id=100,
            request_data={"name": "my-job"},
            response_data={"id": "job-456"},
            ip_address="192.168.0.1",
        )
        assert log.operation_type == OperationType.CREATE
        assert log.resource_type == ResourceType.TRAINING_JOB
        assert log.resource_id == "job-456"
        assert log.user_id == 100
        assert log.request_data == {"name": "my-job"}

    def test_create_resource_log_minimal(self) -> None:
        """Test create_resource_log with minimal parameters."""
        log = AuditLog.create_resource_log(
            operation=OperationType.DELETE,
            resource_type=ResourceType.USER,
            resource_id="user-123",
        )
        assert log.operation_type == OperationType.DELETE
        assert log.resource_id == "user-123"
        assert log.user_id is None
        assert log.request_data is None


class TestAuditLogSerialization:
    """Tests for AuditLog serialization methods."""

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.CREATE,
            resource_type=ResourceType.TRAINING_JOB,
            status=AuditStatus.SUCCESS,
            user_id=42,
            resource_id="job-123",
            ip_address="10.0.0.1",
        )
        result = log.to_dict()

        assert result["id"] == 1
        assert result["operation_type"] == OperationType.CREATE.value
        assert result["resource_type"] == ResourceType.TRAINING_JOB.value
        assert result["status"] == AuditStatus.SUCCESS.value
        assert result["user_id"] == 42
        assert result["resource_id"] == "job-123"
        assert result["ip_address"] == "10.0.0.1"
        assert "created_at" in result
        assert "expires_at" in result

    def test_to_dict_with_none_values(self) -> None:
        """Test to_dict handles None values correctly."""
        log = AuditLog(
            id=1,
            operation_type=OperationType.UPDATE,
            resource_type=ResourceType.USER,
        )
        result = log.to_dict()

        assert result["user_id"] is None
        assert result["resource_id"] is None
        assert result["request_data"] is None
        assert result["response_data"] is None
        assert result["user_agent"] is None


class TestRetentionPolicyConstant:
    """Tests for retention policy constant."""

    def test_retention_days_value(self) -> None:
        """Test AUDIT_LOG_RETENTION_DAYS is set correctly."""
        assert AUDIT_LOG_RETENTION_DAYS == 90
