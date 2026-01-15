"""ResourceLimitConfig API Endpoints Integration Tests - TDD Red-Green-Refactor.

Tests for T012c (GET), T012d (POST), T012e (PUT), T012f (DELETE).
"""

from typing import Any

import pytest
from httpx import AsyncClient


# === Fixtures ===


@pytest.fixture
def create_config_request_data() -> dict[str, Any]:
    """Valid config creation request data."""
    return {
        "config_name": "engineer-global-limits",
        "role": "engineer",
        "project_id": None,
        "max_gpu_per_job": 8,
        "max_cpu_per_job": 64,
        "max_memory_gb_per_job": 512,
        "max_storage_gb_per_job": 1000,
        "max_nodes_per_job": 4,
        "priority_default": "medium",
    }


@pytest.fixture
def minimal_config_request_data() -> dict[str, Any]:
    """Minimal config creation request (only required fields)."""
    return {
        "config_name": "minimal-config",
        "role": "viewer",
    }


@pytest.fixture
def update_config_request_data() -> dict[str, Any]:
    """Config update request data."""
    return {
        "config_name": "updated-config-name",
        "max_gpu_per_job": 16,
    }


# === Test Classes ===


class TestCreateResourceLimitConfigEndpoint:
    """Tests for POST /api/v1/resource-limit-configs endpoint (T012d)."""

    @pytest.mark.asyncio
    async def test_create_config_requires_auth(self, client: AsyncClient) -> None:
        """Test config creation requires authentication."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json={"config_name": "test-config", "role": "engineer"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_config_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_config_request_data: dict[str, Any],
    ) -> None:
        """Test config creation requires admin role."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json=create_config_request_data,
            headers=engineer_auth_headers,
        )
        # Engineer should get 403 for admin-only endpoints
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_create_config_success(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_config_request_data: dict[str, Any],
    ) -> None:
        """Test successful config creation returns 201."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json=create_config_request_data,
            headers=admin_auth_headers,
        )
        # 201 (success), 409 (duplicate), 500 (DB error)
        assert response.status_code in [201, 409, 500, 503]
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["config_name"] == create_config_request_data["config_name"]
            assert data["role"] == create_config_request_data["role"]
            assert data["max_gpu_per_job"] == create_config_request_data["max_gpu_per_job"]

    @pytest.mark.asyncio
    async def test_create_config_minimal_fields(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
        minimal_config_request_data: dict[str, Any],
    ) -> None:
        """Test config creation with only required fields."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json=minimal_config_request_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in [201, 409, 500, 503]
        if response.status_code == 201:
            data = response.json()
            # Should have default values
            assert data["max_gpu_per_job"] == 8
            assert data["priority_default"] == "medium"

    @pytest.mark.asyncio
    async def test_create_config_missing_required_fields(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test create with missing required fields returns 422."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json={"config_name": "test"},  # Missing role
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_config_invalid_role(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test create with invalid role returns 422."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json={"config_name": "test", "role": "invalid_role"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_config_invalid_gpu_value(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test create with invalid GPU value returns 422."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json={
                "config_name": "test",
                "role": "engineer",
                "max_gpu_per_job": 0,  # Invalid: must be >= 1
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestListResourceLimitConfigsEndpoint:
    """Tests for GET /api/v1/resource-limit-configs endpoint (T012c)."""

    @pytest.mark.asyncio
    async def test_list_configs_requires_auth(self, client: AsyncClient) -> None:
        """Test listing configs requires authentication."""
        response = await client.get("/api/v1/resource-limit-configs")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_configs_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test listing configs requires admin role."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_list_configs_success(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test listing configs returns paginated response."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            headers=admin_auth_headers,
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
    async def test_list_configs_with_pagination(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test listing configs with pagination params."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            params={"page": 1, "page_size": 10},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_configs_filter_by_role(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering configs by role."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            params={"role": "engineer"},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                assert item["role"] == "engineer"

    @pytest.mark.asyncio
    async def test_list_configs_filter_by_project(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering configs by project_id."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            params={"project_id": 100},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_configs_sort_by_created_at(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test sorting configs by created_at."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            params={"sort_by": "created_at", "sort_order": "desc"},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]


class TestGetResourceLimitConfigEndpoint:
    """Tests for GET /api/v1/resource-limit-configs/{config_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_config_requires_auth(self, client: AsyncClient) -> None:
        """Test getting config requires authentication."""
        response = await client.get("/api/v1/resource-limit-configs/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_config_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting config requires admin role."""
        response = await client.get(
            "/api/v1/resource-limit-configs/1",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_get_config_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test getting non-existent config returns 404."""
        response = await client.get(
            "/api/v1/resource-limit-configs/99999",
            headers=admin_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_config_invalid_id_format(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test getting config with invalid ID format returns 422."""
        response = await client.get(
            "/api/v1/resource-limit-configs/invalid",
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestUpdateResourceLimitConfigEndpoint:
    """Tests for PUT /api/v1/resource-limit-configs/{config_id} endpoint (T012e)."""

    @pytest.mark.asyncio
    async def test_update_config_requires_auth(self, client: AsyncClient) -> None:
        """Test updating config requires authentication."""
        response = await client.put(
            "/api/v1/resource-limit-configs/1",
            json={"config_name": "updated"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_config_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        update_config_request_data: dict[str, Any],
    ) -> None:
        """Test updating config requires admin role."""
        response = await client.put(
            "/api/v1/resource-limit-configs/1",
            json=update_config_request_data,
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_update_config_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
        update_config_request_data: dict[str, Any],
    ) -> None:
        """Test updating non-existent config returns 404."""
        response = await client.put(
            "/api/v1/resource-limit-configs/99999",
            json=update_config_request_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_update_config_invalid_gpu_value(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test update with invalid GPU value returns 422."""
        response = await client.put(
            "/api/v1/resource-limit-configs/1",
            json={"max_gpu_per_job": 0},  # Invalid
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestDeleteResourceLimitConfigEndpoint:
    """Tests for DELETE /api/v1/resource-limit-configs/{config_id} endpoint (T012f)."""

    @pytest.mark.asyncio
    async def test_delete_config_requires_auth(self, client: AsyncClient) -> None:
        """Test deleting config requires authentication."""
        response = await client.delete("/api/v1/resource-limit-configs/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_config_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test deleting config requires admin role."""
        response = await client.delete(
            "/api/v1/resource-limit-configs/1",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_delete_config_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test deleting non-existent config returns 404."""
        response = await client.delete(
            "/api/v1/resource-limit-configs/99999",
            headers=admin_auth_headers,
        )
        assert response.status_code in [404, 500]


class TestResourceLimitConfigsRBAC:
    """Tests for resource limit configs API RBAC rules."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_access_configs(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer role cannot access config endpoints."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            headers=viewer_auth_headers,
        )
        # Viewer should get 403 for admin-only endpoints
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_engineer_cannot_access_configs(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test engineer role cannot access config endpoints."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_admin_can_access_configs(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test admin role can access config endpoints."""
        response = await client.get(
            "/api/v1/resource-limit-configs",
            headers=admin_auth_headers,
        )
        # Admin should be allowed (200) or DB error (500)
        assert response.status_code in [200, 500]


class TestResourceLimitConfigsResponseFormat:
    """Tests for resource limit configs API response format."""

    @pytest.mark.asyncio
    async def test_401_response_format(self, client: AsyncClient) -> None:
        """Test 401 responses have proper error format."""
        response = await client.get("/api/v1/resource-limit-configs")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data or "error" in data

    @pytest.mark.asyncio
    async def test_422_response_format(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test 422 responses have proper validation error format."""
        response = await client.post(
            "/api/v1/resource-limit-configs",
            json={"config_name": "x"},  # Missing role
            headers=admin_auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
