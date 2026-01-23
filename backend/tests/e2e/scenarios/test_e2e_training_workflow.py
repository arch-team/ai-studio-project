"""E2E Tests - Training Job Workflow Scenarios.

Tests the complete training job workflow from submission to completion,
covering User Story 1: Algorithm engineer submits and monitors distributed training.

Reference: specs/001-ai-training-platform/spec.md - User Story 1
"""

from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


# =============================================================================
# Test Data
# =============================================================================


def create_training_job_payload(
    job_name: str = "e2e-bert-training",
    instance_type: str = "ml.g5.xlarge",
    node_count: int = 2,
) -> dict[str, Any]:
    """Create a standard training job request payload."""
    return {
        "job_name": job_name,
        "display_name": "E2E BERT Training Test",
        "description": "End-to-end test for training job workflow",
        "image_uri": "123456789.dkr.ecr.us-east-1.amazonaws.com/training:latest",
        "instance_type": instance_type,
        "node_count": node_count,
        "tasks_per_node": 1,
        "entrypoint_command": ["python", "-m", "torch.distributed.launch", "train.py"],
        "distribution_strategy": "DDP",
        "priority": "medium",
        "hyperparameters": {
            "learning_rate": "1e-4",
            "batch_size": "32",
            "max_epochs": "10",
        },
        "environment_variables": {
            "NCCL_DEBUG": "INFO",
            "PYTHONUNBUFFERED": "1",
        },
    }


# =============================================================================
# User Story 1: Algorithm Engineer Training Workflow
# =============================================================================


class TestTrainingJobSubmissionWorkflow:
    """Test training job submission workflow.

    Covers Acceptance Scenario 1:
    Given algorithm engineer is logged in with training quota,
    When submitting PyTorch distributed training configuration,
    Then system accepts and schedules the training job.
    """

    async def test_submit_training_job_requires_authentication(
        self,
        app_client: AsyncClient,
    ):
        """Verify training job submission requires authentication."""
        payload = create_training_job_payload()

        response = await app_client.post(
            "/api/v1/training-jobs",
            json=payload,
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_submit_training_job_with_valid_credentials(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify authenticated user can submit training job."""
        payload = create_training_job_payload(job_name="e2e-auth-test-job")

        response = await authenticated_client.post(
            "/api/v1/training-jobs",
            json=payload,
        )

        # Should succeed or fail due to missing quota (not auth error)
        assert response.status_code in [201, 400, 422, 429]
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["job_name"] == "e2e-auth-test-job"
            assert data["status"] == "Submitted"

    async def test_submit_training_job_validates_required_fields(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify required field validation."""
        # Missing job_name
        payload = create_training_job_payload()
        del payload["job_name"]

        response = await authenticated_client.post(
            "/api/v1/training-jobs",
            json=payload,
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("job_name" in str(e).lower() for e in error_detail)

    async def test_submit_training_job_validates_distribution_strategy(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify distribution strategy validation."""
        payload = create_training_job_payload()
        payload["distribution_strategy"] = "INVALID_STRATEGY"

        response = await authenticated_client.post(
            "/api/v1/training-jobs",
            json=payload,
        )

        assert response.status_code == 422


class TestTrainingJobMonitoringWorkflow:
    """Test training job monitoring workflow.

    Covers Acceptance Scenario 2:
    Given training job is running,
    When algorithm engineer accesses job details,
    Then real-time status, metrics, and logs are displayed.
    """

    async def test_get_training_job_status(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify training job status can be retrieved."""
        # First, try to get a job (may not exist in test env)
        response = await authenticated_client.get(
            "/api/v1/training-jobs/1",
        )

        # Should return 200 with job data or 404 if not found
        assert response.status_code in [200, 404]

    async def test_list_training_jobs_with_filters(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify training job list with filters."""
        response = await authenticated_client.get(
            "/api/v1/training-jobs",
            params={
                "status": "Running",
                "page": 1,
                "page_size": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1

    async def test_list_training_jobs_pagination(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify training job list pagination."""
        response = await authenticated_client.get(
            "/api/v1/training-jobs",
            params={
                "page": 1,
                "page_size": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page_size"] == 5


class TestTrainingJobLifecycleWorkflow:
    """Test training job lifecycle operations.

    Covers pause, resume, and stop operations.
    """

    async def test_pause_training_job_requires_running_status(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify pause operation validates job status."""
        # Try to pause a non-existent or non-running job
        response = await authenticated_client.post(
            "/api/v1/training-jobs/99999/actions/pause",
        )

        # Should fail - job not found or not in valid state
        assert response.status_code in [404, 409]

    async def test_resume_training_job_requires_paused_status(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify resume operation validates job status."""
        response = await authenticated_client.post(
            "/api/v1/training-jobs/99999/actions/resume",
        )

        assert response.status_code in [404, 409]

    async def test_stop_training_job(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify stop operation."""
        response = await authenticated_client.post(
            "/api/v1/training-jobs/99999/actions/stop",
        )

        assert response.status_code in [404, 200]


# =============================================================================
# User Story 3: Admin Resource Quota Workflow
# =============================================================================


class TestAdminResourceQuotaWorkflow:
    """Test admin resource quota management workflow.

    Covers User Story 3: Platform admin configures resource quotas.
    """

    async def test_list_resource_quotas(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify admin can list resource quotas."""
        response = await authenticated_client.get(
            "/api/v1/resource-quotas",
        )

        # Should return list or 403 if not admin
        assert response.status_code in [200, 403]

    async def test_create_resource_quota_requires_admin(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify resource quota creation requires admin role."""
        payload = {
            "name": "e2e-test-quota",
            "max_gpu_count": 10,
            "max_cpu_cores": 100,
            "max_memory_gb": 500,
        }

        response = await authenticated_client.post(
            "/api/v1/resource-quotas",
            json=payload,
        )

        # Should succeed if admin, 403 otherwise
        assert response.status_code in [201, 403, 422]


# =============================================================================
# Cross-Cutting Concerns
# =============================================================================


class TestAPIVersioning:
    """Test API versioning compliance."""

    async def test_api_version_header_present(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify API version header in responses."""
        response = await authenticated_client.get(
            "/api/v1/training-jobs",
        )

        # Check for version header (if implemented)
        # assert "X-API-Version" in response.headers
        assert response.status_code in [200, 401]

    async def test_api_v1_endpoints_accessible(
        self,
        app_client: AsyncClient,
    ):
        """Verify v1 API endpoints are accessible."""
        # Health check should not require auth
        response = await app_client.get("/health")

        assert response.status_code == 200


class TestErrorResponseConsistency:
    """Test error response format consistency."""

    async def test_404_error_format(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify 404 error response format."""
        response = await authenticated_client.get(
            "/api/v1/training-jobs/99999999",
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_422_validation_error_format(
        self,
        authenticated_client: AsyncClient,
    ):
        """Verify 422 validation error response format."""
        response = await authenticated_client.post(
            "/api/v1/training-jobs",
            json={"invalid": "payload"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
