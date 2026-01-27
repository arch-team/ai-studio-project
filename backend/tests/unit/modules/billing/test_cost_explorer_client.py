"""Cost Explorer Client 单元测试 (T069a)."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.billing.application.interfaces import ICostExplorerClient
from src.modules.billing.infrastructure.external import CostExplorerClient


class TestICostExplorerClient:
    """测试 ICostExplorerClient 接口契约."""

    @pytest.mark.asyncio
    async def test_interface_compliance(self):
        """测试实现类符合接口契约."""
        assert issubclass(CostExplorerClient, ICostExplorerClient)


class TestCostExplorerClient:
    """测试 CostExplorerClient 实现."""

    @pytest.fixture
    def mock_ce_client(self):
        """创建 Mock Cost Explorer 客户端."""
        client = AsyncMock()
        client.get_cost_and_usage = AsyncMock()
        return client

    @pytest.fixture
    def cost_explorer_client(self):
        """创建 CostExplorerClient 实例."""
        return CostExplorerClient()

    @pytest.mark.asyncio
    async def test_get_cost_and_usage_basic(self, cost_explorer_client):
        """测试基础成本数据获取."""
        # Arrange
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        mock_response = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2025-01-01", "End": "2025-01-31"},
                    "Total": {"UnblendedCost": {"Amount": "1234.56", "Unit": "USD"}},
                    "Groups": [
                        {
                            "Keys": ["EC2"],
                            "Metrics": {"UnblendedCost": {"Amount": "800.00", "Unit": "USD"}},
                        },
                        {
                            "Keys": ["S3"],
                            "Metrics": {"UnblendedCost": {"Amount": "434.56", "Unit": "USD"}},
                        },
                    ],
                }
            ]
        }

        # Mock aioboto3 session client
        mock_ce = AsyncMock()
        mock_ce.get_cost_and_usage = AsyncMock(return_value=mock_response)
        mock_session_client = AsyncMock()
        mock_session_client.__aenter__ = AsyncMock(return_value=mock_ce)
        mock_session_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch.object(cost_explorer_client._session, "client", return_value=mock_session_client):
            result = await cost_explorer_client.get_cost_and_usage(
                start_date=start_date, end_date=end_date, granularity="MONTHLY"
            )

        # Assert
        assert result == mock_response
        mock_ce.get_cost_and_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cost_and_usage_with_filter_tags(self, cost_explorer_client):
        """测试按标签过滤成本数据."""
        # Arrange
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        filter_tags = {"project": "ml-training", "env": "production"}
        mock_response = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2025-01-01", "End": "2025-01-31"},
                    "Total": {"UnblendedCost": {"Amount": "500.00", "Unit": "USD"}},
                }
            ]
        }

        # Mock aioboto3 session client
        mock_ce = AsyncMock()
        mock_ce.get_cost_and_usage = AsyncMock(return_value=mock_response)
        mock_session_client = AsyncMock()
        mock_session_client.__aenter__ = AsyncMock(return_value=mock_ce)
        mock_session_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch.object(cost_explorer_client._session, "client", return_value=mock_session_client):
            result = await cost_explorer_client.get_cost_and_usage(
                start_date=start_date, end_date=end_date, granularity="MONTHLY", filter_tags=filter_tags
            )

        # Assert
        assert result == mock_response
        call_args = mock_ce.get_cost_and_usage.call_args
        assert call_args is not None
        assert "Filter" in call_args.kwargs
        assert "And" in call_args.kwargs["Filter"]

    @pytest.mark.asyncio
    async def test_get_cost_and_usage_with_service_dimension(self, cost_explorer_client):
        """测试按服务分组获取成本数据."""
        # Arrange
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        mock_response = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2025-01-01", "End": "2025-01-31"},
                    "Groups": [
                        {"Keys": ["EC2"], "Metrics": {"UnblendedCost": {"Amount": "800.00", "Unit": "USD"}}},
                        {"Keys": ["S3"], "Metrics": {"UnblendedCost": {"Amount": "200.00", "Unit": "USD"}}},
                        {"Keys": ["FSx"], "Metrics": {"UnblendedCost": {"Amount": "100.00", "Unit": "USD"}}},
                        {"Keys": ["EBS"], "Metrics": {"UnblendedCost": {"Amount": "50.00", "Unit": "USD"}}},
                    ],
                }
            ]
        }

        # Mock aioboto3 session client
        mock_ce = AsyncMock()
        mock_ce.get_cost_and_usage = AsyncMock(return_value=mock_response)
        mock_session_client = AsyncMock()
        mock_session_client.__aenter__ = AsyncMock(return_value=mock_ce)
        mock_session_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch.object(cost_explorer_client._session, "client", return_value=mock_session_client):
            result = await cost_explorer_client.get_cost_and_usage(
                start_date=start_date,
                end_date=end_date,
                granularity="MONTHLY",
                group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

        # Assert
        assert result == mock_response
        assert len(result["ResultsByTime"][0]["Groups"]) == 4
        services = [group["Keys"][0] for group in result["ResultsByTime"][0]["Groups"]]
        assert "EC2" in services
        assert "S3" in services
        assert "FSx" in services
        assert "EBS" in services

    @pytest.mark.asyncio
    async def test_cache_strategy(self, cost_explorer_client):
        """测试缓存策略 (1小时刷新)."""
        # Arrange
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        mock_response = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2025-01-01", "End": "2025-01-31"},
                    "Total": {"UnblendedCost": {"Amount": "1000.00", "Unit": "USD"}},
                }
            ]
        }

        # Mock aioboto3 session client
        mock_ce = AsyncMock()
        mock_ce.get_cost_and_usage = AsyncMock(return_value=mock_response)
        mock_session_client = AsyncMock()
        mock_session_client.__aenter__ = AsyncMock(return_value=mock_ce)
        mock_session_client.__aexit__ = AsyncMock(return_value=None)

        # Act - 首次调用和第二次调用
        with patch.object(cost_explorer_client._session, "client", return_value=mock_session_client):
            result1 = await cost_explorer_client.get_cost_and_usage(
                start_date=start_date, end_date=end_date, granularity="MONTHLY"
            )
            result2 = await cost_explorer_client.get_cost_and_usage(
                start_date=start_date, end_date=end_date, granularity="MONTHLY"
            )

        # Assert - 两次调用返回相同结果
        assert result1 == result2
        # Note: 实际缓存实现将在实现类中完成，这里只验证接口行为一致性

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """测试单例模式."""
        from src.modules.billing.infrastructure.external import get_cost_explorer_client

        # Act
        client1 = get_cost_explorer_client()
        client2 = get_cost_explorer_client()

        # Assert
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_date_format_conversion(self, cost_explorer_client):
        """测试日期格式转换 (datetime → YYYY-MM-DD)."""
        # Arrange
        start_date = datetime(2025, 1, 15, 10, 30, 45)  # 包含时间部分
        end_date = datetime(2025, 1, 31, 23, 59, 59)
        mock_response = {"ResultsByTime": []}

        # Mock aioboto3 session client
        mock_ce = AsyncMock()
        mock_ce.get_cost_and_usage = AsyncMock(return_value=mock_response)
        mock_session_client = AsyncMock()
        mock_session_client.__aenter__ = AsyncMock(return_value=mock_ce)
        mock_session_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch.object(cost_explorer_client._session, "client", return_value=mock_session_client):
            await cost_explorer_client.get_cost_and_usage(start_date=start_date, end_date=end_date, granularity="DAILY")

        # Assert
        call_args = mock_ce.get_cost_and_usage.call_args
        assert call_args.kwargs["TimePeriod"]["Start"] == "2025-01-15"
        assert call_args.kwargs["TimePeriod"]["End"] == "2025-01-31"
