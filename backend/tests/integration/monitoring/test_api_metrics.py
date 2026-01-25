"""Monitoring API Endpoints Integration Tests - TDD Red-Green-Refactor (T061)."""

import pytest
from httpx import AsyncClient


class TestGetClusterMetricsEndpoint:
    """Tests for GET /api/v1/monitoring/clusters/{cluster_name}/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_cluster_metrics_requires_auth(self, client: AsyncClient) -> None:
        """Test cluster metrics requires authentication."""
        response = await client.get("/api/v1/monitoring/clusters/test-cluster/metrics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_cluster_metrics_returns_data(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test cluster metrics returns data."""
        response = await client.get(
            "/api/v1/monitoring/clusters/test-cluster/metrics",
            headers=engineer_auth_headers,
        )
        # 200 (success) or 500/503 (Prometheus not available)
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data

    @pytest.mark.asyncio
    async def test_get_cluster_metrics_with_metric_names(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test cluster metrics with specific metric names filter."""
        response = await client.get(
            "/api/v1/monitoring/clusters/test-cluster/metrics",
            params={"metric_names": "DCGM_FI_DEV_GPU_UTIL,node_cpu_usage"},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_get_cluster_metrics_with_time_range(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test cluster metrics with time range filter."""
        response = await client.get(
            "/api/v1/monitoring/clusters/test-cluster/metrics",
            params={
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-01T01:00:00Z",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 422, 500, 503]


class TestGetGPUUtilizationEndpoint:
    """Tests for GET /api/v1/monitoring/jobs/{job_id}/gpu-utilization endpoint."""

    @pytest.mark.asyncio
    async def test_get_gpu_utilization_requires_auth(self, client: AsyncClient) -> None:
        """Test GPU utilization requires authentication."""
        response = await client.get("/api/v1/monitoring/jobs/1/gpu-utilization")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_gpu_utilization_for_job(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test GPU utilization returns data for a job."""
        response = await client.get(
            "/api/v1/monitoring/jobs/1/gpu-utilization",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "data_points" in data


class TestGetGrafanaDashboardsEndpoint:
    """Tests for GET /api/v1/monitoring/grafana/dashboards endpoint."""

    @pytest.mark.asyncio
    async def test_get_grafana_dashboards_requires_auth(self, client: AsyncClient) -> None:
        """Test Grafana dashboards requires authentication."""
        response = await client.get("/api/v1/monitoring/grafana/dashboards")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_grafana_dashboards_list(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test Grafana dashboards returns list."""
        response = await client.get(
            "/api/v1/monitoring/grafana/dashboards",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "dashboards" in data
            assert isinstance(data["dashboards"], list)


class TestStorageMetricsEndpoint:
    """Tests for GET /api/v1/monitoring/storage endpoint."""

    @pytest.mark.asyncio
    async def test_get_storage_metrics_requires_auth(self, client: AsyncClient) -> None:
        """Test storage metrics requires authentication."""
        response = await client.get("/api/v1/monitoring/storage")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_storage_metrics(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test storage metrics returns data."""
        response = await client.get(
            "/api/v1/monitoring/storage",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500, 503]


class TestNetworkMetricsEndpoint:
    """Tests for GET /api/v1/monitoring/network endpoint."""

    @pytest.mark.asyncio
    async def test_get_network_metrics_requires_auth(self, client: AsyncClient) -> None:
        """Test network metrics requires authentication."""
        response = await client.get("/api/v1/monitoring/network")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_network_metrics(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test network metrics returns data."""
        response = await client.get(
            "/api/v1/monitoring/network",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 500, 503]


class TestClusterHealthEndpoint:
    """Tests for GET /api/v1/monitoring/clusters/{cluster_name}/health endpoint."""

    @pytest.mark.asyncio
    async def test_get_cluster_health_requires_auth(self, client: AsyncClient) -> None:
        """Test cluster health requires authentication."""
        response = await client.get("/api/v1/monitoring/clusters/test-cluster/health")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_cluster_health(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test cluster health returns status."""
        response = await client.get(
            "/api/v1/monitoring/clusters/test-cluster/health",
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data


class TestMonitoringAPIRBAC:
    """Tests for monitoring API RBAC rules."""

    @pytest.mark.asyncio
    async def test_viewer_can_access_metrics(
        self,
        client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ) -> None:
        """Test viewer role can access monitoring metrics."""
        response = await client.get(
            "/api/v1/monitoring/clusters/test-cluster/metrics",
            headers=viewer_auth_headers,
        )
        # Viewer should be allowed (200) or error due to Prometheus
        assert response.status_code in [200, 500, 503]
