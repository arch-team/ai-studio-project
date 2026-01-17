"""Unit tests for EnumMapper."""

import pytest

from src.shared.utils.mapping import EnumMapper
from src.modules.training.domain.entities.training_job import JobStatus, JobPriority
from src.modules.training.api.schemas import JobStatusEnum, JobPriorityEnum


class TestEnumMapperToApi:
    """Tests for EnumMapper.to_api()."""

    def test_converts_uppercase_to_lowercase(self):
        """Domain RUNNING → API running."""
        result = EnumMapper.to_api(JobStatus.RUNNING, JobStatusEnum)
        assert result == JobStatusEnum.RUNNING
        assert result.value == "running"

    def test_handles_none(self):
        """None input returns None."""
        result = EnumMapper.to_api(None, JobStatusEnum)
        assert result is None

    @pytest.mark.parametrize(
        "domain_status,expected_api",
        [
            (JobStatus.SUBMITTED, JobStatusEnum.SUBMITTED),
            (JobStatus.RUNNING, JobStatusEnum.RUNNING),
            (JobStatus.PAUSED, JobStatusEnum.PAUSED),
            (JobStatus.PREEMPTED, JobStatusEnum.PREEMPTED),
            (JobStatus.COMPLETED, JobStatusEnum.COMPLETED),
            (JobStatus.FAILED, JobStatusEnum.FAILED),
        ],
    )
    def test_all_job_statuses(self, domain_status, expected_api):
        """All JobStatus values convert correctly."""
        result = EnumMapper.to_api(domain_status, JobStatusEnum)
        assert result == expected_api

    @pytest.mark.parametrize(
        "domain_priority,expected_api",
        [
            (JobPriority.HIGH, JobPriorityEnum.HIGH),
            (JobPriority.MEDIUM, JobPriorityEnum.MEDIUM),
            (JobPriority.LOW, JobPriorityEnum.LOW),
        ],
    )
    def test_all_job_priorities(self, domain_priority, expected_api):
        """All JobPriority values convert correctly."""
        result = EnumMapper.to_api(domain_priority, JobPriorityEnum)
        assert result == expected_api


class TestEnumMapperToDomain:
    """Tests for EnumMapper.to_domain()."""

    def test_converts_lowercase_to_uppercase(self):
        """API running → Domain RUNNING."""
        result = EnumMapper.to_domain(JobStatusEnum.RUNNING, JobStatus)
        assert result == JobStatus.RUNNING
        assert result.value == "RUNNING"

    def test_handles_none(self):
        """None input returns None."""
        result = EnumMapper.to_domain(None, JobStatus)
        assert result is None

    @pytest.mark.parametrize("api_status", list(JobStatusEnum))
    def test_all_api_statuses(self, api_status):
        """All JobStatusEnum values convert correctly."""
        result = EnumMapper.to_domain(api_status, JobStatus)
        assert result.value == api_status.value.upper()


class TestEnumMapperRoundTrip:
    """Tests for bidirectional conversion."""

    @pytest.mark.parametrize("domain_status", list(JobStatus))
    def test_roundtrip_domain_to_api_to_domain(self, domain_status):
        """Domain → API → Domain preserves value."""
        api_status = EnumMapper.to_api(domain_status, JobStatusEnum)
        back_to_domain = EnumMapper.to_domain(api_status, JobStatus)
        assert back_to_domain == domain_status

    @pytest.mark.parametrize("api_status", list(JobStatusEnum))
    def test_roundtrip_api_to_domain_to_api(self, api_status):
        """API → Domain → API preserves value."""
        domain_status = EnumMapper.to_domain(api_status, JobStatus)
        back_to_api = EnumMapper.to_api(domain_status, JobStatusEnum)
        assert back_to_api == api_status
