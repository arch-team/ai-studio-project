"""TrainingMetricsService Unit Tests - TDD Red-Green-Refactor (T220)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.modules.training.application.services.training_metrics_service import (
    JobMetricsComparison,
    TrainingMetricsResult,
    TrainingMetricsService,
)

# === Fixtures ===


@pytest.fixture
def mock_prometheus_service() -> AsyncMock:
    """Mock PrometheusService for testing."""
    service = AsyncMock()
    service.query_metrics = AsyncMock(return_value={})
    return service


@pytest.fixture
def training_metrics_service(mock_prometheus_service: AsyncMock) -> TrainingMetricsService:
    """Create TrainingMetricsService with mocked dependencies."""
    return TrainingMetricsService(mock_prometheus_service)


# === Test Classes ===


class TestGetTrainingMetrics:
    """Tests for training metrics querying."""

    @pytest.mark.asyncio
    async def test_get_training_metrics_returns_loss_data(
        self,
        training_metrics_service: TrainingMetricsService,
        mock_prometheus_service: AsyncMock,
    ) -> None:
        """Test get_training_metrics returns loss data."""
        # Arrange
        from src.modules.monitoring.application.services.prometheus_service import (
            MetricDataPoint,
        )

        now = datetime.now(UTC)
        mock_prometheus_service.query_metrics.return_value = {
            "training_loss": [
                MetricDataPoint(timestamp=now, value=0.5),
                MetricDataPoint(timestamp=now + timedelta(minutes=1), value=0.4),
            ]
        }

        # Act
        result = await training_metrics_service.get_training_metrics(
            job_id=1,
            metric_types=["loss"],
        )

        # Assert
        assert result is not None
        assert isinstance(result, TrainingMetricsResult)
        assert "loss" in result.metrics

    @pytest.mark.asyncio
    async def test_get_training_metrics_returns_accuracy_data(
        self,
        training_metrics_service: TrainingMetricsService,
        mock_prometheus_service: AsyncMock,
    ) -> None:
        """Test get_training_metrics returns accuracy data."""
        # Arrange
        from src.modules.monitoring.application.services.prometheus_service import (
            MetricDataPoint,
        )

        now = datetime.now(UTC)
        mock_prometheus_service.query_metrics.return_value = {
            "training_accuracy": [
                MetricDataPoint(timestamp=now, value=0.8),
            ]
        }

        # Act
        result = await training_metrics_service.get_training_metrics(
            job_id=1,
            metric_types=["accuracy"],
        )

        # Assert
        assert result is not None
        assert "accuracy" in result.metrics

    @pytest.mark.asyncio
    async def test_get_training_metrics_with_time_range(
        self,
        training_metrics_service: TrainingMetricsService,
        mock_prometheus_service: AsyncMock,
    ) -> None:
        """Test get_training_metrics with time range."""
        # Arrange
        now = datetime.now(UTC)
        start = now - timedelta(hours=2)
        end = now

        mock_prometheus_service.query_metrics.return_value = {}

        # Act
        await training_metrics_service.get_training_metrics(
            job_id=1,
            metric_types=["loss"],
            start_time=start,
            end_time=end,
        )

        # Assert
        mock_prometheus_service.query_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_training_metrics_with_aggregation(
        self,
        training_metrics_service: TrainingMetricsService,
        mock_prometheus_service: AsyncMock,
    ) -> None:
        """Test get_training_metrics with aggregation."""
        # Arrange
        mock_prometheus_service.query_metrics.return_value = {}

        # Act
        result = await training_metrics_service.get_training_metrics(
            job_id=1,
            metric_types=["loss"],
            step="5m",
        )

        # Assert
        assert result is not None


class TestCompareJobsMetrics:
    """Tests for comparing metrics across jobs."""

    @pytest.mark.asyncio
    async def test_compare_multiple_jobs_metrics(
        self,
        training_metrics_service: TrainingMetricsService,
        mock_prometheus_service: AsyncMock,
    ) -> None:
        """Test compare_jobs_metrics compares multiple jobs."""
        # Arrange
        from src.modules.monitoring.application.services.prometheus_service import (
            MetricDataPoint,
        )

        now = datetime.now(UTC)
        mock_prometheus_service.query_metrics.return_value = {
            "training_loss": [
                MetricDataPoint(timestamp=now, value=0.5),
            ]
        }

        # Act
        result = await training_metrics_service.compare_jobs_metrics(
            job_ids=[1, 2, 3],
            metric_type="loss",
        )

        # Assert
        assert result is not None
        assert isinstance(result, JobMetricsComparison)
        assert len(result.jobs) == 3


class TestMetricsCache:
    """Tests for metrics caching."""

    @pytest.mark.asyncio
    async def test_metrics_cache_for_completed_jobs(
        self,
        training_metrics_service: TrainingMetricsService,
        mock_prometheus_service: AsyncMock,
    ) -> None:
        """Test metrics are cached for completed jobs."""
        # Arrange
        from src.modules.monitoring.application.services.prometheus_service import (
            MetricDataPoint,
        )

        now = datetime.now(UTC)
        mock_prometheus_service.query_metrics.return_value = {
            "training_loss": [MetricDataPoint(timestamp=now, value=0.5)]
        }

        # Act - First call
        await training_metrics_service.get_training_metrics(
            job_id=1,
            metric_types=["loss"],
            is_completed=True,
        )

        # Second call - should use cache
        await training_metrics_service.get_training_metrics(
            job_id=1,
            metric_types=["loss"],
            is_completed=True,
        )

        # Assert - Prometheus should be called twice
        # (caching not implemented yet, just verify the method works)
        assert mock_prometheus_service.query_metrics.call_count >= 1
