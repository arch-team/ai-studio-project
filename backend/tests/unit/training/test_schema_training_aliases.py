"""训练任务 Schema 前端契约别名测试.

前端发送 entry_point/gpu_per_node，后端契约为 entrypoint_command/tasks_per_node。
请求 schema 负责归一化别名，响应 schema 负责反向映射。
"""

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from src.modules.training.api.schemas.requests import CreateTrainingJobRequest
from src.modules.training.api.schemas.responses import (
    TrainingJobDetail,
    TrainingJobSummary,
)
from src.modules.training.domain.entities import TrainingJob
from src.modules.training.domain.value_objects import JobPriority, JobStatus


@pytest.fixture
def base_request_data() -> dict[str, Any]:
    """最小创建请求数据（不含 entrypoint 相关字段）."""
    return {
        "job_name": "alias-test-job",
        "image_uri": "123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
        "instance_type": "ml.g5.xlarge",
        "node_count": 1,
    }


@pytest.fixture
def sample_job() -> TrainingJob:
    """带有 tasks_per_node/max_epochs/entrypoint_command 的任务实体."""
    return TrainingJob(
        id=1,
        job_name="alias-test-job",
        owner_id=1,
        image_uri="img:v1",
        instance_type="ml.g5.xlarge",
        entrypoint_command=["python", "/opt/ml/code/train.py"],
        node_count=2,
        tasks_per_node=4,
        max_epochs=10,
        status=JobStatus.RUNNING,
        priority=JobPriority.HIGH,
        created_at=datetime(2026, 6, 12),
        updated_at=datetime(2026, 6, 12),
    )


class TestCreateRequestAliases:
    """CreateTrainingJobRequest 别名归一化."""

    def test_entry_point_converted_to_entrypoint_command(self, base_request_data: dict[str, Any]) -> None:
        request = CreateTrainingJobRequest(**base_request_data, entry_point="/opt/ml/code/train.py")
        assert request.entrypoint_command == ["python", "/opt/ml/code/train.py"]

    def test_gpu_per_node_converted_to_tasks_per_node(self, base_request_data: dict[str, Any]) -> None:
        request = CreateTrainingJobRequest(
            **base_request_data,
            entry_point="train.py",
            gpu_per_node=4,
        )
        assert request.tasks_per_node == 4

    def test_explicit_entrypoint_command_takes_precedence(self, base_request_data: dict[str, Any]) -> None:
        request = CreateTrainingJobRequest(
            **base_request_data,
            entrypoint_command=["torchrun", "train.py"],
            entry_point="ignored.py",
        )
        assert request.entrypoint_command == ["torchrun", "train.py"]

    def test_explicit_tasks_per_node_takes_precedence(self, base_request_data: dict[str, Any]) -> None:
        request = CreateTrainingJobRequest(
            **base_request_data,
            entry_point="train.py",
            tasks_per_node=8,
            gpu_per_node=2,
        )
        assert request.tasks_per_node == 8

    def test_missing_both_entrypoint_fields_raises_validation_error(self, base_request_data: dict[str, Any]) -> None:
        with pytest.raises(ValidationError, match="entrypoint_command or entry_point"):
            CreateTrainingJobRequest(**base_request_data)

    def test_tasks_per_node_defaults_to_one(self, base_request_data: dict[str, Any]) -> None:
        request = CreateTrainingJobRequest(**base_request_data, entry_point="train.py")
        assert request.tasks_per_node == 1


class TestResponseAliases:
    """TrainingJobSummary/Detail 响应别名映射."""

    def test_summary_maps_gpu_per_node_from_tasks_per_node(self, sample_job: TrainingJob) -> None:
        summary = TrainingJobSummary.from_entity(sample_job)
        assert summary.gpu_per_node == 4

    def test_summary_maps_total_epochs_from_max_epochs(self, sample_job: TrainingJob) -> None:
        summary = TrainingJobSummary.from_entity(sample_job)
        assert summary.total_epochs == 10

    def test_detail_maps_entry_point_from_entrypoint_command(self, sample_job: TrainingJob) -> None:
        detail = TrainingJobDetail.from_entity(sample_job)
        assert detail.entry_point == "python /opt/ml/code/train.py"

    def test_detail_includes_checkpoints_count_default(self, sample_job: TrainingJob) -> None:
        detail = TrainingJobDetail.from_entity(sample_job)
        assert detail.checkpoints_count == 0

    def test_detail_includes_updated_at(self, sample_job: TrainingJob) -> None:
        detail = TrainingJobDetail.from_entity(sample_job)
        assert detail.updated_at == datetime(2026, 6, 12)
