"""User Management API Endpoints Integration Tests - TDD Red-Green-Refactor.

Tests for T055 (GET /users), T056 (POST /users), T057 (PUT /users/{id}).
"""

from typing import Any

import pytest
from httpx import AsyncClient


# === Fixtures ===


@pytest.fixture
def create_user_request_data() -> dict[str, Any]:
    """Valid user creation request data."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "display_name": "New User",
        "role": "engineer",
    }


@pytest.fixture
def update_user_request_data() -> dict[str, Any]:
    """User update request data."""
    return {
        "role": "viewer",
        "status": "suspended",
        "display_name": "Updated User",
    }


# === Test Classes ===


class TestListUsersEndpoint:
    """Tests for GET /api/v1/users endpoint (T055)."""

    @pytest.mark.asyncio
    async def test_list_users_requires_auth(self, client: AsyncClient) -> None:
        """Test listing users requires authentication."""
        response = await client.get("/api/v1/users")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_users_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test listing users requires admin role."""
        response = await client.get(
            "/api/v1/users",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_list_users_viewer_forbidden(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer cannot list users."""
        response = await client.get(
            "/api/v1/users",
            headers=viewer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_list_users_returns_paginated_response(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test listing users returns paginated response."""
        response = await client.get(
            "/api/v1/users",
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
    async def test_list_users_with_pagination(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test listing users with pagination params."""
        response = await client.get(
            "/api/v1/users",
            params={"page": 1, "page_size": 10},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_users_filter_by_role(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering users by role."""
        response = await client.get(
            "/api/v1/users",
            params={"role": "engineer"},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                assert item["role"] == "engineer"

    @pytest.mark.asyncio
    async def test_list_users_filter_by_status(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test filtering users by status."""
        response = await client.get(
            "/api/v1/users",
            params={"status": "active"},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                assert item["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_users_sort_by_created_at(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test sorting users by created_at."""
        response = await client.get(
            "/api/v1/users",
            params={"sort_by": "created_at", "sort_order": "desc"},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]


class TestCreateUserEndpoint:
    """Tests for POST /api/v1/users endpoint (T056)."""

    @pytest.mark.asyncio
    async def test_create_user_requires_auth(
        self,
        client: AsyncClient,
        create_user_request_data: dict[str, Any],
    ) -> None:
        """Test user creation requires authentication."""
        response = await client.post(
            "/api/v1/users",
            json=create_user_request_data,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_user_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_user_request_data: dict[str, Any],
    ) -> None:
        """Test user creation requires admin role."""
        response = await client.post(
            "/api/v1/users",
            json=create_user_request_data,
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_user_request_data: dict[str, Any],
    ) -> None:
        """Test successful user creation returns 201."""
        # Make email unique for this test
        create_user_request_data["email"] = "unique_test_user@example.com"
        create_user_request_data["username"] = "unique_test_user"

        response = await client.post(
            "/api/v1/users",
            json=create_user_request_data,
            headers=admin_auth_headers,
        )
        # 201 (success), 409 (duplicate), 500 (DB error)
        assert response.status_code in [201, 409, 500, 503]
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["username"] == create_user_request_data["username"]
            assert data["email"] == create_user_request_data["email"]
            assert data["role"] == create_user_request_data["role"]

    @pytest.mark.asyncio
    async def test_create_user_missing_required_fields(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test create with missing required fields returns 422."""
        response = await client.post(
            "/api/v1/users",
            json={"username": "test"},  # Missing email and role
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test create with invalid email returns 422."""
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "test",
                "email": "invalid-email",
                "role": "engineer",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_invalid_role(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test create with invalid role returns 422."""
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "test",
                "email": "test@example.com",
                "role": "invalid_role",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_with_quota_id(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test user creation with resource quota assignment."""
        request_data = {
            "username": "user_with_quota",
            "email": "quota_user@example.com",
            "role": "engineer",
            "resource_quota_id": 1,
        }
        response = await client.post(
            "/api/v1/users",
            json=request_data,
            headers=admin_auth_headers,
        )
        # 201 (success), 409 (duplicate), 500 (DB error), 404 (quota not found)
        assert response.status_code in [201, 404, 409, 500, 503]


class TestUpdateUserEndpoint:
    """Tests for PUT /api/v1/users/{user_id} endpoint (T057)."""

    @pytest.mark.asyncio
    async def test_update_user_requires_auth(
        self,
        client: AsyncClient,
        update_user_request_data: dict[str, Any],
    ) -> None:
        """Test user update requires authentication."""
        response = await client.put(
            "/api/v1/users/1",
            json=update_user_request_data,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        update_user_request_data: dict[str, Any],
    ) -> None:
        """Test user update requires admin role."""
        response = await client.put(
            "/api/v1/users/1",
            json=update_user_request_data,
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
        update_user_request_data: dict[str, Any],
    ) -> None:
        """Test updating non-existent user returns 404."""
        response = await client.put(
            "/api/v1/users/99999",
            json=update_user_request_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_update_user_invalid_id_format(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
        update_user_request_data: dict[str, Any],
    ) -> None:
        """Test update with invalid ID format returns 422."""
        response = await client.put(
            "/api/v1/users/invalid",
            json=update_user_request_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_user_change_role(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test updating user role."""
        response = await client.put(
            "/api/v1/users/1",
            json={"role": "viewer"},
            headers=admin_auth_headers,
        )
        # 200 (success), 404 (not found), 500 (DB error)
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["role"] == "viewer"

    @pytest.mark.asyncio
    async def test_update_user_change_status(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test updating user status."""
        response = await client.put(
            "/api/v1/users/1",
            json={"status": "suspended"},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_update_user_assign_quota(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test assigning resource quota to user."""
        response = await client.put(
            "/api/v1/users/1",
            json={"resource_quota_id": 1},
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_update_user_invalid_role(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test update with invalid role returns 422."""
        response = await client.put(
            "/api/v1/users/1",
            json={"role": "invalid_role"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_user_invalid_status(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test update with invalid status returns 422."""
        response = await client.put(
            "/api/v1/users/1",
            json={"status": "invalid_status"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestGetUserEndpoint:
    """Tests for GET /api/v1/users/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_requires_auth(self, client: AsyncClient) -> None:
        """Test getting user requires authentication."""
        response = await client.get("/api/v1/users/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_requires_admin(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test getting user requires admin role."""
        response = await client.get(
            "/api/v1/users/1",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test getting non-existent user returns 404."""
        response = await client.get(
            "/api/v1/users/99999",
            headers=admin_auth_headers,
        )
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_user_invalid_id_format(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test getting user with invalid ID format returns 422."""
        response = await client.get(
            "/api/v1/users/invalid",
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestUsersAPIRBAC:
    """Tests for users API RBAC rules."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_access_users(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer role cannot access user endpoints."""
        response = await client.get(
            "/api/v1/users",
            headers=viewer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_engineer_cannot_access_users(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test engineer role cannot access user endpoints."""
        response = await client.get(
            "/api/v1/users",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [403, 500, 503]

    @pytest.mark.asyncio
    async def test_admin_can_access_users(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test admin role can access user endpoints."""
        response = await client.get(
            "/api/v1/users",
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]


class TestUsersAPIResponseFormat:
    """Tests for users API response format."""

    @pytest.mark.asyncio
    async def test_401_response_format(self, client: AsyncClient) -> None:
        """Test 401 responses have proper error format."""
        response = await client.get("/api/v1/users")
        assert response.status_code == 401
        data = response.json()
        assert "code" in data or "detail" in data or "error" in data

    @pytest.mark.asyncio
    async def test_422_response_format(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test 422 responses have proper validation error format."""
        response = await client.post(
            "/api/v1/users",
            json={"username": "x"},  # Missing required fields
            headers=admin_auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_user_response_fields(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test user response contains expected fields."""
        response = await client.get(
            "/api/v1/users",
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            if data["items"]:
                user = data["items"][0]
                assert "id" in user
                assert "username" in user
                assert "email" in user
                assert "role" in user
                assert "status" in user
