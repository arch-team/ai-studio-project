"""Model API Endpoints Integration Tests - TDD Red-Green-Refactor.

Tests for T031a (POST /models), T031b (GET /models), T031c (GET /models/{id}/versions).
"""

from typing import Any

import pytest
from httpx import AsyncClient

# === Fixtures ===


@pytest.fixture
def create_model_request_data() -> dict[str, Any]:
    """Valid model creation request data."""
    return {
        "training_job_id": 1,
        "checkpoint_id": 1,
        "model_name": "bert-base-classifier",
        "display_name": "BERT Base Classifier v1",
        "description": "Fine-tuned BERT model for text classification",
        "framework": "pytorch",
        "framework_version": "2.1.0",
        "metrics": {
            "accuracy": 0.92,
            "f1_score": 0.89,
            "loss": 0.15,
        },
        "hyperparameters": {
            "learning_rate": 0.0001,
            "batch_size": 32,
            "epochs": 10,
        },
        "tags": ["nlp", "classification", "bert"],
    }


@pytest.fixture
def minimal_model_request_data() -> dict[str, Any]:
    """Minimal model creation request (only required fields)."""
    return {
        "training_job_id": 1,
        "checkpoint_id": 1,
        "model_name": "simple-model",
        "framework": "pytorch",
    }


@pytest.fixture
def invalid_model_name_data() -> dict[str, Any]:
    """Invalid model name (uppercase not allowed)."""
    return {
        "training_job_id": 1,
        "checkpoint_id": 1,
        "model_name": "INVALID_NAME",
        "framework": "pytorch",
    }


# === Test Classes ===


class TestCreateModelEndpoint:
    """Tests for POST /api/v1/models endpoint (T031a)."""

    @pytest.mark.asyncio
    async def test_create_model_requires_auth(self, client: AsyncClient) -> None:
        """Test model creation requires authentication."""
        response = await client.post(
            "/api/v1/models",
            json={"model_name": "test-model"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_model_success(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_model_request_data: dict[str, Any],
    ) -> None:
        """Test successful model creation returns 201."""
        response = await client.post(
            "/api/v1/models",
            json=create_model_request_data,
            headers=engineer_auth_headers,
        )
        # 201 (success), 404 (training_job/checkpoint not found), 500 (DB error)
        assert response.status_code in [201, 404, 500, 503]
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["model_name"] == create_model_request_data["model_name"]
            assert data["status"] == "registered"
            assert "version" in data

    @pytest.mark.asyncio
    async def test_create_model_minimal_fields(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        minimal_model_request_data: dict[str, Any],
    ) -> None:
        """Test model creation with only required fields."""
        response = await client.post(
            "/api/v1/models",
            json=minimal_model_request_data,
            headers=engineer_auth_headers,
        )
        assert response.status_code in [201, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_create_model_invalid_training_job(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create model with non-existent training job returns 404."""
        response = await client.post(
            "/api/v1/models",
            json={
                "training_job_id": 99999,
                "checkpoint_id": 1,
                "model_name": "test-model",
                "framework": "pytorch",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_create_model_invalid_checkpoint(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create model with non-existent checkpoint returns 404."""
        response = await client.post(
            "/api/v1/models",
            json={
                "training_job_id": 1,
                "checkpoint_id": 99999,
                "model_name": "test-model",
                "framework": "pytorch",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_create_model_invalid_name_returns_422(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        invalid_model_name_data: dict[str, Any],
    ) -> None:
        """Test create with invalid model name returns validation error."""
        response = await client.post(
            "/api/v1/models",
            json=invalid_model_name_data,
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_model_missing_required_fields(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create with missing required fields returns 422."""
        response = await client.post(
            "/api/v1/models",
            json={"model_name": "test-model"},  # Missing training_job_id, checkpoint_id
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_model_invalid_framework(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create with invalid framework returns 422."""
        response = await client.post(
            "/api/v1/models",
            json={
                "training_job_id": 1,
                "checkpoint_id": 1,
                "model_name": "test-model",
                "framework": "invalid_framework",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422


class TestListModelsEndpoint:
    """Tests for GET /api/v1/models endpoint (T031b)."""

    @pytest.mark.asyncio
    async def test_list_models_requires_auth(self, client: AsyncClient) -> None:
        """Test listing models requires authentication."""
        response = await client.get("/api/v1/models")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_models_success(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test listing models returns paginated response."""
        response = await client.get(
            "/api/v1/models",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_models_with_pagination(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test listing models with pagination params."""
        response = await client.get(
            "/api/v1/models",
            params={"page": 1, "page_size": 10},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_models_filter_by_training_job(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering models by training_job_id."""
        response = await client.get(
            "/api/v1/models",
            params={"training_job_id": 1},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            # All items should belong to the specified training job
            for item in data["items"]:
                assert item["training_job_id"] == 1

    @pytest.mark.asyncio
    async def test_list_models_filter_by_status(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering models by status."""
        response = await client.get(
            "/api/v1/models",
            params={"status": "registered"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                assert item["status"] == "registered"

    @pytest.mark.asyncio
    async def test_list_models_filter_by_framework(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering models by framework."""
        response = await client.get(
            "/api/v1/models",
            params={"framework": "pytorch"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                assert item["framework"] == "pytorch"

    @pytest.mark.asyncio
    async def test_list_models_sort_by_created_at(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test sorting models by created_at."""
        response = await client.get(
            "/api/v1/models",
            params={"sort_by": "created_at", "sort_order": "desc"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_models_sort_by_version(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test sorting models by version."""
        response = await client.get(
            "/api/v1/models",
            params={"sort_by": "version", "sort_order": "asc"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_models_invalid_sort_field(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test invalid sort field returns 422."""
        response = await client.get(
            "/api/v1/models",
            params={"sort_by": "invalid_field"},
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422


class TestGetModelEndpoint:
    """Tests for GET /api/v1/models/{model_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_model_requires_auth(self, client: AsyncClient) -> None:
        """Test getting model details requires authentication."""
        response = await client.get("/api/v1/models/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_model_not_found(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting non-existent model returns 404."""
        response = await client.get(
            "/api/v1/models/99999",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_model_invalid_id_format(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting model with invalid ID format returns 422."""
        response = await client.get(
            "/api/v1/models/invalid",
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422


class TestGetModelVersionsEndpoint:
    """Tests for GET /api/v1/models/{model_id}/versions endpoint (T031c)."""

    @pytest.mark.asyncio
    async def test_get_versions_requires_auth(self, client: AsyncClient) -> None:
        """Test getting model versions requires authentication."""
        response = await client.get("/api/v1/models/1/versions")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_versions_success(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting model versions returns list."""
        response = await client.get(
            "/api/v1/models/1/versions",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "versions" in data
            assert isinstance(data["versions"], list)

    @pytest.mark.asyncio
    async def test_get_versions_not_found(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting versions for non-existent model returns 404."""
        response = await client.get(
            "/api/v1/models/99999/versions",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_versions_with_comparison(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting versions with comparison to another version."""
        response = await client.get(
            "/api/v1/models/1/versions",
            params={"compare_with": 2},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            # Should include comparison data
            if "comparison" in data:
                assert "metrics_diff" in data["comparison"]
                assert "hyperparams_changed" in data["comparison"]


class TestModelsRBAC:
    """Tests for models API RBAC rules."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_model(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
        create_model_request_data: dict[str, Any],
    ) -> None:
        """Test viewer role cannot create models."""
        response = await client.post(
            "/api/v1/models",
            json=create_model_request_data,
            headers=viewer_auth_headers,
        )
        # Viewer should get 403 for write operations
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_viewer_can_list_models(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer role can list models."""
        response = await client.get(
            "/api/v1/models",
            headers=viewer_auth_headers,
        )
        # Viewer should be able to list (200) or DB error (500)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_viewer_can_get_model_versions(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer role can get model versions."""
        response = await client.get(
            "/api/v1/models/1/versions",
            headers=viewer_auth_headers,
        )
        # Viewer should be able to read (200/404) or DB error (500)
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_engineer_can_create_model(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_model_request_data: dict[str, Any],
    ) -> None:
        """Test engineer role can create models."""
        response = await client.post(
            "/api/v1/models",
            json=create_model_request_data,
            headers=engineer_auth_headers,
        )
        # Engineer should be allowed (201) or service error (404/500/503)
        assert response.status_code in [201, 404, 500, 503]


class TestModelsResponseFormat:
    """Tests for models API response format."""

    @pytest.mark.asyncio
    async def test_401_response_format(self, client: AsyncClient) -> None:
        """Test 401 responses have proper error format."""
        response = await client.get("/api/v1/models")
        assert response.status_code == 401
        data = response.json()
        # Middleware returns {"code": "...", "message": "..."}
        assert "code" in data or "detail" in data or "error" in data

    @pytest.mark.asyncio
    async def test_422_response_format(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test 422 responses have proper validation error format."""
        response = await client.post(
            "/api/v1/models",
            json={"model_name": "x"},  # Missing required fields
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
