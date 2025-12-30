"""模型管理相关的Pydantic schemas"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from models import ModelStatus, ModelFramework


# ==================== 模型相关 schemas ====================


class ModelCreate(BaseModel):
    """创建模型请求"""

    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    description: str | None = Field(None, max_length=1000, description="模型描述")
    framework: ModelFramework = Field(..., description="模型框架")
    task_type: str | None = Field(None, max_length=50, description="任务类型")
    project_id: int = Field(..., gt=0, description="所属项目ID")
    source_training_job_id: int | None = Field(None, gt=0, description="来源训练任务ID")
    tags: list[str] | None = Field(None, description="标签列表")
    metadata: dict[str, Any] | None = Field(None, description="元数据")


class ModelUpdate(BaseModel):
    """更新模型请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="模型名称")
    description: str | None = Field(None, max_length=1000, description="模型描述")
    task_type: str | None = Field(None, max_length=50, description="任务类型")
    tags: list[str] | None = Field(None, description="标签列表")
    metadata: dict[str, Any] | None = Field(None, description="元数据")


class ModelResponse(BaseModel):
    """模型响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    framework: ModelFramework
    task_type: str | None
    project_id: int
    creator_id: int
    source_training_job_id: int | None
    tags: list[str] | None
    metadata: dict[str, Any] | None
    latest_version: str | None
    latest_version_id: int | None
    created_at: datetime
    updated_at: datetime


class ModelListResponse(BaseModel):
    """模型列表响应"""

    items: list[ModelResponse]
    total: int
    page: int
    page_size: int


# ==================== 模型版本相关 schemas ====================


class ModelVersionCreate(BaseModel):
    """创建模型版本请求"""

    version: str = Field(..., min_length=1, max_length=50, description="版本号")
    description: str | None = Field(None, max_length=1000, description="版本描述")
    model_format: str | None = Field(None, max_length=50, description="模型格式")
    model_architecture: str | None = Field(None, max_length=100, description="模型架构")
    metrics: dict[str, Any] | None = Field(None, description="性能指标")
    hyperparameters: dict[str, Any] | None = Field(None, description="超参数")
    dependencies: dict[str, Any] | None = Field(None, description="依赖信息")


class ModelVersionUpdate(BaseModel):
    """更新模型版本请求"""

    description: str | None = Field(None, max_length=1000, description="版本描述")
    model_format: str | None = Field(None, max_length=50, description="模型格式")
    model_architecture: str | None = Field(None, max_length=100, description="模型架构")
    metrics: dict[str, Any] | None = Field(None, description="性能指标")
    hyperparameters: dict[str, Any] | None = Field(None, description="超参数")
    dependencies: dict[str, Any] | None = Field(None, description="依赖信息")


class ModelVersionResponse(BaseModel):
    """模型版本响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    version: str
    description: str | None
    status: ModelStatus
    error_message: str | None
    storage_path: str
    storage_size_bytes: int | None
    checksum_md5: str | None
    model_format: str | None
    model_architecture: str | None
    metrics: dict[str, Any] | None
    hyperparameters: dict[str, Any] | None
    dependencies: dict[str, Any] | None
    is_published: bool
    published_at: datetime | None
    published_by_id: int | None
    created_at: datetime
    updated_at: datetime


class ModelVersionListResponse(BaseModel):
    """模型版本列表响应"""

    items: list[ModelVersionResponse]


class ModelFileInfo(BaseModel):
    """模型文件信息"""

    name: str = Field(..., description="文件名")
    path: str = Field(..., description="相对路径")
    size: int = Field(..., description="文件大小(字节)")
    modified_at: str = Field(..., description="修改时间")


class ModelFilesResponse(BaseModel):
    """模型文件列表响应"""

    files: list[ModelFileInfo]


class ModelStorageStats(BaseModel):
    """模型存储统计"""

    total_size: int = Field(..., description="总大小(字节)")
    file_count: int = Field(..., description="文件数量")
    version_count: int = Field(..., description="版本数量")


__all__ = [
    "ModelCreate",
    "ModelUpdate",
    "ModelResponse",
    "ModelListResponse",
    "ModelVersionCreate",
    "ModelVersionUpdate",
    "ModelVersionResponse",
    "ModelVersionListResponse",
    "ModelFileInfo",
    "ModelFilesResponse",
    "ModelStorageStats",
]
