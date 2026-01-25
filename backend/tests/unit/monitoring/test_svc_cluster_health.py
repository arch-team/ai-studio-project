"""ClusterHealthService Unit Tests - TDD Red-Green-Refactor (T068)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.monitoring.application.services.cluster_health_service import (
    ClusterHealthService,
    HealthCheckResult,
)
from src.modules.monitoring.domain.entities import HyperPodCluster
from src.modules.monitoring.domain.value_objects import ClusterStatus, HealthStatus


# === Fixtures ===


@pytest.fixture
def mock_cluster_repository() -> AsyncMock:
    """Mock IHyperPodClusterRepository for testing."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_name = AsyncMock(return_value=None)
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_prometheus_service() -> AsyncMock:
    """Mock PrometheusService for testing."""
    service = AsyncMock()
    service.check_storage_alerts = AsyncMock(return_value=[])
    service.check_network_alerts = AsyncMock(return_value=[])
    return service


@pytest.fixture
def cluster_health_service(
    mock_cluster_repository: AsyncMock,
    mock_prometheus_service: AsyncMock,
) -> ClusterHealthService:
    """Create ClusterHealthService with mocked dependencies."""
    return ClusterHealthService(mock_cluster_repository, mock_prometheus_service)


@pytest.fixture
def sample_cluster() -> HyperPodCluster:
    """Create a sample HyperPodCluster entity for testing."""
    return HyperPodCluster(
        id=1,
        cluster_name="test-cluster",
        cluster_arn="arn:aws:sagemaker:us-east-1:123456789012:cluster/test-cluster",
        region="us-east-1",
        vpc_id="vpc-12345678",
        instance_groups=[{"instance_type": "ml.p4d.24xlarge", "count": 4}],
        total_nodes=4,
        available_nodes=4,
        status=ClusterStatus.ACTIVE,
        health_status=HealthStatus.HEALTHY,
        prometheus_endpoint="http://prometheus:9090",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# === Test Classes ===


class TestCheckClusterHealth:
    """Tests for cluster health check functionality."""

    @pytest.mark.asyncio
    async def test_check_cluster_health_returns_healthy(
        self,
        cluster_health_service: ClusterHealthService,
        mock_cluster_repository: AsyncMock,
        mock_prometheus_service: AsyncMock,
        sample_cluster: HyperPodCluster,
    ) -> None:
        """Test health check returns healthy when no alerts."""
        # Arrange
        mock_cluster_repository.get_by_id.return_value = sample_cluster
        mock_prometheus_service.check_storage_alerts.return_value = []
        mock_prometheus_service.check_network_alerts.return_value = []

        # Act
        result = await cluster_health_service.check_health(cluster_id=1)

        # Assert
        assert result is not None
        assert isinstance(result, HealthCheckResult)
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_cluster_health_returns_degraded(
        self,
        cluster_health_service: ClusterHealthService,
        mock_cluster_repository: AsyncMock,
        mock_prometheus_service: AsyncMock,
        sample_cluster: HyperPodCluster,
    ) -> None:
        """Test health check returns degraded when warning alerts exist."""
        # Arrange
        from src.modules.monitoring.application.services.prometheus_service import StorageAlert

        mock_cluster_repository.get_by_id.return_value = sample_cluster
        mock_prometheus_service.check_storage_alerts.return_value = [
            StorageAlert(
                severity="warning",
                message="Storage at 80%",
                mountpoint="/fsx",
                usage_percent=80.0,
            )
        ]
        mock_prometheus_service.check_network_alerts.return_value = []

        # Act
        result = await cluster_health_service.check_health(cluster_id=1)

        # Assert
        assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_check_cluster_health_returns_unhealthy(
        self,
        cluster_health_service: ClusterHealthService,
        mock_cluster_repository: AsyncMock,
        mock_prometheus_service: AsyncMock,
        sample_cluster: HyperPodCluster,
    ) -> None:
        """Test health check returns unhealthy when critical alerts exist."""
        # Arrange
        from src.modules.monitoring.application.services.prometheus_service import StorageAlert

        mock_cluster_repository.get_by_id.return_value = sample_cluster
        mock_prometheus_service.check_storage_alerts.return_value = [
            StorageAlert(
                severity="critical",
                message="Storage at 95%",
                mountpoint="/fsx",
                usage_percent=95.0,
            )
        ]
        mock_prometheus_service.check_network_alerts.return_value = []

        # Act
        result = await cluster_health_service.check_health(cluster_id=1)

        # Assert
        assert result.status == HealthStatus.UNHEALTHY


class TestSyncClusterStatus:
    """Tests for cluster status synchronization."""

    @pytest.mark.asyncio
    async def test_sync_cluster_status_updates_database(
        self,
        cluster_health_service: ClusterHealthService,
        mock_cluster_repository: AsyncMock,
        mock_prometheus_service: AsyncMock,
        sample_cluster: HyperPodCluster,
    ) -> None:
        """Test sync updates cluster status in database."""
        # Arrange
        mock_cluster_repository.get_by_id.return_value = sample_cluster
        mock_prometheus_service.check_storage_alerts.return_value = []
        mock_prometheus_service.check_network_alerts.return_value = []

        # Act
        await cluster_health_service.sync_cluster_status(cluster_id=1)

        # Assert
        mock_cluster_repository.update.assert_called_once()


class TestHealthCheckClusterNotFound:
    """Tests for cluster not found scenarios."""

    @pytest.mark.asyncio
    async def test_health_check_cluster_not_found(
        self,
        cluster_health_service: ClusterHealthService,
        mock_cluster_repository: AsyncMock,
    ) -> None:
        """Test health check raises error when cluster not found."""
        # Arrange
        mock_cluster_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(Exception):
            await cluster_health_service.check_health(cluster_id=999)
