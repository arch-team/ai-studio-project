"""Unit tests for PodStatistics value object."""

import pytest

from src.modules.training.domain.value_objects.pod_statistics import PodStatistics


class TestPodStatisticsCreation:
    """Tests for PodStatistics value object creation."""

    def test_create_with_all_fields(self) -> None:
        """Test creating PodStatistics with all fields."""
        stats = PodStatistics(
            total_pods=8,
            running_pods=6,
            failed_pods=1,
            preemption_count=2,
        )
        assert stats.total_pods == 8
        assert stats.running_pods == 6
        assert stats.failed_pods == 1
        assert stats.preemption_count == 2

    def test_create_with_defaults(self) -> None:
        """Test creating PodStatistics with default values."""
        stats = PodStatistics()
        assert stats.total_pods is None
        assert stats.running_pods == 0
        assert stats.failed_pods == 0
        assert stats.preemption_count == 0

    def test_create_with_partial_fields(self) -> None:
        """Test creating PodStatistics with some fields."""
        stats = PodStatistics(total_pods=4, running_pods=4)
        assert stats.total_pods == 4
        assert stats.running_pods == 4
        assert stats.failed_pods == 0
        assert stats.preemption_count == 0


class TestPodStatisticsImmutability:
    """Tests for PodStatistics immutability (value object property)."""

    def test_stats_is_frozen(self) -> None:
        """Test that PodStatistics is immutable."""
        stats = PodStatistics(running_pods=4)
        with pytest.raises(AttributeError):
            stats.running_pods = 8  # type: ignore


class TestPodStatisticsEquality:
    """Tests for PodStatistics equality."""

    def test_equal_stats(self) -> None:
        """Test that two stats with same values are equal."""
        s1 = PodStatistics(total_pods=4, running_pods=4)
        s2 = PodStatistics(total_pods=4, running_pods=4)
        assert s1 == s2

    def test_unequal_stats(self) -> None:
        """Test that two stats with different values are not equal."""
        s1 = PodStatistics(running_pods=4)
        s2 = PodStatistics(running_pods=8)
        assert s1 != s2


class TestPodStatisticsBehavior:
    """Tests for PodStatistics business methods."""

    def test_healthy_ratio_all_running(self) -> None:
        """Test healthy_ratio() when all pods are running."""
        stats = PodStatistics(total_pods=8, running_pods=8)
        assert stats.healthy_ratio() == 1.0

    def test_healthy_ratio_partial_running(self) -> None:
        """Test healthy_ratio() when some pods are running."""
        stats = PodStatistics(total_pods=8, running_pods=6)
        assert stats.healthy_ratio() == 0.75

    def test_healthy_ratio_no_total(self) -> None:
        """Test healthy_ratio() when total_pods is None."""
        stats = PodStatistics(running_pods=4)
        assert stats.healthy_ratio() == 0.0

    def test_healthy_ratio_zero_total(self) -> None:
        """Test healthy_ratio() when total_pods is 0."""
        stats = PodStatistics(total_pods=0)
        assert stats.healthy_ratio() == 0.0

    def test_has_failures_true(self) -> None:
        """Test has_failures() returns True when failed_pods > 0."""
        stats = PodStatistics(failed_pods=1)
        assert stats.has_failures()

    def test_has_failures_false(self) -> None:
        """Test has_failures() returns False when failed_pods == 0."""
        stats = PodStatistics(failed_pods=0)
        assert not stats.has_failures()

    def test_was_preempted_true(self) -> None:
        """Test was_preempted() returns True when preemption_count > 0."""
        stats = PodStatistics(preemption_count=1)
        assert stats.was_preempted()

    def test_was_preempted_false(self) -> None:
        """Test was_preempted() returns False when preemption_count == 0."""
        stats = PodStatistics(preemption_count=0)
        assert not stats.was_preempted()

    def test_increment_preemption(self) -> None:
        """Test increment_preemption() returns new instance with incremented count."""
        stats = PodStatistics(preemption_count=2)
        new_stats = stats.increment_preemption()
        assert new_stats.preemption_count == 3
        assert stats.preemption_count == 2  # Original unchanged
