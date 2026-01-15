"""HyperPod Service - Training job lifecycle management via HyperPod SDK.

T036: HyperPodPytorchJob Integration Logic
Encapsulates HyperPod SDK operations with retry mechanism and error handling.
"""

import asyncio
from typing import Any

from src.modules.training.application.interfaces import IHyperPodClient
from src.modules.training.domain.entities.training_job import TrainingJob
from src.shared.domain.exceptions import EntityNotFoundError

# Status mapping: HyperPod SDK status -> Platform standard status
STATUS_MAPPING = {
    "Pending": "submitted",
    "Running": "running",
    "Succeeded": "completed",
    "Failed": "failed",
}


def map_hyperpod_status(hyperpod_status: str) -> str:
    """Map HyperPod status to platform standard status."""
    return STATUS_MAPPING.get(hyperpod_status, "unknown")


def build_volume_config(
    data_path: str | None = None,
    checkpoint_path: str | None = None,
) -> list[dict[str, Any]]:
    """Build FSx for Lustre volume configuration.

    Args:
        data_path: Host path for training data
        checkpoint_path: Host path for checkpoints

    Returns:
        List of volume configurations for HyperPod SDK
    """
    volumes = []

    if data_path:
        volumes.append(
            {
                "name": "training-data",
                "type": "hostPath",
                "mount_path": "/data",
                "path": data_path,
            }
        )

    if checkpoint_path:
        volumes.append(
            {
                "name": "checkpoints",
                "type": "hostPath",
                "mount_path": "/checkpoints",
                "path": checkpoint_path,
            }
        )

    return volumes


def build_job_config(job: TrainingJob) -> dict[str, Any]:
    """Build HyperPod job configuration from TrainingJob entity.

    Args:
        job: TrainingJob domain entity

    Returns:
        Job configuration dict for HyperPod SDK
    """
    config: dict[str, Any] = {
        "image_uri": job.image_uri,
        "instance_type": job.instance_type,
        "node_count": job.node_count,
        "tasks_per_node": job.tasks_per_node,
        "command": job.entrypoint_command,
    }

    if job.environment_variables:
        config["environment"] = job.environment_variables

    return config


class HyperPodServiceError(Exception):
    """HyperPod service error with retry information."""

    def __init__(
        self, message: str, retries: int = 0, original_error: Exception | None = None
    ):
        super().__init__(message)
        self.retries = retries
        self.original_error = original_error


class HyperPodService:
    """HyperPod SDK service for training job lifecycle management.

    Provides submit, pause, resume, terminate operations with retry mechanism.
    """

    def __init__(
        self,
        hyperpod_client: IHyperPodClient,
        cluster_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize HyperPod service.

        Args:
            hyperpod_client: HyperPod SDK client interface
            cluster_name: Target HyperPod cluster name
            max_retries: Maximum retry attempts for transient errors
            retry_delay: Delay between retries in seconds
        """
        self._client = hyperpod_client
        self._cluster_name = cluster_name
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def _execute_with_retry(
        self,
        operation: str,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute operation with retry on transient errors.

        Args:
            operation: Operation name for error messages
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            HyperPodServiceError: After max retries exceeded
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay)

        raise HyperPodServiceError(
            f"{operation} failed after {self._max_retries} retries: {last_error}",
            retries=self._max_retries,
            original_error=last_error,
        )

    async def submit_job(
        self,
        job_name: str,
        job_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit training job to HyperPod cluster.

        Args:
            job_name: Unique job name
            job_config: Job configuration (image, instance type, etc.)

        Returns:
            Job submission result with status

        Raises:
            HyperPodServiceError: On submission failure after retries
        """
        return await self._execute_with_retry(
            "submit_job",
            self._client.submit_training_job,
            cluster_name=self._cluster_name,
            job_name=job_name,
            job_config=job_config,
        )

    async def get_job_status(self, job_name: str) -> dict[str, Any]:
        """Get training job status.

        Args:
            job_name: Job name to query

        Returns:
            Job status information

        Raises:
            EntityNotFoundError: Job not found
        """
        try:
            return await self._client.get_training_job_status(
                cluster_name=self._cluster_name,
                job_name=job_name,
            )
        except Exception as e:
            if "not found" in str(e).lower():
                raise EntityNotFoundError(
                    entity_type="TrainingJob",
                    entity_id=job_name,
                ) from e
            raise

    async def terminate_job(self, job_name: str) -> dict[str, Any]:
        """Terminate running training job.

        Args:
            job_name: Job name to terminate

        Returns:
            Termination result

        Raises:
            HyperPodServiceError: On termination failure after retries
        """
        return await self._execute_with_retry(
            "terminate_job",
            self._client.stop_training_job,
            cluster_name=self._cluster_name,
            job_name=job_name,
        )

    async def pause_job(self, job_name: str) -> dict[str, Any]:
        """Pause training job.

        Note: HyperPod SDK does not have native pause support.
        Pause is implemented as signaling checkpoint + terminate.
        The actual checkpoint logic is handled by the training script.

        Args:
            job_name: Job name to pause

        Returns:
            Pause result with status='paused'
        """
        # Stop the job (training script should handle graceful shutdown)
        await self._client.stop_training_job(
            cluster_name=self._cluster_name,
            job_name=job_name,
        )

        return {
            "job_name": job_name,
            "status": "paused",
            "cluster_name": self._cluster_name,
        }

    async def resume_job(
        self,
        job_name: str,
        job_config: dict[str, Any],
        checkpoint_path: str | None = None,
    ) -> dict[str, Any]:
        """Resume paused training job.

        Note: Resume is implemented as resubmitting with checkpoint restore.

        Args:
            job_name: Job name to resume
            job_config: Original job configuration
            checkpoint_path: Path to checkpoint for restoration

        Returns:
            Resume result (new job submission)
        """
        config = dict(job_config)
        if checkpoint_path:
            config["checkpoint_path"] = checkpoint_path

        return await self._client.submit_training_job(
            cluster_name=self._cluster_name,
            job_name=job_name,
            job_config=config,
        )

    async def list_job_pods(self, job_name: str) -> list[dict[str, Any]]:
        """List pods for a training job.

        Args:
            job_name: Job name

        Returns:
            List of pod information
        """
        return await self._client.list_training_job_pods(
            cluster_name=self._cluster_name,
            job_name=job_name,
        )
