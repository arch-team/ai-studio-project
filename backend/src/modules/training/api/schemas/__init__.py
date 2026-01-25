"""Training API schemas."""

from .requests import (
    CreateTrainingJobRequest,
    UpdateTrainingJobRequest,
    CreateCheckpointRequest,
    CreateJobTemplateRequest,
    UpdateJobTemplateRequest,
    CreateJobFromTemplateRequest,
    TemplateVisibilityEnum as RequestTemplateVisibilityEnum,
    TrainingConfigSchema,
)
from .responses import (
    CheckpointResponse,
    CheckpointStatusEnum,
    CheckpointTypeEnum,
    JobPriorityEnum,
    JobStatusEnum,
    StorageTierEnum,
    TrainingJobDetail,
    TrainingJobListResponse,
    TrainingJobSummary,
    JobTemplateDetail,
    JobTemplateListResponse,
    JobTemplateSummary,
    TemplateVisibilityEnum,
    # Log responses
    LogEntry,
    TrainingLogsResponse,
    # Kueue debug responses
    KueueDebugResponse,
    KueueWorkloadStatus,
    KueueCondition,
    KueueAdmission,
    KueueQuotaUsage,
    QueueInfo,
    PreemptionEvent,
)

__all__ = [
    # Enums
    "JobStatusEnum",
    "JobPriorityEnum",
    "CheckpointTypeEnum",
    "CheckpointStatusEnum",
    "StorageTierEnum",
    "TemplateVisibilityEnum",
    # Requests
    "CreateTrainingJobRequest",
    "UpdateTrainingJobRequest",
    "CreateCheckpointRequest",
    "CreateJobTemplateRequest",
    "UpdateJobTemplateRequest",
    "CreateJobFromTemplateRequest",
    "TrainingConfigSchema",
    # Responses
    "TrainingJobSummary",
    "TrainingJobDetail",
    "TrainingJobListResponse",
    "CheckpointResponse",
    "JobTemplateSummary",
    "JobTemplateDetail",
    "JobTemplateListResponse",
    # Log responses
    "LogEntry",
    "TrainingLogsResponse",
    # Kueue debug responses
    "KueueDebugResponse",
    "KueueWorkloadStatus",
    "KueueCondition",
    "KueueAdmission",
    "KueueQuotaUsage",
    "QueueInfo",
    "PreemptionEvent",
]
