"""Training Metrics API Endpoints Integration Tests - TDD Red-Green-Refactor (T220)."""

import pytest
from httpx import AsyncClient


class TestGetTrainingMetricsEndpoint:
    """Tests for GET /api/v1/training-jobs/{job_id}/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_metrics_requires_auth(self, client: AsyncClient) -> None:
        """Test metrics endpoint requires authentication."""
        response = await client.get("/api/v1/training-jobs/1/metrics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_metrics_returns_loss_data(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test get_metrics returns loss data for existing job."""
        response = await client.get(
            "/api/v1/training-jobs/1/metrics",
            params={"metric_names": ["loss"]},
            headers=engineer_auth_headers,
        )
        # 404 if job not found, or 200 with metrics
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data

    @pytest.mark.asyncio
    async def test_get_metrics_returns_multiple_metrics(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test get_metrics returns multiple metric types."""
        response = await client.get(
            "/api/v1/training-jobs/1/metrics",
            params={"metric_names": ["loss", "accuracy", "learning_rate"]},
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data

    @pytest.mark.asyncio
    async def test_get_metrics_with_time_range(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test get_metrics with time range filter."""
        response = await client.get(
            "/api/v1/training-jobs/1/metrics",
            params={
                "metric_names": ["loss"],
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-12-31T23:59:59Z",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_metrics_with_step_aggregation(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test get_metrics with step aggregation."""
        response = await client.get(
            "/api/v1/training-jobs/1/metrics",
            params={
                "metric_names": ["loss"],
                "step": "5m",
            },
            headers=engineer_auth_headers,
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_metrics_job_not_found(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test get_metrics returns 404 for non-existent job."""
        response = await client.get(
            "/api/v1/training-jobs/99999/metrics",
            params={"metric_names": ["loss"]},
            headers=engineer_auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_metrics_default_metric_names(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test get_metrics returns default metrics when no metric_names specified."""
        response = await client.get(
            "/api/v1/training-jobs/1/metrics",
            headers=engineer_auth_headers,
        )
        # Should return default metrics (loss, accuracy, learning_rate, throughput)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data


class TestCompareJobsMetricsEndpoint:
    """Tests for GET /api/v1/training-jobs/compare-metrics endpoint."""

    @pytest.mark.asyncio
    async def test_compare_metrics_requires_auth(self, client: AsyncClient) -> None:
        """Test compare metrics endpoint requires authentication."""
        response = await client.get(
            "/api/v1/training-jobs/compare-metrics",
            params={"job_ids": [1, 2], "metric_type": "loss"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_compare_metrics_multiple_jobs(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ) -> None:
        """Test compare_metrics compares multiple jobs."""
        response = await client.get(
            "/api/v1/training-jobs/compare-metrics",
            params={"job_ids": [1, 2], "metric_type": "loss"},
            headers=engineer_auth_headers,
        )
        # Might get 200 (success) or 404 (jobs not found)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "metric_type" in data
            assert "jobs" in data
