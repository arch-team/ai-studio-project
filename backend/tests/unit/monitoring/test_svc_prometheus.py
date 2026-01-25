"""PrometheusService Unit Tests - TDD Red-Green-Refactor (T062)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.modules.monitoring.application.services.prometheus_service import (
    PrometheusService,
    StorageCapacityMetrics,
)
from src.modules.monitoring.infrastructure.external.prometheus_client import (
    IPrometheusClient,
)

# === Fixtures ===


@pytest.fixture
def mock_prometheus_client() -> AsyncMock:
    """Mock IPrometheusClient for testing."""
    client = AsyncMock(spec=IPrometheusClient)
    client.query_instant = AsyncMock(return_value=[])
    client.query_range = AsyncMock(return_value=[])
    return client


@pytest.fixture
def prometheus_service(mock_prometheus_client: AsyncMock) -> PrometheusService:
    """Create PrometheusService with mocked client."""
    return PrometheusService(mock_prometheus_client)


# === Test Classes ===


class TestQueryMetrics:
    """Tests for basic metric querying."""

    @pytest.mark.asyncio
    async def test_query_metrics_returns_data_points(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test query_metrics returns data points."""
        # Arrange
        now = datetime.now(UTC)
        mock_prometheus_client.query_range.return_value = [
            {"metric": {"__name__": "test_metric"}, "values": [[now.timestamp(), "42.5"]]}
        ]

        # Act
        result = await prometheus_service.query_metrics(
            metric_names=["test_metric"],
            start_time=now - timedelta(hours=1),
            end_time=now,
        )

        # Assert
        assert "test_metric" in result
        assert len(result["test_metric"]) > 0

    @pytest.mark.asyncio
    async def test_query_metrics_with_time_range(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test query_metrics respects time range."""
        # Arrange
        now = datetime.now(UTC)
        start = now - timedelta(hours=2)
        end = now

        # Act
        await prometheus_service.query_metrics(
            metric_names=["cpu_usage"],
            start_time=start,
            end_time=end,
        )

        # Assert
        mock_prometheus_client.query_range.assert_called()
        call_args = mock_prometheus_client.query_range.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_query_metrics_handles_prometheus_error(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test query_metrics handles Prometheus errors gracefully."""
        # Arrange
        mock_prometheus_client.query_range.side_effect = Exception("Prometheus error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await prometheus_service.query_metrics(
                metric_names=["test"],
                start_time=datetime.now(UTC) - timedelta(hours=1),
                end_time=datetime.now(UTC),
            )
        assert "Prometheus" in str(exc_info.value) or "error" in str(exc_info.value).lower()


class TestStorageCapacityMonitoring:
    """Tests for storage capacity monitoring (FR-020)."""

    @pytest.mark.asyncio
    async def test_get_storage_capacity_metrics(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test get_storage_capacity_metrics returns metrics."""
        # Arrange
        mock_prometheus_client.query_instant.return_value = [
            {"metric": {"mountpoint": "/fsx"}, "value": [datetime.now(UTC).timestamp(), "80"]}
        ]

        # Act
        result = await prometheus_service.get_storage_capacity_metrics()

        # Assert
        assert result is not None
        assert isinstance(result, StorageCapacityMetrics)

    @pytest.mark.asyncio
    async def test_storage_capacity_alerts_at_80_percent(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test alert generated at 80% storage usage."""
        # Arrange
        mock_prometheus_client.query_instant.return_value = [
            {"metric": {"mountpoint": "/fsx"}, "value": [datetime.now(UTC).timestamp(), "80"]}
        ]

        # Act
        alerts = await prometheus_service.check_storage_alerts()

        # Assert
        assert len(alerts) > 0
        assert any(a.severity == "warning" for a in alerts)

    @pytest.mark.asyncio
    async def test_storage_capacity_alerts_at_90_percent(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test alert generated at 90% storage usage (high severity)."""
        # Arrange
        mock_prometheus_client.query_instant.return_value = [
            {"metric": {"mountpoint": "/fsx"}, "value": [datetime.now(UTC).timestamp(), "90"]}
        ]

        # Act
        alerts = await prometheus_service.check_storage_alerts()

        # Assert
        assert len(alerts) > 0
        assert any(a.severity == "high" for a in alerts)

    @pytest.mark.asyncio
    async def test_storage_capacity_alerts_at_95_percent(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test alert generated at 95% storage usage (critical severity)."""
        # Arrange
        mock_prometheus_client.query_instant.return_value = [
            {"metric": {"mountpoint": "/fsx"}, "value": [datetime.now(UTC).timestamp(), "95"]}
        ]

        # Act
        alerts = await prometheus_service.check_storage_alerts()

        # Assert
        assert len(alerts) > 0
        assert any(a.severity == "critical" for a in alerts)


class TestNetworkMonitoring:
    """Tests for network monitoring (FR-021)."""

    @pytest.mark.asyncio
    async def test_get_network_metrics(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test get_network_metrics returns metrics."""
        # Arrange
        mock_prometheus_client.query_instant.return_value = [
            {"metric": {"interface": "eth0"}, "value": [datetime.now(UTC).timestamp(), "5.0"]}
        ]

        # Act
        result = await prometheus_service.get_network_metrics()

        # Assert
        assert result is not None
        assert hasattr(result, "latency_ms")

    @pytest.mark.asyncio
    async def test_network_latency_alerts(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test alert generated for high network latency."""
        # Arrange - high latency
        mock_prometheus_client.query_instant.return_value = [
            {"metric": {"interface": "eth0"}, "value": [datetime.now(UTC).timestamp(), "100"]}
        ]

        # Act
        alerts = await prometheus_service.check_network_alerts()

        # Assert
        assert len(alerts) > 0


class TestGPUMetrics:
    """Tests for GPU metrics querying."""

    @pytest.mark.asyncio
    async def test_get_gpu_utilization(
        self,
        prometheus_service: PrometheusService,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test get_gpu_utilization returns data."""
        # Arrange
        now = datetime.now(UTC)
        mock_prometheus_client.query_range.return_value = [
            {
                "metric": {"gpu": "0", "instance": "node-1"},
                "values": [[now.timestamp(), "75.5"]],
            }
        ]

        # Act
        result = await prometheus_service.get_gpu_utilization(
            cluster_name="test-cluster",
            start_time=now - timedelta(hours=1),
            end_time=now,
        )

        # Assert
        assert result is not None
        assert len(result) > 0
