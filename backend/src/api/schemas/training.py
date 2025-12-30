"""训练任务API模式定义

定义训练任务相关的请求和响应模式
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from models.training import FrameworkType, TrainingJobStatus, TrainingJobType


# ==================== 请求模式 ====================


class TrainingJobConfigCreate(BaseModel):
    """训练任务配置创建模式"""

    # 资源配置
    node_count: int = Field(default=1, ge=1, le=100, description="节点数量")
    gpu_per_node: int = Field(default=1, ge=0, le=8, description="每节点GPU数")
    cpu_per_node: int = Field(default=8, ge=1, le=64, description="每节点CPU核心数")
    memory_per_node_gb: int = Field(
        default=32, ge=1, le=512, description="每节点内存(GB)"
    )
    gpu_type: str | None = Field(default=None, description="GPU型号")

    # 容器配置
    docker_image: str = Field(..., description="Docker镜像")
    command: list[str] = Field(..., description="执行命令")
    args: list[str] | None = Field(default=None, description="命令参数")
    env_vars: dict[str, str] | None = Field(default=None, description="环境变量")

    # 数据配置
    dataset_path: str | None = Field(default=None, description="数据集路径")
    checkpoint_path: str | None = Field(default=None, description="检查点路径")
    output_path: str = Field(..., description="输出路径")

    # 训练配置
    hyperparameters: dict[str, Any] | None = Field(
        default=None, description="超参数配置"
    )
    distributed_config: dict[str, Any] | None = Field(
        default=None, description="分布式配置"
    )

    # 执行配置
    timeout_seconds: int | None = Field(
        default=None, ge=60, le=604800, description="超时时间(秒)"
    )
    max_retries: int = Field(default=0, ge=0, le=5, description="最大重试次数")


class TrainingJobCreate(BaseModel):
    """训练任务创建模式"""

    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    description: str | None = Field(default=None, max_length=500, description="任务描述")
    job_type: TrainingJobType = Field(..., description="任务类型")
    framework: FrameworkType = Field(..., description="训练框架")
    project_id: int = Field(..., gt=0, description="项目ID")
    config: TrainingJobConfigCreate = Field(..., description="任务配置")


class TrainingJobUpdate(BaseModel):
    """训练任务更新模式"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ==================== 响应模式 ====================


class TrainingJobConfigResponse(BaseModel):
    """训练任务配置响应模式"""

    id: int
    job_id: int

    # 资源配置
    node_count: int
    gpu_per_node: int
    cpu_per_node: int
    memory_per_node_gb: int
    gpu_type: str | None

    # 容器配置
    docker_image: str
    command: list[str]
    args: list[str] | None
    env_vars: dict[str, str] | None

    # 数据配置
    dataset_path: str | None
    checkpoint_path: str | None
    output_path: str

    # 训练配置
    hyperparameters: dict[str, Any] | None
    distributed_config: dict[str, Any] | None

    # 执行配置
    timeout_seconds: int | None
    max_retries: int

    class Config:
        from_attributes = True


class TrainingJobResponse(BaseModel):
    """训练任务响应模式"""

    id: int
    name: str
    description: str | None
    status: TrainingJobStatus
    job_type: TrainingJobType
    framework: FrameworkType

    # 关联
    project_id: int
    creator_id: int

    # K8S信息
    k8s_namespace: str
    k8s_job_name: str | None
    k8s_pod_names: list[str] | None

    # 时间戳
    queued_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    # 错误信息
    error_message: str | None

    # 配置(可选包含)
    config: TrainingJobConfigResponse | None = None

    class Config:
        from_attributes = True


class TrainingJobListResponse(BaseModel):
    """训练任务列表响应模式"""

    total: int = Field(..., description="总数量")
    items: list[TrainingJobResponse] = Field(..., description="任务列表")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class TrainingJobStatusResponse(BaseModel):
    """训练任务状态响应模式"""

    id: int
    name: str
    status: str
    is_active: bool
    is_terminal: bool

    # 时间信息
    queued_at: str | None
    started_at: str | None
    completed_at: str | None
    duration_seconds: int | None

    # K8S信息
    k8s_job_name: str | None
    k8s_status: dict[str, Any] | None = None
    pods: list[dict[str, Any]] | None = None

    # 错误信息
    error_message: str | None
    k8s_error: str | None = None


__all__ = [
    "TrainingJobConfigCreate",
    "TrainingJobCreate",
    "TrainingJobUpdate",
    "TrainingJobConfigResponse",
    "TrainingJobResponse",
    "TrainingJobListResponse",
    "TrainingJobStatusResponse",
]
