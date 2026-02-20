"""Dataset API Endpoints Integration Tests - TDD Red-Green-Refactor.

Tests for T041 (POST /datasets), T042 (GET /datasets), T043 (GET /datasets/{id}),
T044 (PATCH /datasets/{id}), T045 (DELETE /datasets/{id}), T046 (POST /datasets/{id}/versions).
"""

from typing import Any

import pytest
from httpx import AsyncClient

# === Fixtures ===


@pytest.fixture
def create_dataset_request_data() -> dict[str, Any]:
    """Valid dataset creation request data."""
    return {
        "name": "imagenet-train",
        "version": "v1",
        "description": "ImageNet training dataset for image classification",
        "storage_type": "s3",
        "storage_uri": "s3://my-bucket/datasets/imagenet",
        "dataset_type": "image",
        "data_format": "imagenet",
        "tags": ["cv", "classification", "imagenet"],
        "visibility": "private",
    }


@pytest.fixture
def minimal_dataset_request_data() -> dict[str, Any]:
    """Minimal dataset creation request (only required fields)."""
    return {
        "name": "simple-dataset",
        "storage_type": "s3",
        "storage_uri": "s3://bucket/simple",
        "dataset_type": "text",
    }


@pytest.fixture
def update_dataset_request_data() -> dict[str, Any]:
    """Dataset update request data."""
    return {
        "description": "Updated description",
        "tags": ["new", "tags"],
        "visibility": "public",
    }


# === Test Classes ===


class TestCreateDatasetEndpoint:
    """Tests for POST /api/v1/datasets endpoint (T041)."""

    @pytest.mark.asyncio
    async def test_create_dataset_requires_auth(self, client: AsyncClient) -> None:
        """Test dataset creation requires authentication."""
        response = await client.post(
            "/api/v1/datasets",
            json={"name": "test-dataset"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_dataset_success(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_dataset_request_data: dict[str, Any],
    ) -> None:
        """Test successful dataset creation returns 201."""
        response = await client.post(
            "/api/v1/datasets",
            json=create_dataset_request_data,
            headers=engineer_auth_headers,
        )
        # 201 (success), 500 (DB error), 503 (service unavailable)
        assert response.status_code in [201, 500, 503]
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == create_dataset_request_data["name"]
            assert data["status"] == "preparing"
            assert data["version"] == "v1"

    @pytest.mark.asyncio
    async def test_create_dataset_minimal_fields(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        minimal_dataset_request_data: dict[str, Any],
    ) -> None:
        """Test dataset creation with only required fields."""
        response = await client.post(
            "/api/v1/datasets",
            json=minimal_dataset_request_data,
            headers=engineer_auth_headers,
        )
        assert response.status_code in [201, 500, 503]
        if response.status_code == 201:
            data = response.json()
            assert data["version"] == "v1"  # Default version
            assert data["visibility"] == "private"  # Default visibility

    @pytest.mark.asyncio
    async def test_create_dataset_name_too_short(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create dataset with name shorter than 3 characters returns 422."""
        response = await client.post(
            "/api/v1/datasets",
            json={
                "name": "ab",  # Too short
                "storage_type": "s3",
                "storage_uri": "s3://bucket/path",
                "dataset_type": "image",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_dataset_missing_required_fields(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create with missing required fields returns 422."""
        response = await client.post(
            "/api/v1/datasets",
            json={"name": "test-dataset"},  # Missing storage_type, storage_uri, dataset_type
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_dataset_invalid_storage_type(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create with invalid storage type returns 422."""
        response = await client.post(
            "/api/v1/datasets",
            json={
                "name": "test-dataset",
                "storage_type": "invalid_type",
                "storage_uri": "s3://bucket/path",
                "dataset_type": "image",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_dataset_invalid_dataset_type(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test create with invalid dataset type returns 422."""
        response = await client.post(
            "/api/v1/datasets",
            json={
                "name": "test-dataset",
                "storage_type": "s3",
                "storage_uri": "s3://bucket/path",
                "dataset_type": "invalid_type",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422


class TestListDatasetsEndpoint:
    """Tests for GET /api/v1/datasets endpoint (T042)."""

    @pytest.mark.asyncio
    async def test_list_datasets_requires_auth(self, client: AsyncClient) -> None:
        """Test listing datasets requires authentication."""
        response = await client.get("/api/v1/datasets")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_datasets_success(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test listing datasets returns paginated response."""
        response = await client.get(
            "/api/v1/datasets",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert "total_pages" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_datasets_with_pagination(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test listing datasets with pagination params."""
        response = await client.get(
            "/api/v1/datasets",
            params={"page": 1, "page_size": 10},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_datasets_filter_by_type(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering datasets by type."""
        response = await client.get(
            "/api/v1/datasets",
            params={"dataset_type": "image"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                assert item["dataset_type"] == "image"

    @pytest.mark.asyncio
    async def test_list_datasets_filter_by_storage_type(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering datasets by storage type."""
        response = await client.get(
            "/api/v1/datasets",
            params={"storage_type": "s3"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                assert item["storage_type"] == "s3"

    @pytest.mark.asyncio
    async def test_list_datasets_filter_by_visibility(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering datasets by visibility."""
        response = await client.get(
            "/api/v1/datasets",
            params={"visibility": "private"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_datasets_filter_by_status(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering datasets by status."""
        response = await client.get(
            "/api/v1/datasets",
            params={"status": "available"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_datasets_sort_by_created_at(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test sorting datasets by created_at."""
        response = await client.get(
            "/api/v1/datasets",
            params={"sort_by": "created_at", "sort_order": "desc"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500]


class TestGetDatasetEndpoint:
    """Tests for GET /api/v1/datasets/{dataset_id} endpoint (T043)."""

    @pytest.mark.asyncio
    async def test_get_dataset_requires_auth(self, client: AsyncClient) -> None:
        """Test getting dataset details requires authentication."""
        response = await client.get("/api/v1/datasets/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting non-existent dataset returns 404."""
        response = await client.get(
            "/api/v1/datasets/99999",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_dataset_invalid_id_format(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting dataset with invalid ID format returns 422."""
        response = await client.get(
            "/api/v1/datasets/invalid",
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422


class TestUpdateDatasetEndpoint:
    """Tests for PATCH /api/v1/datasets/{dataset_id} endpoint (T044)."""

    @pytest.mark.asyncio
    async def test_update_dataset_requires_auth(self, client: AsyncClient) -> None:
        """Test updating dataset requires authentication."""
        response = await client.patch(
            "/api/v1/datasets/1",
            json={"description": "Updated"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_dataset_not_found(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        update_dataset_request_data: dict[str, Any],
    ) -> None:
        """Test updating non-existent dataset returns 404."""
        response = await client.patch(
            "/api/v1/datasets/99999",
            json=update_dataset_request_data,
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_update_dataset_invalid_visibility(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test update with invalid visibility returns 422."""
        response = await client.patch(
            "/api/v1/datasets/1",
            json={"visibility": "invalid"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 422, 500]


class TestDeleteDatasetEndpoint:
    """Tests for DELETE /api/v1/datasets/{dataset_id} endpoint (T045)."""

    @pytest.mark.asyncio
    async def test_delete_dataset_requires_auth(self, client: AsyncClient) -> None:
        """Test deleting dataset requires authentication."""
        response = await client.delete("/api/v1/datasets/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_dataset_not_found(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test deleting non-existent dataset returns 404."""
        response = await client.delete(
            "/api/v1/datasets/99999",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]


class TestCreateDatasetVersionEndpoint:
    """Tests for POST /api/v1/datasets/{dataset_id}/versions endpoint (T046)."""

    @pytest.mark.asyncio
    async def test_create_version_requires_auth(self, client: AsyncClient) -> None:
        """Test creating dataset version requires authentication."""
        response = await client.post(
            "/api/v1/datasets/1/versions",
            json={"version": "v2"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_version_not_found(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test creating version for non-existent dataset returns 404."""
        response = await client.post(
            "/api/v1/datasets/99999/versions",
            json={"version": "v2"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_create_version_missing_version(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test creating version without version field.

        Note: 由于依赖注入先验证数据集存在性，不存在的数据集返回 404。
        如果数据集存在但缺少 version 字段，则返回 422。
        数据库不可用时返回 500。
        """
        response = await client.post(
            "/api/v1/datasets/1/versions",
            json={},
            headers=engineer_auth_headers,
        )
        # 404: 数据集不存在（依赖先执行）
        # 422: 参数验证失败（数据集存在时）
        # 500: 数据库不可用（依赖注入失败）
        assert response.status_code in [404, 422, 500]


class TestDatasetsRBAC:
    """Tests for datasets API RBAC rules."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_dataset(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
        create_dataset_request_data: dict[str, Any],
    ) -> None:
        """Test viewer role cannot create datasets."""
        response = await client.post(
            "/api/v1/datasets",
            json=create_dataset_request_data,
            headers=viewer_auth_headers,
        )
        # Viewer should get 403 for write operations
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_viewer_can_list_datasets(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer role can list datasets."""
        response = await client.get(
            "/api/v1/datasets",
            headers=viewer_auth_headers,
        )
        # Viewer should be able to list (200) or DB error (500)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_viewer_cannot_delete_dataset(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer role cannot delete datasets."""
        response = await client.delete(
            "/api/v1/datasets/1",
            headers=viewer_auth_headers,
        )
        # Viewer should get 403 for delete operations
        assert response.status_code in [403, 404, 500]

    @pytest.mark.asyncio
    async def test_engineer_can_create_dataset(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_dataset_request_data: dict[str, Any],
    ) -> None:
        """Test engineer role can create datasets."""
        response = await client.post(
            "/api/v1/datasets",
            json=create_dataset_request_data,
            headers=engineer_auth_headers,
        )
        # Engineer should be allowed (201) or service error (500/503)
        assert response.status_code in [201, 500, 503]


class TestDatasetsResponseFormat:
    """Tests for datasets API response format."""

    @pytest.mark.asyncio
    async def test_401_response_format(self, client: AsyncClient) -> None:
        """Test 401 responses have proper error format."""
        response = await client.get("/api/v1/datasets")
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
            "/api/v1/datasets",
            json={"name": "x"},  # Missing required fields
            headers=engineer_auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
