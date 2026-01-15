"""Resource type value object for audit logging."""

from enum import Enum


class ResourceType(Enum):
    """Resource type being audited."""

    TRAINING_JOB = "training_job"
    DATASET = "dataset"
    MODEL = "model"
    USER = "user"
    QUOTA = "quota"
    SPACE = "space"
