"""Fixtures for spaces module unit tests."""

import pytest

from src.modules.spaces.domain.entities.space import Space
from src.modules.spaces.domain.value_objects import SpaceInstanceType, SpaceType


@pytest.fixture
def sample_space() -> Space:
    """Create a sample space for testing."""
    return Space(
        id="550e8400-e29b-41d4-a716-446655440000",
        space_name="test-space",
        owner_id=1,
        instance_type=SpaceInstanceType.ML_G5_XLARGE,
        space_type=SpaceType.JUPYTER,
        storage_size_gb=50,
    )
