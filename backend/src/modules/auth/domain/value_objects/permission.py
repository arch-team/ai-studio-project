"""Permission value object."""

from enum import Enum


class Permission(str, Enum):
    """Permission definitions for the platform."""

    # User management
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Training job management
    TRAINING_JOB_VIEW = "training_job:view"
    TRAINING_JOB_CREATE = "training_job:create"
    TRAINING_JOB_UPDATE = "training_job:update"
    TRAINING_JOB_DELETE = "training_job:delete"
    TRAINING_JOB_CANCEL = "training_job:cancel"

    # Dataset management
    DATASET_VIEW = "dataset:view"
    DATASET_CREATE = "dataset:create"
    DATASET_UPDATE = "dataset:update"
    DATASET_DELETE = "dataset:delete"

    # Model management
    MODEL_VIEW = "model:view"
    MODEL_CREATE = "model:create"
    MODEL_UPDATE = "model:update"
    MODEL_DELETE = "model:delete"
    MODEL_DEPLOY = "model:deploy"

    # Cluster management
    CLUSTER_VIEW = "cluster:view"
    CLUSTER_CREATE = "cluster:create"
    CLUSTER_UPDATE = "cluster:update"
    CLUSTER_DELETE = "cluster:delete"
    CLUSTER_SCALE = "cluster:scale"

    # Resource quota management
    QUOTA_VIEW = "quota:view"
    QUOTA_CREATE = "quota:create"
    QUOTA_UPDATE = "quota:update"
    QUOTA_DELETE = "quota:delete"

    # Development space management
    DEV_SPACE_VIEW = "dev_space:view"
    DEV_SPACE_CREATE = "dev_space:create"
    DEV_SPACE_UPDATE = "dev_space:update"
    DEV_SPACE_DELETE = "dev_space:delete"

    # Audit log access
    AUDIT_VIEW = "audit:view"

    # System administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
