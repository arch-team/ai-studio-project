"""Unit tests for HyperPod exceptions."""

import pytest

from src.modules.training.domain.exceptions import (
    HyperPodOperationError,
    HyperPodPodNotFoundError,
    HyperPodSDKUnavailableError,
    TrainingError,
)


class TestHyperPodSDKUnavailableError:
    """Tests for HyperPodSDKUnavailableError exception."""

    def test_default_component(self) -> None:
        """Test exception with default component name."""
        error = HyperPodSDKUnavailableError()
        assert error.component == "HyperPodPytorchJob"

    def test_custom_component(self) -> None:
        """Test exception with custom component name."""
        error = HyperPodSDKUnavailableError(component="HyperPodTrainingJob")
        assert error.component == "HyperPodTrainingJob"

    def test_message_format_default(self) -> None:
        """Test error message format with default component."""
        error = HyperPodSDKUnavailableError()
        expected = (
            "HyperPod SDK component 'HyperPodPytorchJob' is not available. "
            "Please install sagemaker-hyperpod package."
        )
        assert str(error) == expected

    def test_message_format_custom(self) -> None:
        """Test error message format with custom component."""
        error = HyperPodSDKUnavailableError(component="CustomJob")
        expected = "HyperPod SDK component 'CustomJob' is not available. " "Please install sagemaker-hyperpod package."
        assert str(error) == expected

    def test_inherits_from_training_error(self) -> None:
        """Test that exception inherits from TrainingError."""
        error = HyperPodSDKUnavailableError()
        assert isinstance(error, TrainingError)

    def test_can_be_raised_and_caught(self) -> None:
        """Test that exception can be raised and caught."""
        with pytest.raises(HyperPodSDKUnavailableError) as exc_info:
            raise HyperPodSDKUnavailableError()
        assert exc_info.value.component == "HyperPodPytorchJob"


class TestHyperPodPodNotFoundError:
    """Tests for HyperPodPodNotFoundError exception."""

    def test_required_parameters(self) -> None:
        """Test exception requires job_name and pod_name."""
        error = HyperPodPodNotFoundError(job_name="my-job", pod_name="pod-0")
        assert error.job_name == "my-job"
        assert error.pod_name == "pod-0"

    def test_message_format(self) -> None:
        """Test error message format."""
        error = HyperPodPodNotFoundError(job_name="training-job-123", pod_name="worker-1")
        expected = "Pod 'worker-1' not found in job 'training-job-123'"
        assert str(error) == expected

    def test_inherits_from_training_error(self) -> None:
        """Test that exception inherits from TrainingError."""
        error = HyperPodPodNotFoundError(job_name="job", pod_name="pod")
        assert isinstance(error, TrainingError)

    def test_can_be_raised_and_caught(self) -> None:
        """Test that exception can be raised and caught."""
        with pytest.raises(HyperPodPodNotFoundError) as exc_info:
            raise HyperPodPodNotFoundError(job_name="job-1", pod_name="pod-2")
        assert exc_info.value.job_name == "job-1"
        assert exc_info.value.pod_name == "pod-2"


class TestHyperPodOperationError:
    """Tests for HyperPodOperationError exception."""

    def test_without_job_name(self) -> None:
        """Test exception without job_name."""
        error = HyperPodOperationError(
            operation="submit",
            reason="invalid configuration",
        )
        assert error.operation == "submit"
        assert error.reason == "invalid configuration"
        assert error.job_name is None

    def test_with_job_name(self) -> None:
        """Test exception with job_name."""
        error = HyperPodOperationError(
            operation="terminate",
            reason="job already completed",
            job_name="my-training-job",
        )
        assert error.operation == "terminate"
        assert error.reason == "job already completed"
        assert error.job_name == "my-training-job"

    def test_message_format_without_job_name(self) -> None:
        """Test error message format without job_name."""
        error = HyperPodOperationError(
            operation="create_cluster",
            reason="insufficient quota",
        )
        expected = "HyperPod operation 'create_cluster' failed: insufficient quota"
        assert str(error) == expected

    def test_message_format_with_job_name(self) -> None:
        """Test error message format with job_name."""
        error = HyperPodOperationError(
            operation="pause",
            reason="job not running",
            job_name="llm-training-v2",
        )
        expected = "HyperPod operation 'pause' on job 'llm-training-v2' failed: job not running"
        assert str(error) == expected

    def test_inherits_from_training_error(self) -> None:
        """Test that exception inherits from TrainingError."""
        error = HyperPodOperationError(operation="test", reason="test")
        assert isinstance(error, TrainingError)

    def test_can_be_raised_and_caught(self) -> None:
        """Test that exception can be raised and caught."""
        with pytest.raises(HyperPodOperationError) as exc_info:
            raise HyperPodOperationError(
                operation="resume",
                reason="checkpoint not found",
                job_name="job-123",
            )
        assert exc_info.value.operation == "resume"
        assert exc_info.value.reason == "checkpoint not found"
        assert exc_info.value.job_name == "job-123"


class TestHyperPodExceptionHierarchy:
    """Tests for HyperPod exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_training_error(self) -> None:
        """Test that all HyperPod exceptions inherit from TrainingError."""
        exceptions = [
            HyperPodSDKUnavailableError(),
            HyperPodPodNotFoundError(job_name="j", pod_name="p"),
            HyperPodOperationError(operation="op", reason="r"),
        ]
        for exc in exceptions:
            assert isinstance(exc, TrainingError), f"{type(exc).__name__} should inherit from TrainingError"

    def test_catch_by_training_error(self) -> None:
        """Test that HyperPod exceptions can be caught by TrainingError."""
        with pytest.raises(TrainingError):
            raise HyperPodSDKUnavailableError()

        with pytest.raises(TrainingError):
            raise HyperPodPodNotFoundError(job_name="j", pod_name="p")

        with pytest.raises(TrainingError):
            raise HyperPodOperationError(operation="op", reason="r")

    def test_catch_by_base_exception(self) -> None:
        """Test that HyperPod exceptions can be caught by Exception."""
        with pytest.raises(Exception):
            raise HyperPodSDKUnavailableError()
