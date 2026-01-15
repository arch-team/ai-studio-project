"""Unit tests for TrainingMetrics value object."""

from decimal import Decimal

import pytest

from src.modules.training.domain.value_objects.training_metrics import TrainingMetrics


class TestTrainingMetricsCreation:
    """Tests for TrainingMetrics value object creation."""

    def test_create_with_all_fields(self) -> None:
        """Test creating TrainingMetrics with all fields."""
        metrics = TrainingMetrics(
            current_epoch=10,
            current_step=1000,
            latest_loss=Decimal("0.0123"),
            latest_accuracy=Decimal("0.9876"),
        )
        assert metrics.current_epoch == 10
        assert metrics.current_step == 1000
        assert metrics.latest_loss == Decimal("0.0123")
        assert metrics.latest_accuracy == Decimal("0.9876")

    def test_create_with_defaults(self) -> None:
        """Test creating TrainingMetrics with default values."""
        metrics = TrainingMetrics()
        assert metrics.current_epoch is None
        assert metrics.current_step is None
        assert metrics.latest_loss is None
        assert metrics.latest_accuracy is None

    def test_create_with_partial_fields(self) -> None:
        """Test creating TrainingMetrics with some fields."""
        metrics = TrainingMetrics(current_epoch=5, latest_loss=Decimal("0.05"))
        assert metrics.current_epoch == 5
        assert metrics.current_step is None
        assert metrics.latest_loss == Decimal("0.05")
        assert metrics.latest_accuracy is None


class TestTrainingMetricsImmutability:
    """Tests for TrainingMetrics immutability (value object property)."""

    def test_metrics_is_frozen(self) -> None:
        """Test that TrainingMetrics is immutable."""
        metrics = TrainingMetrics(current_epoch=10)
        with pytest.raises(AttributeError):
            metrics.current_epoch = 20  # type: ignore


class TestTrainingMetricsEquality:
    """Tests for TrainingMetrics equality."""

    def test_equal_metrics(self) -> None:
        """Test that two metrics with same values are equal."""
        m1 = TrainingMetrics(current_epoch=10, latest_loss=Decimal("0.01"))
        m2 = TrainingMetrics(current_epoch=10, latest_loss=Decimal("0.01"))
        assert m1 == m2

    def test_unequal_metrics(self) -> None:
        """Test that two metrics with different values are not equal."""
        m1 = TrainingMetrics(current_epoch=10)
        m2 = TrainingMetrics(current_epoch=20)
        assert m1 != m2


class TestTrainingMetricsBehavior:
    """Tests for TrainingMetrics business methods."""

    def test_has_progress_with_epoch(self) -> None:
        """Test has_progress() returns True when epoch is set."""
        metrics = TrainingMetrics(current_epoch=1)
        assert metrics.has_progress()

    def test_has_progress_with_step(self) -> None:
        """Test has_progress() returns True when step is set."""
        metrics = TrainingMetrics(current_step=100)
        assert metrics.has_progress()

    def test_has_progress_empty(self) -> None:
        """Test has_progress() returns False when no progress."""
        metrics = TrainingMetrics()
        assert not metrics.has_progress()

    def test_is_improving_with_better_loss(self) -> None:
        """Test is_improving() with better loss."""
        current = TrainingMetrics(latest_loss=Decimal("0.01"))
        previous = TrainingMetrics(latest_loss=Decimal("0.05"))
        assert current.is_improving(previous)

    def test_is_improving_with_worse_loss(self) -> None:
        """Test is_improving() with worse loss."""
        current = TrainingMetrics(latest_loss=Decimal("0.05"))
        previous = TrainingMetrics(latest_loss=Decimal("0.01"))
        assert not current.is_improving(previous)

    def test_is_improving_no_loss_data(self) -> None:
        """Test is_improving() returns False when no loss data."""
        current = TrainingMetrics()
        previous = TrainingMetrics()
        assert not current.is_improving(previous)
