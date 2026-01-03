# Data Model Design: 企业级AI训练平台

**Feature**: `001-ai-training-platform`
**Branch**: `001-ai-training-platform`
**Date**: 2026-01-03
**Phase**: Phase 1 - Data Model Design
**Spec**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)
**Plan**: [plan.md](./plan.md)

---

## 概述

本文档定义企业级AI训练平台的数据模型设计,包括数据库表结构、实体关系、索引策略和迁移方案。

### 技术栈

**数据库**:
- **开发环境**: MySQL 8.0.28 (Docker 部署)
- **生产环境**: Amazon Aurora MySQL 3.04.x LTS (Multi-AZ + 2+ replicas)

**ORM 框架**:
- SQLAlchemy 2.0+ (异步模式)
- Alembic (数据库迁移)
- aiomysql (MySQL 驱动)

**设计原则**:
- ✅ **兼容性优先**: 确保开发环境 MySQL 8.0 与生产环境 Aurora MySQL 3.x 完全兼容
- ✅ **性能优化**: 基于访问模式设计索引,支持高并发查询
- ✅ **可扩展性**: 支持多租户和资源配额管理
- ✅ **审计追踪**: 所有表包含 created_at, updated_at 时间戳
- ✅ **软删除**: 关键实体支持软删除 (deleted_at)

---

## 核心实体关系图 (ER Diagram)

```
┌─────────────────┐
│     Users       │
│   (用户表)       │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────────────┐       ┌─────────────────────┐
│   TrainingJobs          │ N   1 │    Datasets         │
│   (训练任务表)            ├───────┤    (数据集表)        │
└────────┬────────────────┘       └─────────────────────┘
         │ 1
         │
         │ N
┌────────▼────────────────┐
│   Checkpoints           │
│   (检查点表)             │
└─────────────────────────┘

┌─────────────────────────┐       ┌─────────────────────┐
│   ResourceQuotas        │ 1   N │    Users            │
│   (资源配额表)           ├───────┤    (用户表)          │
└─────────────────────────┘       └─────────────────────┘

┌─────────────────────────┐
│   HyperPodClusters      │
│   (HyperPod 集群表)      │
└─────────────────────────┘
```

---

## 表结构设计

### 1. users (用户表)

**用途**: 存储平台用户信息,支持 AWS IAM Identity Center (SSO) 集成。

```sql
CREATE TABLE users (
    -- 主键
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',

    -- 身份信息
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名 (IAM 用户名)',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱地址',
    display_name VARCHAR(128) COMMENT '显示名称',

    -- IAM 集成
    iam_identity_id VARCHAR(255) UNIQUE COMMENT 'AWS IAM Identity Center 用户ID',
    iam_groups JSON COMMENT 'IAM 用户组列表 (JSON 数组)',

    -- 用户状态
    status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '用户状态',
    role ENUM('admin', 'user', 'viewer') NOT NULL DEFAULT 'user' COMMENT '用户角色',

    -- 资源配额 (关联到 resource_quotas 表)
    resource_quota_id BIGINT UNSIGNED COMMENT '关联的资源配额ID',

    -- 审计字段
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    last_login_at DATETIME(3) COMMENT '最后登录时间',

    -- 索引
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_resource_quota_id (resource_quota_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

**字段说明**:
- `iam_identity_id`: AWS IAM Identity Center (原 AWS SSO) 集成标识
- `iam_groups`: 用户所属 IAM 组,用于权限继承 (存储为 JSON 数组)
- `resource_quota_id`: 外键关联到 `resource_quotas` 表,定义用户资源配额
- `status`: 用户账号状态 (active=活跃, inactive=非活跃, suspended=已暂停)
- `role`: 平台角色 (admin=管理员, user=普通用户, viewer=只读用户)

**索引策略**:
- `username`, `email`: 登录查询优化
- `status`: 筛选活跃用户
- `resource_quota_id`: 关联查询优化
- `created_at`: 时间范围查询

---

### 2. resource_quotas (资源配额表)

**用途**: 定义用户或组的资源配额限制,支持多租户资源管理 (基于 Kueue)。

```sql
CREATE TABLE resource_quotas (
    -- 主键
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '配额ID',

    -- 配额标识
    name VARCHAR(128) NOT NULL UNIQUE COMMENT '配额名称 (例如: team-a-quota)',
    description TEXT COMMENT '配额描述',

    -- 配额类型
    quota_type ENUM('user', 'team', 'project') NOT NULL DEFAULT 'user' COMMENT '配额类型',

    -- CPU 配额 (单位: vCPU)
    max_cpu_cores INT UNSIGNED NOT NULL COMMENT '最大 CPU 核心数',
    reserved_cpu_cores INT UNSIGNED DEFAULT 0 COMMENT '预留 CPU 核心数',

    -- GPU 配额
    max_gpu_count INT UNSIGNED NOT NULL COMMENT '最大 GPU 数量',
    reserved_gpu_count INT UNSIGNED DEFAULT 0 COMMENT '预留 GPU 数量',
    gpu_types JSON COMMENT '允许的 GPU 类型 (例如: ["ml.p4d.24xlarge", "ml.g5.xlarge"])',

    -- 内存配额 (单位: GB)
    max_memory_gb INT UNSIGNED NOT NULL COMMENT '最大内存 (GB)',
    reserved_memory_gb INT UNSIGNED DEFAULT 0 COMMENT '预留内存 (GB)',

    -- 存储配额 (单位: GB)
    max_storage_gb INT UNSIGNED COMMENT '最大存储空间 (GB)',

    -- 训练任务配额
    max_concurrent_jobs INT UNSIGNED NOT NULL DEFAULT 5 COMMENT '最大并发训练任务数',
    max_total_jobs INT UNSIGNED COMMENT '总训练任务数限制 (NULL 表示无限制)',

    -- Spot 实例配额
    max_spot_instances INT UNSIGNED DEFAULT 0 COMMENT '最大 Spot 实例数',

    -- 配额状态
    status ENUM('active', 'suspended', 'expired') NOT NULL DEFAULT 'active' COMMENT '配额状态',

    -- 有效期
    valid_from DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '生效时间',
    valid_until DATETIME(3) COMMENT '过期时间 (NULL 表示永久)',

    -- 审计字段
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    created_by BIGINT UNSIGNED COMMENT '创建人用户ID',

    -- 索引
    INDEX idx_name (name),
    INDEX idx_quota_type (quota_type),
    INDEX idx_status (status),
    INDEX idx_valid_period (valid_from, valid_until),

    -- 外键
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资源配额表';
```

**字段说明**:
- `quota_type`: 配额类型 (user=用户级, team=团队级, project=项目级)
- `reserved_*`: Kueue 预留资源 (保证最低资源可用性)
- `max_*`: Kueue 最大资源限制 (资源使用上限)
- `gpu_types`: 允许使用的 GPU 实例类型列表 (JSON 数组)
- `valid_from`, `valid_until`: 配额有效期 (支持临时配额)

**Kueue 映射**:
- 该表对应 Kueue 的 `ClusterQueue` 和 `ResourceFlavor` 资源
- 后端将配额信息同步到 Kueue CRD

**索引策略**:
- `name`: 配额名称唯一索引
- `status`: 筛选活跃配额
- `valid_period`: 时间范围查询

---

### 3. datasets (数据集表)

**用途**: 存储训练数据集元数据,支持 FSx for Lustre 和 S3 数据源。

```sql
CREATE TABLE datasets (
    -- 主键
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '数据集ID',

    -- 数据集标识
    name VARCHAR(128) NOT NULL COMMENT '数据集名称',
    description TEXT COMMENT '数据集描述',
    version VARCHAR(32) NOT NULL DEFAULT 'v1' COMMENT '数据集版本',

    -- 存储位置
    storage_type ENUM('fsx', 's3', 'efs') NOT NULL DEFAULT 'fsx' COMMENT '存储类型',
    storage_uri VARCHAR(512) NOT NULL COMMENT '存储 URI (例如: s3://bucket/path 或 /fsx/datasets/imagenet)',

    -- 数据集统计
    total_size_bytes BIGINT UNSIGNED COMMENT '总大小 (字节)',
    file_count INT UNSIGNED COMMENT '文件数量',

    -- 数据集类型
    dataset_type ENUM('image', 'text', 'audio', 'video', 'tabular', 'custom') NOT NULL COMMENT '数据集类型',
    data_format VARCHAR(64) COMMENT '数据格式 (例如: imagenet, coco, csv, parquet)',

    -- 数据集标签
    tags JSON COMMENT '数据集标签 (JSON 数组,例如: ["cv", "classification", "imagenet"])',

    -- 访问权限
    visibility ENUM('public', 'private', 'restricted') NOT NULL DEFAULT 'private' COMMENT '可见性',
    owner_id BIGINT UNSIGNED NOT NULL COMMENT '所有者用户ID',

    -- 数据集状态
    status ENUM('available', 'preparing', 'archived', 'error') NOT NULL DEFAULT 'preparing' COMMENT '数据集状态',

    -- 审计字段
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    last_accessed_at DATETIME(3) COMMENT '最后访问时间',

    -- 唯一约束
    UNIQUE KEY uk_name_version (name, version),

    -- 索引
    INDEX idx_owner_id (owner_id),
    INDEX idx_storage_type (storage_type),
    INDEX idx_dataset_type (dataset_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FULLTEXT INDEX ft_name_desc (name, description),

    -- 外键
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据集表';
```

**字段说明**:
- `storage_type`: 存储类型 (fsx=FSx for Lustre, s3=S3, efs=EFS)
- `storage_uri`: 数据集存储位置 (支持 S3 URI 和文件系统路径)
- `dataset_type`: 数据类型 (image=图像, text=文本, audio=音频, video=视频, tabular=表格, custom=自定义)
- `data_format`: 具体格式 (imagenet, coco, csv, parquet 等)
- `visibility`: 数据集可见性 (public=公开, private=私有, restricted=受限)
- `status`: 数据集状态 (available=可用, preparing=准备中, archived=已归档, error=错误)

**索引策略**:
- `uk_name_version`: 唯一约束 (同一名称只能有一个版本)
- `owner_id`: 用户数据集查询
- `storage_type`, `dataset_type`: 按类型筛选
- `ft_name_desc`: 全文搜索索引 (支持数据集名称和描述搜索)

---

### 4. training_jobs (训练任务表)

**用途**: 存储训练任务元数据,对应 HyperPod SDK 的 `HyperPodPytorchJob` 资源。

```sql
CREATE TABLE training_jobs (
    -- 主键
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '训练任务ID',

    -- 任务标识
    job_name VARCHAR(128) NOT NULL UNIQUE COMMENT '任务名称 (HyperPod Job 名称)',
    display_name VARCHAR(256) COMMENT '显示名称',
    description TEXT COMMENT '任务描述',

    -- 所有者
    owner_id BIGINT UNSIGNED NOT NULL COMMENT '所有者用户ID',

    -- 训练配置
    image_uri VARCHAR(512) NOT NULL COMMENT 'Docker 镜像 URI',
    instance_type VARCHAR(64) NOT NULL COMMENT '实例类型 (例如: ml.p4d.24xlarge)',
    node_count INT UNSIGNED NOT NULL DEFAULT 1 COMMENT '节点数量',
    tasks_per_node INT UNSIGNED NOT NULL DEFAULT 1 COMMENT '每节点任务数 (GPU 数量)',

    -- 训练脚本
    entrypoint_command JSON NOT NULL COMMENT '启动命令 (JSON 数组,例如: ["torchrun", "--nproc_per_node=8", "train.py"])',
    environment_variables JSON COMMENT '环境变量 (JSON 对象)',

    -- 数据集配置
    dataset_id BIGINT UNSIGNED COMMENT '关联数据集ID',
    data_mount_path VARCHAR(256) COMMENT '数据挂载路径 (例如: /data)',

    -- 检查点配置
    checkpoint_mount_path VARCHAR(256) COMMENT '检查点挂载路径 (例如: /checkpoints)',
    checkpoint_interval INT UNSIGNED COMMENT '检查点保存间隔 (epoch)',

    -- 训练参数
    hyperparameters JSON COMMENT '超参数 (JSON 对象)',
    max_epochs INT UNSIGNED COMMENT '最大训练轮数',
    batch_size INT UNSIGNED COMMENT '批次大小',
    learning_rate DECIMAL(10, 8) COMMENT '学习率',

    -- 分布式训练配置
    distribution_strategy ENUM('ddp', 'fsdp', 'deepspeed', 'horovod') NOT NULL DEFAULT 'ddp' COMMENT '分布式策略',
    mixed_precision BOOLEAN DEFAULT FALSE COMMENT '是否使用混合精度训练 (AMP)',

    -- Spot 实例配置
    use_spot_instances BOOLEAN DEFAULT FALSE COMMENT '是否使用 Spot 实例',
    spot_interruption_behavior ENUM('stop', 'terminate', 'hibernate') DEFAULT 'stop' COMMENT 'Spot 中断行为',

    -- 调度优先级 (对应 FR-004 抢占式调度)
    priority ENUM('high', 'medium', 'low') NOT NULL DEFAULT 'medium' COMMENT '任务优先级 (用于抢占式调度)',

    -- 任务状态 (对应 spec.md 状态机)
    status ENUM('submitted', 'running', 'paused', 'preempted', 'completed', 'failed') NOT NULL DEFAULT 'submitted' COMMENT '任务状态',

    -- HyperPod 状态映射
    hyperpod_status VARCHAR(64) COMMENT 'HyperPod Job 原始状态',
    kueue_workload_name VARCHAR(128) COMMENT 'Kueue Workload 名称',
    kueue_status VARCHAR(64) COMMENT 'Kueue Workload 状态',

    -- 任务统计
    total_pods INT UNSIGNED COMMENT '总 Pod 数量',
    running_pods INT UNSIGNED DEFAULT 0 COMMENT '运行中 Pod 数量',
    failed_pods INT UNSIGNED DEFAULT 0 COMMENT '失败 Pod 数量',

    -- 抢占统计 (用于连续抢占失败检测)
    preemption_count INT UNSIGNED DEFAULT 0 COMMENT '累计被抢占次数 (用于判断是否超过阈值)',

    -- 训练指标 (最新值)
    current_epoch INT UNSIGNED COMMENT '当前训练轮次',
    current_step BIGINT UNSIGNED COMMENT '当前训练步数',
    latest_loss DECIMAL(10, 6) COMMENT '最新损失值',
    latest_accuracy DECIMAL(5, 4) COMMENT '最新准确率',

    -- 时间统计
    submitted_at DATETIME(3) COMMENT '提交时间',
    started_at DATETIME(3) COMMENT '开始时间',
    completed_at DATETIME(3) COMMENT '完成时间',
    duration_seconds INT UNSIGNED COMMENT '运行时长 (秒)',

    -- 资源统计
    total_gpu_hours DECIMAL(12, 2) COMMENT '总 GPU 时',
    estimated_cost_usd DECIMAL(12, 2) COMMENT '预估成本 (USD)',

    -- 错误信息
    error_message TEXT COMMENT '错误信息',
    failure_reason VARCHAR(512) COMMENT '失败原因',

    -- 审计字段
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',

    -- 索引
    INDEX idx_owner_id (owner_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_dataset_id (dataset_id),
    INDEX idx_submitted_at (submitted_at),
    INDEX idx_completed_at (completed_at),
    INDEX idx_hyperpod_status (hyperpod_status),
    INDEX idx_kueue_workload_name (kueue_workload_name),
    INDEX idx_status_priority (status, priority),
    FULLTEXT INDEX ft_job_name_desc (job_name, description),

    -- 外键
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='训练任务表';
```

**字段说明**:
- `job_name`: HyperPod Job 名称 (必须全局唯一,对应 K8s 资源名称)
- `entrypoint_command`: 训练启动命令 (JSON 数组,例如: `["torchrun", "train.py"]`)
- `environment_variables`: 环境变量 (JSON 对象,例如: `{"NCCL_DEBUG": "INFO"}`)
- `distribution_strategy`: 分布式训练策略 (ddp=DDP, fsdp=FSDP, deepspeed=DeepSpeed, horovod=Horovod)
- `priority`: 任务优先级 (high=高优先级, medium=中优先级, low=低优先级),用于 FR-004 抢占式调度,高优先级任务可抢占低优先级任务资源
- `status`: 平台标准化状态 (对应 spec.md 的 6 种状态)
- `hyperpod_status`: HyperPod SDK 返回的原始状态 (Pending, Running, Succeeded, Failed)
- `kueue_workload_name`: Kueue Workload 资源名称 (用于资源配额管理)
- `kueue_status`: Kueue Workload 状态 (Pending, Admitted, Finished)

**状态映射逻辑** (spec.md Section 2.2):
```python
# HyperPod 状态 → 平台状态
STATUS_MAPPING = {
    "Pending": "submitted",      # 等待资源分配
    "Running": "running",        # 训练中
    "Succeeded": "completed",    # 成功完成
    "Failed": "failed",          # 失败
}

# Kueue 状态 → 平台状态
KUEUE_STATUS_MAPPING = {
    "Pending": "submitted",      # 等待配额
    "Admitted": "running",       # 已分配资源
    "Evicted": "preempted",      # Spot 实例被抢占
}
```

**索引策略**:
- `owner_id`: 用户任务查询
- `status`: 按状态筛选 (运行中、已完成等)
- `priority`: 按优先级筛选和排序
- `status_priority`: 复合索引,优化按状态和优先级的联合查询 (如查找所有 submitted 状态的 high 优先级任务)
- `submitted_at`, `completed_at`: 时间范围查询
- `hyperpod_status`, `kueue_workload_name`: HyperPod/Kueue 集成查询
- `ft_job_name_desc`: 全文搜索

---

### 5. checkpoints (检查点表)

**用途**: 存储训练检查点元数据,后端扫描 FSx for Lustre 存储生成 (research.md Section 1.4)。

```sql
CREATE TABLE checkpoints (
    -- 主键
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '检查点ID',

    -- 关联训练任务
    training_job_id BIGINT UNSIGNED NOT NULL COMMENT '关联训练任务ID',

    -- 检查点标识
    checkpoint_name VARCHAR(256) NOT NULL COMMENT '检查点名称 (例如: checkpoint-epoch100.pth)',
    storage_path VARCHAR(512) NOT NULL COMMENT '存储路径 (例如: /fsx/checkpoints/job-123/checkpoint-epoch100.pth)',

    -- 检查点类型
    checkpoint_type ENUM('epoch', 'step', 'best', 'final', 'manual') NOT NULL DEFAULT 'epoch' COMMENT '检查点类型',

    -- 训练进度
    epoch INT UNSIGNED COMMENT '训练轮次',
    step BIGINT UNSIGNED COMMENT '训练步数',

    -- 检查点统计
    size_bytes BIGINT UNSIGNED NOT NULL COMMENT '文件大小 (字节)',

    -- 训练指标 (检查点保存时的指标)
    loss DECIMAL(10, 6) COMMENT '损失值',
    accuracy DECIMAL(5, 4) COMMENT '准确率',
    metrics JSON COMMENT '其他指标 (JSON 对象)',

    -- 存储层级 (分层存储)
    storage_tier ENUM('nvme', 'fsx', 's3') NOT NULL DEFAULT 'fsx' COMMENT '存储层级',

    -- 检查点状态
    status ENUM('available', 'archived', 'deleted') NOT NULL DEFAULT 'available' COMMENT '检查点状态',

    -- 审计字段
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    archived_at DATETIME(3) COMMENT '归档时间 (S3)',
    deleted_at DATETIME(3) COMMENT '删除时间 (软删除)',

    -- 唯一约束
    UNIQUE KEY uk_job_checkpoint_name (training_job_id, checkpoint_name),

    -- 索引
    INDEX idx_training_job_id (training_job_id),
    INDEX idx_checkpoint_type (checkpoint_type),
    INDEX idx_storage_tier (storage_tier),
    INDEX idx_status (status),
    INDEX idx_epoch (epoch),
    INDEX idx_created_at (created_at),

    -- 外键
    FOREIGN KEY (training_job_id) REFERENCES training_jobs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检查点表';
```

**字段说明**:
- `checkpoint_name`: 检查点文件名 (例如: `checkpoint-epoch100.pth`)
- `storage_path`: FSx for Lustre 或 S3 完整路径
- `checkpoint_type`: 检查点类型 (epoch=按轮次, step=按步数, best=最佳模型, final=最终模型, manual=手动保存)
- `storage_tier`: 存储层级 (nvme=本地 NVMe, fsx=FSx for Lustre, s3=S3 归档)
- `status`: 检查点状态 (available=可用, archived=已归档到 S3, deleted=已删除)

**生成流程** (research.md Section 1.4):
```python
# 后端 CheckpointService 扫描 FSx 存储
async def scan_checkpoints(job_id: int, checkpoint_dir: str):
    """
    扫描训练任务的检查点目录并生成元数据

    Example:
    /fsx/checkpoints/job-123/
    ├── checkpoint-epoch10.pth   (5.2 GB)
    ├── checkpoint-epoch20.pth   (5.2 GB)
    └── checkpoint-epoch100.pth  (5.2 GB)
    """
    for file in os.listdir(checkpoint_dir):
        if file.endswith('.pth') or file.endswith('.ckpt'):
            size_bytes = os.path.getsize(file_path)
            epoch = extract_epoch_from_filename(file)

            # 创建检查点记录
            checkpoint = Checkpoint(
                training_job_id=job_id,
                checkpoint_name=file,
                storage_path=file_path,
                epoch=epoch,
                size_bytes=size_bytes,
                storage_tier='fsx',
                status='available'
            )
            db.add(checkpoint)
```

**索引策略**:
- `uk_job_checkpoint_name`: 同一任务不允许重复检查点名称
- `training_job_id`: 查询任务的所有检查点
- `checkpoint_type`: 筛选特定类型检查点 (如最佳模型)
- `epoch`: 按训练进度查询

---

### 6. hyperpod_clusters (HyperPod 集群表)

**用途**: 存储 HyperPod 集群信息,用于任务调度和资源管理。

```sql
CREATE TABLE hyperpod_clusters (
    -- 主键
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '集群ID',

    -- 集群标识
    cluster_name VARCHAR(128) NOT NULL UNIQUE COMMENT '集群名称 (HyperPod Cluster 名称)',
    cluster_arn VARCHAR(512) NOT NULL UNIQUE COMMENT '集群 ARN',

    -- 集群配置
    region VARCHAR(32) NOT NULL COMMENT 'AWS 区域',
    vpc_id VARCHAR(64) NOT NULL COMMENT 'VPC ID',

    -- 实例配置
    instance_groups JSON NOT NULL COMMENT '实例组配置 (JSON 数组)',
    total_nodes INT UNSIGNED NOT NULL COMMENT '总节点数',
    available_nodes INT UNSIGNED DEFAULT 0 COMMENT '可用节点数',

    -- 资源统计
    total_cpu_cores INT UNSIGNED COMMENT '总 CPU 核心数',
    total_gpu_count INT UNSIGNED COMMENT '总 GPU 数量',
    total_memory_gb INT UNSIGNED COMMENT '总内存 (GB)',

    -- 集群状态
    status ENUM('creating', 'active', 'updating', 'deleting', 'failed') NOT NULL DEFAULT 'creating' COMMENT '集群状态',
    health_status ENUM('healthy', 'degraded', 'unhealthy') COMMENT '健康状态',

    -- 存储配置
    fsx_filesystem_id VARCHAR(128) COMMENT 'FSx for Lustre 文件系统ID',
    fsx_mount_point VARCHAR(256) COMMENT 'FSx 挂载点路径',

    -- 监控配置
    prometheus_endpoint VARCHAR(512) COMMENT 'Prometheus 端点',
    grafana_workspace_id VARCHAR(128) COMMENT 'Grafana Workspace ID',

    -- 审计字段
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    last_sync_at DATETIME(3) COMMENT '最后同步时间',

    -- 索引
    INDEX idx_region (region),
    INDEX idx_status (status),
    INDEX idx_health_status (health_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='HyperPod 集群表';
```

**字段说明**:
- `cluster_name`: HyperPod 集群名称 (对应 AWS 资源)
- `cluster_arn`: AWS 资源唯一标识符
- `instance_groups`: 实例组配置 (JSON 数组,包含实例类型、数量、Spot 配置等)
- `status`: 集群状态 (creating=创建中, active=活跃, updating=更新中, deleting=删除中, failed=失败)
- `health_status`: 健康状态 (healthy=健康, degraded=降级, unhealthy=不健康)
- `fsx_filesystem_id`: FSx for Lustre 文件系统 ID (用于数据和检查点存储)

**instance_groups JSON 示例**:
```json
[
  {
    "instance_group_name": "on-demand-workers",
    "instance_type": "ml.p4d.24xlarge",
    "instance_count": 4,
    "capacity_type": "on_demand"
  },
  {
    "instance_group_name": "spot-workers",
    "instance_type": "ml.p4d.24xlarge",
    "instance_count": 16,
    "capacity_type": "spot",
    "spot_interruption_behavior": "stop"
  }
]
```

---

## 数据库配置

### SQLAlchemy 配置 (research.md Section 3.3)

```python
# backend/src/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 开发环境
DEV_DATABASE_URL = "mysql+aiomysql://user:password@localhost:3306/ai_training_platform?charset=utf8mb4"

# 生产环境 (Aurora MySQL 3.04.x LTS)
PROD_DATABASE_URL = "mysql+aiomysql://user:password@aurora-cluster.xxx.rds.amazonaws.com:3306/ai_training_platform?charset=utf8mb4"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Critical: Aurora 连接健康检查
    pool_recycle=3600,   # 防止 Aurora 连接超时 (默认 8 小时)
    echo=False,          # 生产环境关闭 SQL 日志
)

# 创建异步 Session 工厂
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 依赖注入
async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
```

### Alembic 迁移配置

```python
# alembic/env.py
from sqlalchemy import pool
from alembic import context
from backend.src.models import Base  # 导入所有 ORM 模型

# Alembic Config
config = context.config
target_metadata = Base.metadata

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to database)."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

**迁移脚本生成**:
```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "create initial tables"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

---

## ORM 模型示例

### User 模型

```python
# backend/src/models/user.py
from sqlalchemy import Column, String, Enum, DateTime, BigInteger, func
from sqlalchemy.orm import relationship
from backend.src.core.database import Base
import enum

class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"

class UserRole(enum.Enum):
    admin = "admin"
    user = "user"
    viewer = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(64), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(255), unique=True, nullable=False, index=True, comment="邮箱地址")
    display_name = Column(String(128), comment="显示名称")

    iam_identity_id = Column(String(255), unique=True, comment="AWS IAM Identity Center 用户ID")
    iam_groups = Column(JSON, comment="IAM 用户组列表")

    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.active, comment="用户状态")
    role = Column(Enum(UserRole), nullable=False, default=UserRole.user, comment="用户角色")

    resource_quota_id = Column(BigInteger, ForeignKey("resource_quotas.id"), comment="资源配额ID")

    created_at = Column(DateTime(3), nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(3), nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at = Column(DateTime(3), comment="最后登录时间")

    # 关系
    resource_quota = relationship("ResourceQuota", back_populates="users")
    training_jobs = relationship("TrainingJob", back_populates="owner", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
```

### TrainingJob 模型

```python
# backend/src/models/training_job.py
from sqlalchemy import Column, String, Enum, Integer, JSON, DateTime, BigInteger, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.src.core.database import Base
import enum

class JobStatus(enum.Enum):
    submitted = "submitted"
    running = "running"
    paused = "paused"
    preempted = "preempted"
    completed = "completed"
    failed = "failed"

class JobPriority(enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"

class DistributionStrategy(enum.Enum):
    ddp = "ddp"
    fsdp = "fsdp"
    deepspeed = "deepspeed"
    horovod = "horovod"

class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="训练任务ID")
    job_name = Column(String(128), unique=True, nullable=False, index=True, comment="任务名称")
    display_name = Column(String(256), comment="显示名称")
    description = Column(Text, comment="任务描述")

    owner_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所有者用户ID")

    image_uri = Column(String(512), nullable=False, comment="Docker 镜像 URI")
    instance_type = Column(String(64), nullable=False, comment="实例类型")
    node_count = Column(Integer, nullable=False, default=1, comment="节点数量")
    tasks_per_node = Column(Integer, nullable=False, default=1, comment="每节点任务数")

    entrypoint_command = Column(JSON, nullable=False, comment="启动命令")
    environment_variables = Column(JSON, comment="环境变量")

    dataset_id = Column(BigInteger, ForeignKey("datasets.id", ondelete="SET NULL"), index=True, comment="数据集ID")

    hyperparameters = Column(JSON, comment="超参数")
    distribution_strategy = Column(Enum(DistributionStrategy), nullable=False, default=DistributionStrategy.ddp, comment="分布式策略")

    priority = Column(Enum(JobPriority), nullable=False, default=JobPriority.medium, index=True, comment="任务优先级")
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.submitted, index=True, comment="任务状态")
    hyperpod_status = Column(String(64), index=True, comment="HyperPod Job 状态")
    kueue_workload_name = Column(String(128), index=True, comment="Kueue Workload 名称")

    current_epoch = Column(Integer, comment="当前训练轮次")
    latest_loss = Column(DECIMAL(10, 6), comment="最新损失值")

    submitted_at = Column(DateTime(3), index=True, comment="提交时间")
    started_at = Column(DateTime(3), comment="开始时间")
    completed_at = Column(DateTime(3), index=True, comment="完成时间")

    created_at = Column(DateTime(3), nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(3), nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    owner = relationship("User", back_populates="training_jobs")
    dataset = relationship("Dataset", back_populates="training_jobs")
    checkpoints = relationship("Checkpoint", back_populates="training_job", cascade="all, delete-orphan")
```

---

## 索引优化策略

### 1. 查询模式分析

**高频查询场景**:
```sql
-- Q1: 用户查询自己的训练任务 (按状态筛选)
SELECT * FROM training_jobs
WHERE owner_id = ? AND status = ?
ORDER BY created_at DESC;

-- Q2: 查询训练任务的所有检查点 (按 epoch 排序)
SELECT * FROM checkpoints
WHERE training_job_id = ? AND status = 'available'
ORDER BY epoch DESC;

-- Q3: 全文搜索训练任务 (按名称或描述)
SELECT * FROM training_jobs
WHERE MATCH(job_name, description) AGAINST (? IN NATURAL LANGUAGE MODE);

-- Q4: 时间范围查询 (资源使用统计)
SELECT * FROM training_jobs
WHERE submitted_at BETWEEN ? AND ? AND status = 'completed';
```

### 2. 组合索引建议

```sql
-- 训练任务表: 用户 + 状态 + 时间 组合索引
CREATE INDEX idx_owner_status_created ON training_jobs(owner_id, status, created_at);

-- 检查点表: 任务 + 状态 + Epoch 组合索引
CREATE INDEX idx_job_status_epoch ON checkpoints(training_job_id, status, epoch);

-- 数据集表: 所有者 + 类型 + 状态 组合索引
CREATE INDEX idx_owner_type_status ON datasets(owner_id, dataset_type, status);
```

### 3. 全文索引优化

```sql
-- 训练任务全文搜索
ALTER TABLE training_jobs ADD FULLTEXT INDEX ft_search (job_name, description);

-- 数据集全文搜索
ALTER TABLE datasets ADD FULLTEXT INDEX ft_search (name, description);

-- 全文搜索示例
SELECT * FROM training_jobs
WHERE MATCH(job_name, description) AGAINST ('llama3 fine-tuning' IN NATURAL LANGUAGE MODE);
```

---

## 数据迁移策略

### Phase 1: 初始化表结构

```bash
# 1. 生成迁移脚本
alembic revision --autogenerate -m "create initial schema"

# 2. 执行迁移
alembic upgrade head
```

### Phase 2: 数据填充 (Seed Data)

```python
# backend/scripts/seed_data.py
async def seed_initial_data():
    """初始化种子数据"""
    async with async_session_factory() as session:
        # 1. 创建管理员用户
        admin = User(
            username="admin",
            email="admin@example.com",
            display_name="Administrator",
            role=UserRole.admin,
            status=UserStatus.active,
        )
        session.add(admin)

        # 2. 创建默认资源配额
        default_quota = ResourceQuota(
            name="default-quota",
            description="Default resource quota for new users",
            quota_type="user",
            max_cpu_cores=64,
            max_gpu_count=8,
            max_memory_gb=512,
            max_concurrent_jobs=5,
            status="active",
        )
        session.add(default_quota)

        await session.commit()
```

### Phase 3: 生产环境迁移

```bash
# 1. 备份生产数据库
mysqldump -h aurora-cluster.xxx.rds.amazonaws.com -u admin -p ai_training_platform > backup_$(date +%Y%m%d).sql

# 2. 执行迁移 (只读模式验证)
alembic upgrade head --sql > migration.sql
# 人工审核 migration.sql

# 3. 执行迁移 (维护窗口)
alembic upgrade head

# 4. 验证迁移结果
python -m backend.scripts.verify_migration
```

---

## 性能优化建议

### 1. 连接池配置

```python
# 生产环境推荐配置
engine = create_async_engine(
    PROD_DATABASE_URL,
    pool_size=20,          # 基础连接数 (根据并发量调整)
    max_overflow=10,       # 最大溢出连接数
    pool_pre_ping=True,    # 连接健康检查
    pool_recycle=3600,     # 1小时回收 (Aurora 默认 8 小时超时)
    echo=False,            # 关闭 SQL 日志
)
```

### 2. 查询优化

```python
# 使用 selectinload 避免 N+1 查询
from sqlalchemy.orm import selectinload

async def get_user_with_jobs(user_id: int):
    async with async_session_factory() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.training_jobs))
            .where(User.id == user_id)
        )
        return result.scalar_one()
```

### 3. 批量操作

```python
# 批量插入检查点
async def bulk_create_checkpoints(checkpoints: List[dict]):
    async with async_session_factory() as session:
        session.add_all([Checkpoint(**c) for c in checkpoints])
        await session.commit()
```

---

## 监控指标

### 数据库性能指标

```yaml
metrics:
  - name: db_connections_active
    description: "活跃数据库连接数"
    threshold: 80% of pool_size

  - name: query_latency_p99
    description: "查询延迟 P99"
    threshold: < 100ms

  - name: slow_query_count
    description: "慢查询数量 (>1s)"
    threshold: < 10 per hour

  - name: deadlock_count
    description: "死锁次数"
    threshold: 0
```

---

## 附录

### A. Aurora MySQL 兼容性清单

✅ **完全兼容** (research.md Section 3):
- SQL 语法: Atomic DDL, Window Functions, CTE, JSON 增强
- Wire Protocol: 与 MySQL 8.0 相同
- SQLAlchemy 2.0+: aiomysql 驱动完全支持

⚠️ **需要注意**:
- Aurora 专有参数 (`aurora_*` 前缀) 在本地 MySQL 不支持
- 连接池需配置 `pool_pre_ping=True` 和 `pool_recycle=3600`

### B. 数据库规模预估

**单集群规模** (100 用户):
- `users`: 100 行
- `resource_quotas`: 20 行
- `datasets`: 500 行
- `training_jobs`: 10,000 行 (每用户 100 个任务)
- `checkpoints`: 100,000 行 (每任务 10 个检查点)
- `hyperpod_clusters`: 5 行

**存储预估**:
- 总行数: ~110,625 行
- 估算大小: ~2-5 GB (含索引)

**Aurora MySQL 实例推荐**:
- 开发/测试: db.r6g.large (2 vCPU, 16 GB RAM)
- 生产环境: db.r6g.xlarge (4 vCPU, 32 GB RAM) 起步

---

**文档版本**: v1.0
**最后更新**: 2026-01-03
**审核状态**: Phase 1 设计完成,待 Phase 2 实施验证
