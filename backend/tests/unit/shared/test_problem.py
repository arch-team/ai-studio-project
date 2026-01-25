"""Tests for Problem base class and @problem decorator.

测试说明:
---------
Problem 基类使用 @problem 装饰器注入 http_status 和 error_code，
使用 @dataclass 自动生成 get_details() 方法。
"""

import pytest
from dataclasses import dataclass, field
from typing import Any

from fastapi import status

from src.shared.domain.problem import Problem, problem


class TestProblemDecorator:
    """测试 @problem 装饰器."""

    def test_decorator_injects_status_and_code(self):
        """装饰器应注入 http_status 和 error_code."""
        @problem(404, "TEST_NOT_FOUND")
        @dataclass
        class TestError(Problem):
            item_id: str

        assert TestError.http_status == 404
        assert TestError.error_code == "TEST_NOT_FOUND"

    def test_decorator_with_message_template(self):
        """装饰器应支持消息模板."""
        @problem(404, "TEST_NOT_FOUND", "Item '{item_id}' not found")
        @dataclass
        class TestError(Problem):
            item_id: str

        err = TestError(item_id="123")
        assert err.message == "Item '123' not found"

    def test_decorator_with_multiple_fields_in_template(self):
        """消息模板应支持多个字段."""
        @problem(409, "STATE_ERROR", "Cannot {operation} {entity} in {state} state")
        @dataclass
        class StateError(Problem):
            entity: str
            state: str
            operation: str

        err = StateError(entity="Job", state="running", operation="delete")
        assert err.message == "Cannot delete Job in running state"

    def test_decorator_without_template_generates_default_message(self):
        """没有模板时应生成默认消息."""
        @problem(500, "INTERNAL_ERROR")
        @dataclass
        class InternalError(Problem):
            reason: str

        err = InternalError(reason="something wrong")
        assert "InternalError" in err.message
        assert "reason='something wrong'" in err.message


class TestProblemGetDetails:
    """测试 get_details() 自动生成."""

    def test_returns_all_fields(self):
        """应返回所有数据字段."""
        @problem(404, "TEST_ERROR")
        @dataclass
        class TestError(Problem):
            field1: str
            field2: int

        err = TestError(field1="value", field2=42)
        details = err.get_details()

        assert details == {"field1": "value", "field2": 42}

    def test_excludes_message_field(self):
        """应排除 message 字段."""
        @problem(400, "TEST_ERROR")
        @dataclass
        class TestError(Problem):
            custom_field: str

        err = TestError(custom_field="test")
        details = err.get_details()

        assert "message" not in details
        assert details == {"custom_field": "test"}

    def test_returns_none_for_no_fields(self):
        """无字段时应返回 None."""
        @problem(400, "TEST_ERROR")
        @dataclass
        class TestError(Problem):
            message: str = field(default="Test error")

        err = TestError()
        details = err.get_details()

        assert details is None or details == {}


class TestProblemException:
    """测试 Problem 作为异常使用."""

    def test_can_be_raised_and_caught(self):
        """应能正常抛出和捕获."""
        @problem(404, "NOT_FOUND", "Resource not found")
        @dataclass
        class NotFoundError(Problem):
            resource_id: str

        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError(resource_id="123")

        assert exc_info.value.resource_id == "123"
        assert exc_info.value.http_status == 404
        assert exc_info.value.error_code == "NOT_FOUND"

    def test_str_returns_message(self):
        """str() 应返回消息."""
        @problem(400, "TEST", "Test message")
        @dataclass
        class TestError(Problem):
            pass

        err = TestError()
        assert str(err) == "Test message"

    def test_exception_args_contains_message(self):
        """异常 args 应包含消息."""
        @problem(400, "TEST", "Test message")
        @dataclass
        class TestError(Problem):
            pass

        err = TestError()
        assert err.args == ("Test message",)


class TestProblemInheritance:
    """测试 Problem 继承关系."""

    def test_is_subclass_of_exception(self):
        """Problem 应是 Exception 子类."""
        assert issubclass(Problem, Exception)

    def test_custom_error_is_instance_of_problem(self):
        """自定义异常应是 Problem 实例."""
        @problem(400, "TEST")
        @dataclass
        class TestError(Problem):
            pass

        err = TestError()
        assert isinstance(err, Problem)
        assert isinstance(err, Exception)


class TestProblemCustomPostInit:
    """测试自定义 __post_init__ 行为."""

    def test_custom_post_init_can_modify_message(self):
        """自定义 __post_init__ 应能修改消息."""
        @problem(500, "OPERATION_ERROR")
        @dataclass
        class OperationError(Problem):
            operation: str
            reason: str
            target: str | None = None

            def __post_init__(self) -> None:
                if self.target:
                    self.message = (
                        f"Operation '{self.operation}' on '{self.target}' failed: {self.reason}"
                    )
                else:
                    self.message = f"Operation '{self.operation}' failed: {self.reason}"
                super().__post_init__()

        err1 = OperationError(operation="delete", reason="timeout", target="job-123")
        assert err1.message == "Operation 'delete' on 'job-123' failed: timeout"

        err2 = OperationError(operation="create", reason="invalid config")
        assert err2.message == "Operation 'create' failed: invalid config"


class TestProblemHttpStatusMappings:
    """测试常见 HTTP 状态码映射."""

    def test_404_not_found(self):
        @problem(status.HTTP_404_NOT_FOUND, "NOT_FOUND")
        @dataclass
        class NotFoundError(Problem):
            pass

        assert NotFoundError.http_status == 404

    def test_400_bad_request(self):
        @problem(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST")
        @dataclass
        class BadRequestError(Problem):
            pass

        assert BadRequestError.http_status == 400

    def test_401_unauthorized(self):
        @problem(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED")
        @dataclass
        class UnauthorizedError(Problem):
            pass

        assert UnauthorizedError.http_status == 401

    def test_403_forbidden(self):
        @problem(status.HTTP_403_FORBIDDEN, "FORBIDDEN")
        @dataclass
        class ForbiddenError(Problem):
            pass

        assert ForbiddenError.http_status == 403

    def test_409_conflict(self):
        @problem(status.HTTP_409_CONFLICT, "CONFLICT")
        @dataclass
        class ConflictError(Problem):
            pass

        assert ConflictError.http_status == 409

    def test_422_unprocessable_entity(self):
        @problem(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR")
        @dataclass
        class ValidationError(Problem):
            pass

        assert ValidationError.http_status == 422

    def test_429_too_many_requests(self):
        @problem(status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT")
        @dataclass
        class RateLimitError(Problem):
            pass

        assert RateLimitError.http_status == 429

    def test_500_internal_server_error(self):
        @problem(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR")
        @dataclass
        class InternalError(Problem):
            pass

        assert InternalError.http_status == 500

    def test_503_service_unavailable(self):
        @problem(status.HTTP_503_SERVICE_UNAVAILABLE, "SERVICE_UNAVAILABLE")
        @dataclass
        class ServiceUnavailableError(Problem):
            pass

        assert ServiceUnavailableError.http_status == 503


class TestProblemDefaultFieldValues:
    """测试带默认值的字段."""

    def test_field_with_default_value(self):
        @problem(400, "TEST")
        @dataclass
        class TestError(Problem):
            required_field: str
            optional_field: str = "default"

        err = TestError(required_field="value")
        assert err.required_field == "value"
        assert err.optional_field == "default"

    def test_field_with_default_factory(self):
        @problem(400, "TEST")
        @dataclass
        class TestError(Problem):
            items: list[str] = field(default_factory=list)

        err = TestError()
        assert err.items == []

    def test_custom_message_override(self):
        """应能通过参数覆盖自动生成的消息."""
        @problem(400, "TEST", "Default message for {field}")
        @dataclass
        class TestError(Problem):
            field: str

        # 使用模板生成消息
        err1 = TestError(field="value")
        assert err1.message == "Default message for value"

        # 手动覆盖消息
        err2 = TestError(field="value", message="Custom message")
        assert err2.message == "Custom message"


class TestDomainExceptionsUseProblem:
    """测试现有域异常使用 Problem 基类."""

    def test_entity_not_found_is_problem_instance(self):
        from src.shared.domain.exceptions import EntityNotFoundError

        err = EntityNotFoundError(entity_type="User", entity_id="123")
        assert isinstance(err, Problem)
        assert err.http_status == 404
        assert err.error_code == "ENTITY_NOT_FOUND"

    def test_validation_error_is_problem_instance(self):
        from src.shared.domain.exceptions import ValidationError

        err = ValidationError(message="Invalid input", field_name="email")
        assert isinstance(err, Problem)
        assert err.http_status == 422
        assert err.error_code == "VALIDATION_ERROR"

    def test_duplicate_entity_is_problem_instance(self):
        from src.shared.domain.exceptions import DuplicateEntityError

        err = DuplicateEntityError(entity_type="User", identifier="email@test.com")
        assert isinstance(err, Problem)
        assert err.http_status == 409
        assert err.error_code == "DUPLICATE_ENTITY"


class TestSecurityExceptionsUseProblem:
    """测试安全异常使用 Problem 基类."""

    def test_authentication_error_is_problem_instance(self):
        from src.shared.infrastructure.security.exceptions import AuthenticationError

        err = AuthenticationError()
        assert isinstance(err, Problem)
        assert err.http_status == 401
        assert err.error_code == "AUTHENTICATION_FAILED"

    def test_insufficient_permissions_is_problem_instance(self):
        from src.shared.infrastructure.security.exceptions import InsufficientPermissionsError

        err = InsufficientPermissionsError(required_permission="admin")
        assert isinstance(err, Problem)
        assert err.http_status == 403
        assert err.error_code == "INSUFFICIENT_PERMISSIONS"

    def test_password_too_weak_is_problem_instance(self):
        from src.shared.infrastructure.security.exceptions import PasswordTooWeakError

        err = PasswordTooWeakError(violations=["too short"])
        assert isinstance(err, Problem)
        assert err.http_status == 400
        assert err.error_code == "PASSWORD_TOO_WEAK"


class TestModuleExceptionsUseProblem:
    """测试模块异常使用 Problem 基类."""

    def test_training_job_not_found_is_problem_instance(self):
        from src.modules.training.domain.exceptions import TrainingJobNotFoundError

        err = TrainingJobNotFoundError(job_id="job-123")
        assert isinstance(err, Problem)
        assert err.http_status == 404
        assert err.error_code == "TRAINING_JOB_NOT_FOUND"

    def test_quota_exceeded_is_problem_instance(self):
        from src.modules.quotas.domain.exceptions import QuotaExceededError

        err = QuotaExceededError(resource="gpu", requested=10, limit=5)
        assert isinstance(err, Problem)
        assert err.http_status == 429
        assert err.error_code == "QUOTA_EXCEEDED"

    def test_space_not_found_is_problem_instance(self):
        from src.modules.spaces.domain.exceptions import SpaceNotFoundError

        err = SpaceNotFoundError(space_id="space-123")
        assert isinstance(err, Problem)
        assert err.http_status == 404
        assert err.error_code == "SPACE_NOT_FOUND"
