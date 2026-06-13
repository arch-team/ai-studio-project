"""监控页端点集成测试 - TDD Red-Green-Refactor (Task 2C.4).

覆盖前端监控页调用的端点：
- 集群列表（无 monitoring 前缀）/api/v1/clusters
- 资源利用率 /api/v1/monitoring/utilization
- 告警分页 /api/v1/monitoring/alerts

并验证故障降级：AMP/SageMaker 故障时返回 200 + 空数据，不返回 5xx。
"""

import pytest
from httpx import AsyncClient


class TestGetClustersEndpoint:
    """Tests for GET /api/v1/clusters endpoint (无 monitoring 前缀)."""

    @pytest.mark.asyncio
    async def test_get_clusters_requires_auth(self, client: AsyncClient) -> None:
        """未认证访问集群列表返回 401."""
        resp = await client.get("/api/v1/clusters")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_clusters_returns_list(self, client: AsyncClient, engineer_auth_headers: dict[str, str]) -> None:
        """已认证访问集群列表返回 200 + 分页结构（items/total）."""
        resp = await client.get("/api/v1/clusters", headers=engineer_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body and "total" in body


class TestGetUtilizationEndpoint:
    """Tests for GET /api/v1/monitoring/utilization endpoint."""

    @pytest.mark.asyncio
    async def test_get_utilization_requires_auth(self, client: AsyncClient) -> None:
        """未认证访问利用率返回 401."""
        resp = await client.get("/api/v1/monitoring/utilization")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_utilization_returns_list(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """已认证访问利用率返回 200 + list."""
        resp = await client.get("/api/v1/monitoring/utilization", headers=engineer_auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestGetAlertsEndpoint:
    """Tests for GET /api/v1/monitoring/alerts endpoint."""

    @pytest.mark.asyncio
    async def test_get_alerts_requires_auth(self, client: AsyncClient) -> None:
        """未认证访问告警返回 401."""
        resp = await client.get("/api/v1/monitoring/alerts")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_alerts_returns_empty_paginated(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """告警子系统未实现，返回 200 + 空分页集."""
        resp = await client.get("/api/v1/monitoring/alerts", headers=engineer_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == [] and body["total"] == 0
        assert body["total_pages"] == 0


class TestEndpointDegradation:
    """故障降级：依赖异常时返回 200 + 空数据，不 5xx。"""

    @pytest.mark.asyncio
    async def test_utilization_degrades_to_200_on_failure(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """AMP 故障时返回 200 + 空 list，不 5xx。"""
        from unittest.mock import AsyncMock

        from src.main import app
        from src.modules.monitoring.api.dependencies import get_prometheus_service

        failing = AsyncMock()
        failing.get_resource_utilization.side_effect = Exception("AMP unreachable")
        app.dependency_overrides[get_prometheus_service] = lambda: failing
        try:
            resp = await client.get("/api/v1/monitoring/utilization", headers=engineer_auth_headers)
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            app.dependency_overrides.pop(get_prometheus_service, None)

    @pytest.mark.asyncio
    async def test_get_clusters_degrades_to_200_on_failure(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """集群回源失败时返回 200 + 空列表，不 5xx。"""
        from unittest.mock import AsyncMock

        from src.main import app
        from src.modules.monitoring.api.dependencies import get_cluster_sync_service

        failing = AsyncMock()
        failing.get_clusters.side_effect = Exception("SageMaker down")
        app.dependency_overrides[get_cluster_sync_service] = lambda: failing
        try:
            resp = await client.get("/api/v1/clusters", headers=engineer_auth_headers)
            assert resp.status_code == 200
            assert resp.json()["items"] == []
        finally:
            app.dependency_overrides.pop(get_cluster_sync_service, None)
