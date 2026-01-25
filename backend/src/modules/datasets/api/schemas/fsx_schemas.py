"""FSx Sync API schemas - FSx 同步请求/响应模型。"""

from enum import Enum

from pydantic import BaseModel, Field


class FsxTaskStatusEnum(str, Enum):
    """FSx 任务状态枚举 (API 层)。"""

    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


# ========== 请求 Schema ==========


class PrefetchDatasetRequest(BaseModel):
    """数据集预热请求。"""

    paths: list[str] | None = Field(
        default=None,
        description="要预热的子路径列表 (可选，默认整个数据集)",
    )


# ========== 响应 Schema ==========


class FsxSyncResponse(BaseModel):
    """FSx 同步任务响应。"""

    task_id: str = Field(..., description="FSx 任务 ID")
    status: str = Field(..., description="任务状态")
    type: str = Field(..., description="任务类型")
    dataset_id: int = Field(..., description="数据集 ID")
    paths: list[str] = Field(default_factory=list, description="同步路径列表")


class FsxSyncStatusResponse(BaseModel):
    """FSx 同步状态响应。"""

    task_id: str = Field(..., description="FSx 任务 ID")
    status: str = Field(..., description="任务状态")
    type: str | None = Field(default=None, description="任务类型")
    progress: dict = Field(default_factory=dict, description="进度信息")
    paths: list[str] = Field(default_factory=list, description="同步路径列表")


class FsxPathResponse(BaseModel):
    """FSx 路径信息响应。"""

    dataset_id: int = Field(..., description="数据集 ID")
    fsx_path: str = Field(..., description="FSx 挂载路径")
    s3_path: str = Field(..., description="S3 路径")
    storage_uri: str | None = Field(default=None, description="数据集存储 URI")


class FsxAvailabilityResponse(BaseModel):
    """FSx 可用性响应。"""

    available: bool = Field(..., description="FSx 是否可用")
    filesystem_id: str | None = Field(default=None, description="文件系统 ID")
    storage_capacity_gb: int | None = Field(default=None, description="存储容量 (GB)")
    lifecycle: str | None = Field(default=None, description="生命周期状态")
    error: str | None = Field(default=None, description="错误信息 (如果不可用)")
