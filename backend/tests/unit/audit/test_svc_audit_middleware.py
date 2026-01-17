"""Unit tests for audit logging middleware - TDD Red Phase."""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from src.modules.audit.domain.value_objects import OperationType, ResourceType


# Test fixtures
@pytest.fixture
def mock_audit_repository() -> AsyncMock:
    """Mock audit log repository for testing."""
    return AsyncMock()


@pytest.fixture
def sample_request_body() -> dict[str, Any]:
    """Sample request body for testing."""
    return {
        "name": "test-job",
        "config": {"epochs": 10},
    }


@pytest.fixture
def sensitive_request_body() -> dict[str, Any]:
    """Request body with sensitive fields."""
    return {
        "username": "testuser",
        "password": "secret123",
        "api_key": "sk-xxx-yyy",
        "token": "jwt-token",
        "secret": "my-secret",
        "data": "normal-data",
    }


@pytest.fixture
def large_request_body() -> dict[str, Any]:
    """Request body exceeding max size limit."""
    return {"data": "x" * 100000}  # ~100KB


class TestAuditMiddlewareExemptPaths:
    """Tests for exempt path handling."""

    def test_skips_health_endpoint(self, mock_audit_repository: AsyncMock) -> None:
        """Health endpoint should not be audited."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        mock_audit_repository.create.assert_not_called()

    def test_skips_docs_endpoint(self, mock_audit_repository: AsyncMock) -> None:
        """OpenAPI docs should not be audited."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware)
        client = TestClient(app)

        response = client.get("/docs")

        assert response.status_code == 200
        mock_audit_repository.create.assert_not_called()

    def test_skips_redoc_endpoint(self, mock_audit_repository: AsyncMock) -> None:
        """ReDoc endpoint should not be audited."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware)
        client = TestClient(app)

        response = client.get("/redoc")

        assert response.status_code == 200
        mock_audit_repository.create.assert_not_called()

    def test_skips_openapi_json(self, mock_audit_repository: AsyncMock) -> None:
        """OpenAPI JSON should not be audited."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware)
        client = TestClient(app)

        response = client.get("/openapi.json")

        assert response.status_code == 200
        mock_audit_repository.create.assert_not_called()

    def _create_test_app(self, middleware_class: type) -> Starlette:
        """Create test app with middleware."""

        async def health(request: Request) -> Response:
            return JSONResponse({"status": "ok"})

        async def docs(request: Request) -> Response:
            return JSONResponse({"docs": "swagger"})

        async def redoc(request: Request) -> Response:
            return JSONResponse({"docs": "redoc"})

        async def openapi(request: Request) -> Response:
            return JSONResponse({"openapi": "3.0.0"})

        app = Starlette(
            routes=[
                Route("/health", health),
                Route("/docs", docs),
                Route("/redoc", redoc),
                Route("/openapi.json", openapi),
            ]
        )
        app.add_middleware(middleware_class)
        return app


class TestAuditMiddlewareHttpMethods:
    """Tests for HTTP method handling."""

    def test_skips_get_requests(self, mock_audit_repository: AsyncMock) -> None:
        """GET requests should not be audited (read-only)."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.get("/api/v1/training-jobs")

        assert response.status_code == 200
        mock_audit_repository.create.assert_not_called()

    def test_skips_head_requests(self, mock_audit_repository: AsyncMock) -> None:
        """HEAD requests should not be audited."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.head("/api/v1/training-jobs")

        assert response.status_code == 200
        mock_audit_repository.create.assert_not_called()

    def test_skips_options_requests(self, mock_audit_repository: AsyncMock) -> None:
        """OPTIONS requests should not be audited."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.options("/api/v1/training-jobs")

        assert response.status_code == 200
        mock_audit_repository.create.assert_not_called()

    def test_records_post_as_create(
        self,
        mock_audit_repository: AsyncMock,
        sample_request_body: dict[str, Any],
    ) -> None:
        """POST requests should be recorded as CREATE operations."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post(
            "/api/v1/training-jobs",
            json=sample_request_body,
        )

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.operation_type == OperationType.CREATE

    def test_records_put_as_update(
        self,
        mock_audit_repository: AsyncMock,
        sample_request_body: dict[str, Any],
    ) -> None:
        """PUT requests should be recorded as UPDATE operations."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.put(
            "/api/v1/training-jobs/123",
            json=sample_request_body,
        )

        assert response.status_code == 200
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.operation_type == OperationType.UPDATE

    def test_records_patch_as_update(
        self,
        mock_audit_repository: AsyncMock,
        sample_request_body: dict[str, Any],
    ) -> None:
        """PATCH requests should be recorded as UPDATE operations."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.patch(
            "/api/v1/training-jobs/123",
            json=sample_request_body,
        )

        assert response.status_code == 200
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.operation_type == OperationType.UPDATE

    def test_records_delete_operation(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """DELETE requests should be recorded as DELETE operations."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.delete("/api/v1/training-jobs/123")

        assert response.status_code == 204
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.operation_type == OperationType.DELETE

    def _create_test_app(
        self,
        middleware_class: type,
        mock_repo: AsyncMock | None = None,
    ) -> Starlette:
        """Create test app with API endpoints."""

        async def list_jobs(request: Request) -> Response:
            return JSONResponse({"jobs": []})

        async def create_job(request: Request) -> Response:
            return JSONResponse({"id": "123"}, status_code=201)

        async def update_job(request: Request) -> Response:
            return JSONResponse({"id": "123", "updated": True})

        async def delete_job(request: Request) -> Response:
            return Response(status_code=204)

        app = Starlette(
            routes=[
                Route(
                    "/api/v1/training-jobs",
                    list_jobs,
                    methods=["GET", "HEAD", "OPTIONS"],
                ),
                Route("/api/v1/training-jobs", create_job, methods=["POST"]),
                Route(
                    "/api/v1/training-jobs/{job_id}",
                    update_job,
                    methods=["PUT", "PATCH"],
                ),
                Route("/api/v1/training-jobs/{job_id}", delete_job, methods=["DELETE"]),
            ]
        )
        if mock_repo:
            app.state.audit_repository = mock_repo
        app.add_middleware(middleware_class)
        return app


class TestAuditMiddlewareResourceTypeMapping:
    """Tests for resource type extraction from paths."""

    @pytest.mark.parametrize(
        "path,expected_type",
        [
            ("/api/v1/training-jobs", ResourceType.TRAINING_JOB),
            ("/api/v1/training-jobs/123", ResourceType.TRAINING_JOB),
            ("/api/v1/datasets", ResourceType.DATASET),
            ("/api/v1/datasets/456", ResourceType.DATASET),
            ("/api/v1/models", ResourceType.MODEL),
            ("/api/v1/models/789", ResourceType.MODEL),
            ("/api/v1/users", ResourceType.USER),
            ("/api/v1/users/abc", ResourceType.USER),
            ("/api/v1/resource-quotas", ResourceType.QUOTA),
            ("/api/v1/quotas", ResourceType.QUOTA),
            ("/api/v1/ide/spaces", ResourceType.SPACE),
            ("/api/v1/spaces", ResourceType.SPACE),
        ],
    )
    def test_maps_path_to_resource_type(
        self,
        mock_audit_repository: AsyncMock,
        path: str,
        expected_type: ResourceType,
    ) -> None:
        """Correctly map API paths to resource types."""
        from src.modules.audit.api.middleware import AuditMiddleware

        middleware = AuditMiddleware(app=MagicMock())
        resource_type = middleware._get_resource_type(path)

        assert resource_type == expected_type

    def test_returns_none_for_unknown_path(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Return None for paths that don't match known resources."""
        from src.modules.audit.api.middleware import AuditMiddleware

        middleware = AuditMiddleware(app=MagicMock())
        resource_type = middleware._get_resource_type("/api/v1/unknown-resource")

        assert resource_type is None


class TestAuditMiddlewareUserExtraction:
    """Tests for user information extraction."""

    def test_extracts_user_from_request_state(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Extract user_id from request.state (set by auth middleware)."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app_with_user(
            AuditMiddleware,
            mock_audit_repository,
            user_id=42,
        )
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.user_id == 42

    def test_handles_anonymous_request(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Handle requests without authenticated user."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app_with_user(
            AuditMiddleware,
            mock_audit_repository,
            user_id=None,
        )
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.user_id is None

    def _create_test_app_with_user(
        self,
        middleware_class: type,
        mock_repo: AsyncMock,
        user_id: int | None,
    ) -> Starlette:
        """Create test app that sets user in request state."""

        async def create_job(request: Request) -> Response:
            return JSONResponse({"id": "123"}, status_code=201)

        async def set_user(request: Request, call_next):
            if user_id is not None:
                request.state.user_id = user_id
            return await call_next(request)

        app = Starlette(
            routes=[
                Route("/api/v1/training-jobs", create_job, methods=["POST"]),
            ]
        )
        app.state.audit_repository = mock_repo
        app.add_middleware(middleware_class)
        app.middleware("http")(set_user)
        return app


class TestAuditMiddlewareRequestCapture:
    """Tests for request body capture and processing."""

    def test_captures_request_body(
        self,
        mock_audit_repository: AsyncMock,
        sample_request_body: dict[str, Any],
    ) -> None:
        """Capture and store request body in audit log."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json=sample_request_body)

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.request_data == sample_request_body

    def test_truncates_large_request_body(
        self,
        mock_audit_repository: AsyncMock,
        large_request_body: dict[str, Any],
    ) -> None:
        """Truncate request body exceeding max size (64KB)."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json=large_request_body)

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        # Request data should be truncated or marked as too large
        assert audit_log.request_data is not None
        request_str = json.dumps(audit_log.request_data)
        assert len(request_str) <= 65536 or "_truncated" in audit_log.request_data

    def test_sanitizes_sensitive_fields(
        self,
        mock_audit_repository: AsyncMock,
        sensitive_request_body: dict[str, Any],
    ) -> None:
        """Sanitize sensitive fields (password, token, etc.)."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json=sensitive_request_body)

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]

        # Sensitive fields should be masked
        assert audit_log.request_data["password"] == "***"
        assert audit_log.request_data["api_key"] == "***"
        assert audit_log.request_data["token"] == "***"
        assert audit_log.request_data["secret"] == "***"
        # Non-sensitive fields should be preserved
        assert audit_log.request_data["username"] == "testuser"
        assert audit_log.request_data["data"] == "normal-data"

    def test_handles_non_json_body(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Handle non-JSON request bodies gracefully."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post(
            "/api/v1/training-jobs",
            content="plain text body",
            headers={"Content-Type": "text/plain"},
        )

        # Should not crash, request_data may be None or contain raw content info
        assert response.status_code in (201, 400, 415)

    def _create_test_app(
        self,
        middleware_class: type,
        mock_repo: AsyncMock,
    ) -> Starlette:
        """Create test app for request capture tests."""

        async def create_job(request: Request) -> Response:
            return JSONResponse({"id": "123"}, status_code=201)

        app = Starlette(
            routes=[
                Route("/api/v1/training-jobs", create_job, methods=["POST"]),
            ]
        )
        app.state.audit_repository = mock_repo
        app.add_middleware(middleware_class)
        return app


class TestAuditMiddlewareResponseCapture:
    """Tests for response status capture."""

    def test_records_success_status(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Record successful response status."""
        from src.modules.audit.api.middleware import AuditMiddleware
        from src.modules.audit.domain.value_objects import AuditStatus

        app = self._create_test_app(
            AuditMiddleware, mock_audit_repository, status_code=201
        )
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.status == AuditStatus.SUCCESS

    def test_records_client_error_status(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Record client error (4xx) as failed status."""
        from src.modules.audit.api.middleware import AuditMiddleware
        from src.modules.audit.domain.value_objects import AuditStatus

        app = self._create_test_app(
            AuditMiddleware, mock_audit_repository, status_code=400
        )
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        assert response.status_code == 400
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.status == AuditStatus.FAILED

    def test_records_server_error_status(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Record server error (5xx) as failed status."""
        from src.modules.audit.api.middleware import AuditMiddleware
        from src.modules.audit.domain.value_objects import AuditStatus

        app = self._create_test_app(
            AuditMiddleware, mock_audit_repository, status_code=500
        )
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        assert response.status_code == 500
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.status == AuditStatus.FAILED

    def test_captures_response_status_code(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Include response status code in response_data."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(
            AuditMiddleware, mock_audit_repository, status_code=201
        )
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.response_data is not None
        assert audit_log.response_data.get("status_code") == 201

    def _create_test_app(
        self,
        middleware_class: type,
        mock_repo: AsyncMock,
        status_code: int = 200,
    ) -> Starlette:
        """Create test app with configurable response status."""

        async def create_job(request: Request) -> Response:
            if status_code >= 400:
                return JSONResponse({"error": "Error"}, status_code=status_code)
            return JSONResponse({"id": "123"}, status_code=status_code)

        app = Starlette(
            routes=[
                Route("/api/v1/training-jobs", create_job, methods=["POST"]),
            ]
        )
        app.state.audit_repository = mock_repo
        app.add_middleware(middleware_class)
        return app


class TestAuditMiddlewareAsyncBehavior:
    """Tests for async write behavior."""

    @pytest.mark.asyncio
    async def test_writes_async_without_blocking(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Audit write should not block the response."""
        from src.modules.audit.api.middleware import AuditMiddleware

        # Configure mock to delay
        async def slow_create(*args, **kwargs):
            await asyncio.sleep(1)  # Simulate slow write
            return MagicMock(id=1)

        mock_audit_repository.create = slow_create

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        import time

        start = time.time()
        response = client.post("/api/v1/training-jobs", json={"name": "test"})
        elapsed = time.time() - start

        # Response should return before the slow write completes
        assert response.status_code == 201
        assert elapsed < 0.5  # Should not wait for the 1s delay

    def test_continues_on_write_failure(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Request should succeed even if audit write fails."""
        from src.modules.audit.api.middleware import AuditMiddleware

        # Configure mock to raise exception
        mock_audit_repository.create.side_effect = Exception("Database error")

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        # Request should still succeed
        assert response.status_code == 201

    def _create_test_app(
        self,
        middleware_class: type,
        mock_repo: AsyncMock,
    ) -> Starlette:
        """Create test app for async tests."""

        async def create_job(request: Request) -> Response:
            return JSONResponse({"id": "123"}, status_code=201)

        app = Starlette(
            routes=[
                Route("/api/v1/training-jobs", create_job, methods=["POST"]),
            ]
        )
        app.state.audit_repository = mock_repo
        app.add_middleware(middleware_class)
        return app


class TestAuditMiddlewareClientInfo:
    """Tests for client information capture."""

    def test_captures_client_ip_from_x_forwarded_for(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Extract client IP from X-Forwarded-For header."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post(
            "/api/v1/training-jobs",
            json={"name": "test"},
            headers={"X-Forwarded-For": "192.168.1.100, 10.0.0.1"},
        )

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.ip_address == "192.168.1.100"

    def test_captures_client_ip_from_host(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Fall back to client host when no X-Forwarded-For."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post(
            "/api/v1/training-jobs",
            json={"name": "test"},
        )

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        # TestClient uses "testclient" as host
        assert audit_log.ip_address is not None

    def test_captures_user_agent(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Capture User-Agent header."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post(
            "/api/v1/training-jobs",
            json={"name": "test"},
            headers={"User-Agent": "TestClient/1.0"},
        )

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.user_agent == "TestClient/1.0"

    def _create_test_app(
        self,
        middleware_class: type,
        mock_repo: AsyncMock,
    ) -> Starlette:
        """Create test app for client info tests."""

        async def create_job(request: Request) -> Response:
            return JSONResponse({"id": "123"}, status_code=201)

        app = Starlette(
            routes=[
                Route("/api/v1/training-jobs", create_job, methods=["POST"]),
            ]
        )
        app.state.audit_repository = mock_repo
        app.add_middleware(middleware_class)
        return app


class TestAuditMiddlewareResourceIdExtraction:
    """Tests for resource ID extraction from paths."""

    def test_extracts_resource_id_from_path(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Extract resource ID from URL path."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.delete("/api/v1/training-jobs/job-123-abc")

        assert response.status_code == 204
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        assert audit_log.resource_id == "job-123-abc"

    def test_handles_collection_endpoint(
        self,
        mock_audit_repository: AsyncMock,
    ) -> None:
        """Handle collection endpoints (no resource ID)."""
        from src.modules.audit.api.middleware import AuditMiddleware

        app = self._create_test_app(AuditMiddleware, mock_audit_repository)
        client = TestClient(app)

        response = client.post("/api/v1/training-jobs", json={"name": "test"})

        assert response.status_code == 201
        mock_audit_repository.create.assert_called_once()
        call_args = mock_audit_repository.create.call_args
        audit_log = call_args[0][0]
        # Resource ID may be None for collection POST, or extracted from response
        assert audit_log.resource_id is None or audit_log.resource_id == "123"

    def _create_test_app(
        self,
        middleware_class: type,
        mock_repo: AsyncMock,
    ) -> Starlette:
        """Create test app for resource ID tests."""

        async def create_job(request: Request) -> Response:
            return JSONResponse({"id": "123"}, status_code=201)

        async def delete_job(request: Request) -> Response:
            return Response(status_code=204)

        app = Starlette(
            routes=[
                Route("/api/v1/training-jobs", create_job, methods=["POST"]),
                Route("/api/v1/training-jobs/{job_id}", delete_job, methods=["DELETE"]),
            ]
        )
        app.state.audit_repository = mock_repo
        app.add_middleware(middleware_class)
        return app
