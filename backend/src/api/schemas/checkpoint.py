"""Checkpoint相关的Pydantic模型

定义Checkpoint API的请求和响应模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.training import CheckpointStorageType


class CheckpointCreate(BaseModel):
    """创建Checkpoint请求模型"""

    job_id: int = Field(..., description="训练任务ID", gt=0)
    step: int = Field(..., description="训练步数", ge=0)
    storage_path: str = Field(..., description="存储路径(绝对路径或S3 URI)", min_length=1)
    storage_type: CheckpointStorageType = Field(..., description="存储类型")
    size_bytes: int = Field(..., description="文件大小(字节)", ge=0)
    epoch: Optional[int] = Field(None, description="训练轮次", ge=0)
    metadata: Optional[dict] = Field(None, description="元数据(学习率、优化器配置等)")
    metrics: Optional[dict] = Field(None, description="训练指标快照(loss, accuracy等)")

    model_config = {"json_schema_extra": {"example": {
        "job_id": 1,
        "step": 1000,
        "storage_path": "/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
        "storage_type": "LOCAL",
        "size_bytes": 1048576000,
        "epoch": 5,
        "metadata": {
            "learning_rate": 0.001,
            "optimizer": "AdamW",
            "batch_size": 32
        },
        "metrics": {
            "loss": 0.25,
            "accuracy": 0.92,
            "perplexity": 15.3
        }
    }}}


class CheckpointResponse(BaseModel):
    """Checkpoint响应模型"""

    id: int = Field(..., description="Checkpoint ID")
    job_id: int = Field(..., description="训练任务ID")
    step: int = Field(..., description="训练步数")
    epoch: Optional[int] = Field(None, description="训练轮次")
    storage_path: str = Field(..., description="存储路径")
    storage_type: CheckpointStorageType = Field(..., description="存储类型")
    size_bytes: int = Field(..., description="文件大小(字节)")
    checkpoint_metadata: Optional[dict] = Field(None, description="元数据")
    checkpoint_metrics: Optional[dict] = Field(None, description="训练指标快照")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class CheckpointListResponse(BaseModel):
    """Checkpoint列表响应模型"""

    checkpoints: list[CheckpointResponse] = Field(..., description="Checkpoint列表")
    total: int = Field(..., description="总数量")


class CheckpointDeleteResponse(BaseModel):
    """Checkpoint删除响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    deleted_count: Optional[int] = Field(None, description="删除数量(批量删除时)")


class CheckpointMigrateRequest(BaseModel):
    """Checkpoint迁移请求模型"""

    checkpoint_id: int = Field(..., description="Checkpoint ID", gt=0)
    delete_source: bool = Field(
        default=False, description="是否删除源文件(迁移后清理本地/FSx)"
    )


class CheckpointMigrateResponse(BaseModel):
    """Checkpoint迁移响应模型"""

    success: bool = Field(..., description="是否成功")
    s3_uri: str = Field(..., description="S3 URI")
    message: str = Field(..., description="消息")


__all__ = [
    "CheckpointCreate",
    "CheckpointResponse",
    "CheckpointListResponse",
    "CheckpointDeleteResponse",
    "CheckpointMigrateRequest",
    "CheckpointMigrateResponse",
]
