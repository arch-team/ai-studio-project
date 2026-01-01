"""训练任务相关的API Schemas"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from models.training import TrainingJobStatus, TrainingJobType, FrameworkType


# === 训练任务配置相关 ===


class TrainingJobConfigCreate(BaseModel):
    """创建训练任务配置"""

    # 资源配置
    node_count: int = Field(default=1, ge=1, le=100, description="节点数量")
    gpu_per_node: int = Field(default=1, ge=0, le=8, description="每节点GPU数")
    cpu_per_node: int = Field(default=8, ge=1, le=96, description="每节点CPU数")
    memory_per_node_gb: int = Field(default=32, ge=4, le=1024, description="每节点内存(GB)")
    gpu_type: Optional[str] = Field(default=None, max_length=50, description="GPU型号")

    # 训练配置
    docker_image: str = Field(..., max_length=500, description="Docker镜像")
    command: list[str] = Field(..., min_length=1, description="执行命令")
    args: Optional[list[str]] = Field(default=None, description="命令参数")
    env_vars: Optional[dict[str, str]] = Field(default=None, description="环境变量")

    # 数据配置
    dataset_path: Optional[str] = Field(default=None, max_length=500, description="数据集路径")
    checkpoint_path: Optional[str] = Field(default=None, max_length=500, description="检查点路径")
    output_path: str = Field(..., max_length=500, description="输出路径")

    # 超参数
    hyperparameters: Optional[dict] = Field(default=None, description="超参数")

    # 分布式配置
    distributed_config: Optional[dict] = Field(default=None, description="分布式训练配置")

    # 超时和重试
    timeout_seconds: Optional[int] = Field(default=None, ge=60, le=604800, description="超时时间(秒)")
    max_retries: int = Field(default=0, ge=0, le=10, description="最大重试次数")


class TrainingJobConfigResponse(TrainingJobConfigCreate):
    """训练任务配置响应"""

    id: int
    job_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === 训练任务相关 ===


class TrainingJobCreate(BaseModel):
    """创建训练任务请求"""

    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    job_type: TrainingJobType = Field(..., description="任务类型")
    framework: FrameworkType = Field(..., description="训练框架")
    project_id: int = Field(..., gt=0, description="项目ID")
    config: TrainingJobConfigCreate = Field(..., description="任务配置")

    # Kueue Gang Scheduling支持
    priority: str = Field(
        default="normal",
        description="Kueue优先级: low, normal, high",
        pattern="^(low|normal|high)$"
    )
    queue_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Kueue队列名称,默认使用项目队列(project-{project_id}-queue)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证任务名称"""
        if not v or not v.strip():
            raise ValueError("任务名称不能为空")
        # K8s名称约束: 小写字母、数字、-
        if not all(c.isalnum() or c in ["-", "_"] for c in v):
            raise ValueError("任务名称只能包含字母、数字、-和_")
        return v.strip()


class TrainingJobUpdate(BaseModel):
    """更新训练任务请求"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    priority: Optional[str] = Field(
        default=None,
        description="Kueue优先级: low, normal, high",
        pattern="^(low|normal|high)$"
    )


class TrainingJobResponse(BaseModel):
    """训练任务响应"""

    id: int
    name: str
    description: Optional[str]
    status: TrainingJobStatus
    job_type: TrainingJobType
    framework: FrameworkType

    # 关联信息
    project_id: int
    creator_id: int

    # Kubernetes信息
    k8s_namespace: str
    k8s_job_name: Optional[str]
    k8s_pod_names: Optional[list[str]]

    # Kueue Gang Scheduling信息
    priority: Optional[str]
    queue_name: Optional[str]

    # 时间信息
    queued_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # 失败信息
    error_message: Optional[str]
    exit_code: Optional[int]

    # 配置(可选包含)
    config: Optional[TrainingJobConfigResponse] = None

    class Config:
        from_attributes = True


class TrainingJobListResponse(BaseModel):
    """训练任务列表响应"""

    items: list[TrainingJobResponse]
    total: int
    page: int
    size: int
    pages: int


class TrainingJobDetailResponse(TrainingJobResponse):
    """训练任务详情响应(包含配置)"""

    config: TrainingJobConfigResponse

    class Config:
        from_attributes = True


# === 训练任务操作相关 ===


class TrainingJobStartRequest(BaseModel):
    """启动训练任务请求"""

    force: bool = Field(default=False, description="强制启动(即使已经在运行)")


class TrainingJobStopRequest(BaseModel):
    """停止训练任务请求"""

    save_checkpoint: bool = Field(default=True, description="是否保存检查点")
    reason: Optional[str] = Field(default=None, max_length=500, description="停止原因")


class TrainingJobResumeRequest(BaseModel):
    """恢复训练任务请求"""

    checkpoint_id: Optional[int] = Field(default=None, description="检查点ID(None表示使用最新)")


class TrainingJobStatusResponse(BaseModel):
    """训练任务状态响应"""

    id: int
    status: TrainingJobStatus
    queued_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    exit_code: Optional[int]

    class Config:
        from_attributes = True


# === 训练指标相关 ===


class TrainingMetricsResponse(BaseModel):
    """训练指标响应"""

    id: int
    job_id: int
    timestamp: datetime
    metrics: dict
    step: Optional[int]
    epoch: Optional[int]

    class Config:
        from_attributes = True


class TrainingMetricsListResponse(BaseModel):
    """训练指标列表响应"""

    items: list[TrainingMetricsResponse]
    total: int


# === 检查点相关 ===


class CheckpointResponse(BaseModel):
    """检查点响应"""

    id: int
    job_id: int
    name: str
    storage_path: str
    storage_type: str
    size_bytes: Optional[int]
    step: Optional[int]
    epoch: Optional[int]
    metrics: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class CheckpointListResponse(BaseModel):
    """检查点列表响应"""

    items: list[CheckpointResponse]
    total: int


# === 训练日志相关 ===


class TrainingLogResponse(BaseModel):
    """训练日志响应"""

    timestamp: datetime
    pod_name: str
    container_name: str
    log_line: str


class TrainingLogListResponse(BaseModel):
    """训练日志列表响应"""

    items: list[TrainingLogResponse]
    total: int
    has_more: bool
