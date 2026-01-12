"""HyperPod SDK Client wrapper.

Task: T014 - HyperPod SDK 客户端封装
使用 HyperPod Training SDK (sagemaker.hyperpod.training) 实现训练任务生命周期管理
(提交、状态查询、暂停/恢复/终止),参考 docs/hyperpod-sdk-reference.md
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from src.core.config import get_settings

# HyperPod SDK imports
# Note: These are the correct imports based on docs/hyperpod-sdk-reference.md
try:
    from sagemaker.hyperpod.training import HyperPodPytorchJob
    from sagemaker.hyperpod.training.config import VolumeConfig

    HYPERPOD_SDK_AVAILABLE = True
except ImportError:
    HYPERPOD_SDK_AVAILABLE = False
    HyperPodPytorchJob = None
    VolumeConfig = None

logger = logging.getLogger(__name__)


class TrainingJobStatus(str, Enum):
    """Training job status enum (matches Kueue/HyperPod states)."""

    SUBMITTED = "submitted"
    RUNNING = "running"
    PAUSED = "paused"
    PREEMPTED = "preempted"
    COMPLETED = "completed"
    FAILED = "failed"


class InstanceType(str, Enum):
    """Supported GPU instance types for training."""

    ML_P4D_24XLARGE = "ml.p4d.24xlarge"  # A100 40GB x 8
    ML_P5_48XLARGE = "ml.p5.48xlarge"  # H100 80GB x 8
    ML_G5_XLARGE = "ml.g5.xlarge"  # A10G x 1
    ML_G5_2XLARGE = "ml.g5.2xlarge"  # A10G x 1
    ML_G5_4XLARGE = "ml.g5.4xlarge"  # A10G x 1
    ML_G5_12XLARGE = "ml.g5.12xlarge"  # A10G x 4


# HyperPod SDK status → Platform standard status mapping
# Based on docs/hyperpod-sdk-reference.md Section "状态转换逻辑"
HYPERPOD_STATUS_MAPPING = {
    "Pending": TrainingJobStatus.SUBMITTED,
    "Running": TrainingJobStatus.RUNNING,
    "Succeeded": TrainingJobStatus.COMPLETED,
    "Failed": TrainingJobStatus.FAILED,
}


@dataclass
class VolumeMount:
    """Volume mount configuration for training jobs."""

    name: str
    mount_path: str
    type: str = "hostPath"  # hostPath or pvc
    path: Optional[str] = None  # For hostPath type
    claim_name: Optional[str] = None  # For pvc type


@dataclass
class TrainingConfig:
    """Training job configuration."""

    job_name: str
    instance_type: str
    node_count: int
    container_image: str
    command: list[str]  # Command to run (e.g., ["torchrun", "--nproc_per_node=8", "train.py"])
    tasks_per_node: int = 1  # Number of tasks per node (typically = GPU count)
    environment: dict[str, str] = field(default_factory=dict)
    volumes: list[VolumeMount] = field(default_factory=list)
    max_runtime_seconds: int = 86400  # 24 hours default
    priority: str = "medium"  # high, medium, low


class TrainingJobInfo(BaseModel):
    """Training job information from HyperPod."""

    job_name: str
    status: TrainingJobStatus
    instance_type: str
    node_count: int
    creation_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    failure_reason: Optional[str] = None


class HyperPodClient:
    """Client for AWS SageMaker HyperPod operations.

    This client wraps the HyperPod Training SDK (sagemaker.hyperpod.training)
    for training job lifecycle management.

    Based on: docs/hyperpod-sdk-reference.md
    """

    def __init__(self):
        """Initialize HyperPod client with configuration."""
        self.settings = get_settings()

        if not HYPERPOD_SDK_AVAILABLE:
            logger.warning(
                "HyperPod SDK not available. Install with: pip install sagemaker-hyperpod"
            )

    def _map_status(self, hyperpod_status: str) -> TrainingJobStatus:
        """Map HyperPod SDK status to platform standard status.

        Args:
            hyperpod_status: Status from HyperPod SDK (Pending/Running/Succeeded/Failed)

        Returns:
            Platform standard TrainingJobStatus
        """
        return HYPERPOD_STATUS_MAPPING.get(hyperpod_status, TrainingJobStatus.SUBMITTED)

    def _build_volume_configs(self, volumes: list[VolumeMount]) -> list:
        """Build VolumeConfig objects from VolumeMount dataclasses.

        Args:
            volumes: List of VolumeMount configurations

        Returns:
            List of VolumeConfig objects for HyperPod SDK
        """
        if not HYPERPOD_SDK_AVAILABLE or VolumeConfig is None:
            return []

        volume_configs = []
        for vol in volumes:
            if vol.type == "hostPath" and vol.path:
                volume_configs.append(
                    VolumeConfig(
                        name=vol.name,
                        type="hostPath",
                        mount_path=vol.mount_path,
                        path=vol.path,
                    )
                )
            elif vol.type == "pvc" and vol.claim_name:
                volume_configs.append(
                    VolumeConfig(
                        name=vol.name,
                        type="pvc",
                        mount_path=vol.mount_path,
                        claim_name=vol.claim_name,
                    )
                )

        return volume_configs

    async def create_training_job(self, config: TrainingConfig) -> TrainingJobInfo:
        """Submit a new training job to HyperPod.

        Uses HyperPodPytorchJob.create() from the HyperPod SDK.

        Args:
            config: Training job configuration

        Returns:
            TrainingJobInfo with job details

        Raises:
            RuntimeError: If SDK not available or job creation fails
        """
        if not HYPERPOD_SDK_AVAILABLE or HyperPodPytorchJob is None:
            raise RuntimeError(
                "HyperPod SDK not available. Install with: pip install sagemaker-hyperpod"
            )

        try:
            # Build volume configurations
            volume_configs = self._build_volume_configs(config.volumes)

            # Create training job using HyperPod SDK
            # Run synchronous SDK call in thread pool to avoid blocking
            job = await asyncio.to_thread(
                HyperPodPytorchJob.create,
                name=config.job_name,
                image_uri=config.container_image,
                instance_type=config.instance_type,
                node_count=config.node_count,
                tasks_per_node=config.tasks_per_node,
                command=config.command,
                environment=config.environment if config.environment else None,
                volumes=volume_configs if volume_configs else None,
            )

            logger.info(f"Training job created: {config.job_name}, status: {job.status}")

            return TrainingJobInfo(
                job_name=job.name,
                status=self._map_status(job.status),
                instance_type=config.instance_type,
                node_count=config.node_count,
                creation_time=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Failed to create training job: {e}")
            raise RuntimeError(f"Failed to create training job: {e}")

    async def describe_training_job(self, job_name: str) -> TrainingJobInfo:
        """Get details of a training job.

        Uses HyperPodPytorchJob.get() from the HyperPod SDK.

        Args:
            job_name: Name of the training job

        Returns:
            TrainingJobInfo with current job status

        Raises:
            RuntimeError: If SDK not available or job lookup fails
        """
        if not HYPERPOD_SDK_AVAILABLE or HyperPodPytorchJob is None:
            raise RuntimeError(
                "HyperPod SDK not available. Install with: pip install sagemaker-hyperpod"
            )

        try:
            # Get job using HyperPod SDK
            job = await asyncio.to_thread(HyperPodPytorchJob.get, name=job_name)

            return TrainingJobInfo(
                job_name=job.name,
                status=self._map_status(job.status),
                instance_type=getattr(job, "instance_type", ""),
                node_count=getattr(job, "node_count", 1),
                start_time=getattr(job, "start_time", None),
                end_time=getattr(job, "end_time", None),
            )

        except Exception as e:
            logger.error(f"Failed to describe training job: {e}")
            raise RuntimeError(f"Training job not found or error: {job_name} - {e}")

    async def delete_training_job(self, job_name: str) -> TrainingJobInfo:
        """Delete (stop) a training job.

        Uses HyperPodPytorchJob.get().delete() from the HyperPod SDK.

        Args:
            job_name: Name of the training job

        Returns:
            TrainingJobInfo with updated status

        Raises:
            RuntimeError: If SDK not available or delete operation fails
        """
        if not HYPERPOD_SDK_AVAILABLE or HyperPodPytorchJob is None:
            raise RuntimeError(
                "HyperPod SDK not available. Install with: pip install sagemaker-hyperpod"
            )

        try:
            # Get job and delete using HyperPod SDK
            job = await asyncio.to_thread(HyperPodPytorchJob.get, name=job_name)
            await asyncio.to_thread(job.delete)

            logger.info(f"Training job deleted: {job_name}")

            return TrainingJobInfo(
                job_name=job_name,
                status=TrainingJobStatus.FAILED,  # Deleted jobs are marked as failed
                instance_type="",
                node_count=0,
            )

        except Exception as e:
            logger.error(f"Failed to delete training job: {e}")
            raise RuntimeError(f"Failed to delete training job: {e}")

    async def get_training_job_logs(
        self,
        job_name: str,
        tail: int = 100,
    ) -> str:
        """Get logs for a training job.

        Uses HyperPodPytorchJob.get().logs() from the HyperPod SDK.

        Args:
            job_name: Name of the training job
            tail: Number of log lines to retrieve (default 100)

        Returns:
            Log content as string
        """
        if not HYPERPOD_SDK_AVAILABLE or HyperPodPytorchJob is None:
            return "HyperPod SDK not available"

        try:
            # Get job and retrieve logs
            job = await asyncio.to_thread(HyperPodPytorchJob.get, name=job_name)
            logs = await asyncio.to_thread(job.logs, tail=tail)

            return logs

        except Exception as e:
            logger.warning(f"Failed to get training job logs: {e}")
            return f"Error retrieving logs: {e}"

    async def list_pods(self, job_name: str) -> list[dict[str, Any]]:
        """List pods for a training job.

        Uses HyperPodPytorchJob.get().list_pods() from the HyperPod SDK.

        Args:
            job_name: Name of the training job

        Returns:
            List of pod information dictionaries
        """
        if not HYPERPOD_SDK_AVAILABLE or HyperPodPytorchJob is None:
            return []

        try:
            job = await asyncio.to_thread(HyperPodPytorchJob.get, name=job_name)
            pods = await asyncio.to_thread(job.list_pods)

            return pods

        except Exception as e:
            logger.warning(f"Failed to list pods: {e}")
            return []


# Singleton instance
_hyperpod_client: Optional[HyperPodClient] = None


def get_hyperpod_client() -> HyperPodClient:
    """Get or create HyperPod client singleton.

    Returns:
        HyperPodClient instance
    """
    global _hyperpod_client
    if _hyperpod_client is None:
        _hyperpod_client = HyperPodClient()
    return _hyperpod_client
