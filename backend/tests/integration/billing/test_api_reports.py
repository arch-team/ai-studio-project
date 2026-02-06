"""报表 API 端点集成测试 (T071, T072)."""

from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.integration
@pytest.mark.asyncio
class TestResourceUsageReportAPI:
    """资源使用报表 API 集成测试 (T071)."""

    async def test_get_resource_usage_report_success(self, client: AsyncClient, engineer_auth_headers: dict):
        """测试成功获取资源使用报表."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        response = await client.get(
            "/api/v1/reports/resource-usage",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": "day",
                "page": 1,
                "page_size": 20,
            },
            headers=engineer_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data_points" in data
        assert "total_cpu_hours" in data
        assert "total_gpu_hours" in data
        assert "total_storage_gb_hours" in data
        assert "total_jobs" in data
        assert "page" in data
        assert "page_size" in data
        assert data["group_by"] == "day"

    async def test_get_resource_usage_report_with_user_filter(self, client: AsyncClient, engineer_auth_headers: dict):
        """测试用户过滤的资源使用报表."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        response = await client.get(
            "/api/v1/reports/resource-usage",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "user_id": 1,
                "group_by": "week",
            },
            headers=engineer_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 1
        assert data["group_by"] == "week"

    async def test_get_resource_usage_report_missing_dates(self, client: AsyncClient, engineer_auth_headers: dict):
        """测试缺少必需的日期参数."""
        response = await client.get(
            "/api/v1/reports/resource-usage",
            headers=engineer_auth_headers,
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.asyncio
class TestCostAnalysisReportAPI:
    """成本分析报表 API 集成测试 (T072)."""

    async def test_get_cost_analysis_report_success(self, client: AsyncClient, engineer_auth_headers: dict):
        """测试成功获取成本分析报表."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        response = await client.get(
            "/api/v1/reports/cost-analysis",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": 1,
                "page_size": 20,
            },
            headers=engineer_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data_points" in data
        assert "total_compute_cost" in data
        assert "total_storage_cost" in data
        assert "total_network_cost" in data
        assert "grand_total_cost" in data
        assert "trend" in data
        assert "page" in data
        assert "page_size" in data

    async def test_get_cost_analysis_report_with_cost_type_filter(
        self, client: AsyncClient, engineer_auth_headers: dict
    ):
        """测试成本类型过滤."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        response = await client.get(
            "/api/v1/reports/cost-analysis",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "cost_type": "compute",
            },
            headers=engineer_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cost_type"] == "compute"

    async def test_get_cost_analysis_report_with_user_filter(self, client: AsyncClient, engineer_auth_headers: dict):
        """测试用户过滤的成本分析报表."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        response = await client.get(
            "/api/v1/reports/cost-analysis",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "user_id": 1,
            },
            headers=engineer_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestReportAuthRequirement:
    """测试报表 API 的认证要求."""

    async def test_resource_usage_report_requires_auth(self):
        """测试资源使用报表需要认证."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/reports/resource-usage",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

        assert response.status_code == 401  # Unauthorized

    async def test_cost_analysis_report_requires_auth(self):
        """测试成本分析报表需要认证."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/reports/cost-analysis",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

        assert response.status_code == 401  # Unauthorized
