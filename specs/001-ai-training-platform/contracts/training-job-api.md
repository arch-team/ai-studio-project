# API契约: 训练任务管理

**版本**: v1.0.0 | **日期**: 2025-12-23 | **特性分支**: `001-ai-training-platform`

## API概述

训练任务管理API提供了创建、管理和监控AI模型训练任务的能力。该API支持单机和分布式训练任务的提交、调度、状态监控、暂停、恢复和终止功能。

## 基本信息

- **基础路径**: `/api/v1/training-jobs`
- **认证**: Bearer Token (JWT)
- **内容类型**: application/json
- **响应格式**: JSON

## 端点概览

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | / | 创建新训练任务 | `training:create` |
| GET | / | 获取训练任务列表 | `training:read` |
| GET | /{id} | 获取特定训练任务详情 | `training:read` |
| PUT | /{id} | 更新特定训练任务 | `training:update` |
| DELETE | /{id} | 删除/取消训练任务 | `training:delete` |
| POST | /{id}/actions/start | 启动训练任务 | `training:execute` |
| POST | /{id}/actions/stop | 停止训练任务 | `training:execute` |
| POST | /{id}/actions/resume | 恢复训练任务 | `training:execute` |
| GET | /{id}/metrics | 获取训练指标 | `training:read` |
| GET | /{id}/logs | 获取训练日志 | `training:read` |
| GET | /{id}/checkpoints | 获取训练检查点列表 | `training:read` |

## 详细定义

### 创建训练任务 (POST /)

创建新的训练任务。任务将被提交到调度系统，根据配置的资源需求和优先级进行调度。

#### 请求体

```json
{
  "name": "bert-pretrain-job-001",
  "description": "BERT预训练任务",
  "job_type": "distributed",
  "framework": "pytorch",
  "distribution_strategy": "ddp",
  "num_nodes": 4,
  "gpus_per_node": 8,
  "container_image": "registry.example.com/pytorch:2.0-cuda11.8",
  "entrypoint": "python /workspace/train.py --config /workspace/configs/bert.yaml",
  "hyperparameters": {
    "learning_rate": 1e-5,
    "batch_size": 32,
    "epochs": 5,
    "gradient_accumulation_steps": 4
  },
  "resource_requirements": {
    "priority": "high",
    "gpu_type": "nvidia-a100-80g",
    "cpu_cores_per_gpu": 8,
    "memory_gb_per_gpu": 128
  },
  "dataset_versions": ["dataset-123/v1.2.0"],
  "project_id": "project-456",
  "timeout_hours": 72,
  "node_selectors": {
    "network": "high-speed-interconnect"
  },
  "environment_variables": {
    "NCCL_DEBUG": "INFO",
    "PYTHONUNBUFFERED": "1"
  },
  "tolerations": [
    {
      "key": "dedicated",
      "operator": "Equal",
      "value": "training",
      "effect": "NoSchedule"
    }
  ],
  "checkpoint_config": {
    "frequency_minutes": 30,
    "storage_type": "tiered"
  },
  "notifications": {
    "email": ["user@example.com"],
    "slack_channel": "#training-notifications"
  }
}
```

#### 响应 (201 Created)

```json
{
  "id": "job-789",
  "name": "bert-pretrain-job-001",
  "status": "pending",
  "created_at": "2025-12-23T08:15:30Z",
  "created_by": "user-123",
  "project_id": "project-456",
  "queue_position": 2,
  "estimated_start_time": "2025-12-23T09:00:00Z",
  "links": {
    "self": "/api/v1/training-jobs/job-789",
    "metrics": "/api/v1/training-jobs/job-789/metrics",
    "logs": "/api/v1/training-jobs/job-789/logs"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **409 Conflict**: 资源冲突，例如同名任务已存在
- **413 Request Entity Too Large**: 请求体过大
- **429 Too Many Requests**: 请求频率超限

### 获取训练任务列表 (GET /)

获取用户可访问的训练任务列表，支持分页和过滤。

#### 查询参数

- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `status`: 按状态过滤 (pending, running, completed, failed, stopped)
- `project_id`: 按项目ID过滤
- `user_id`: 按创建者ID过滤
- `from_date`: 从此日期开始的任务 (ISO 8601格式)
- `to_date`: 到此日期结束的任务 (ISO 8601格式)
- `name`: 按名称搜索（支持模糊匹配）
- `sort`: 排序字段 (created_at, name, status)
- `order`: 排序方向 (asc, desc)，默认desc

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "job-789",
      "name": "bert-pretrain-job-001",
      "status": "running",
      "job_type": "distributed",
      "framework": "pytorch",
      "created_at": "2025-12-23T08:15:30Z",
      "started_at": "2025-12-23T09:00:00Z",
      "project_id": "project-456",
      "created_by": "user-123",
      "progress": {
        "current_epoch": 2,
        "total_epochs": 5,
        "eta_seconds": 43200
      },
      "resource_usage": {
        "gpu_hours": 32,
        "cost_estimate_usd": 128.50
      },
      "links": {
        "self": "/api/v1/training-jobs/job-789"
      }
    },
    {
      "id": "job-788",
      "name": "resnet-finetune",
      "status": "completed",
      "job_type": "single",
      "framework": "tensorflow",
      "created_at": "2025-12-22T14:30:00Z",
      "started_at": "2025-12-22T14:35:00Z",
      "completed_at": "2025-12-22T16:45:00Z",
      "project_id": "project-456",
      "created_by": "user-123",
      "resource_usage": {
        "gpu_hours": 4.25,
        "cost_estimate_usd": 17.00
      },
      "links": {
        "self": "/api/v1/training-jobs/job-788"
      }
    }
  ],
  "pagination": {
    "total_items": 42,
    "total_pages": 3,
    "current_page": 1,
    "per_page": 20,
    "next": "/api/v1/training-jobs?page=2&per_page=20",
    "prev": null
  }
}
```

### 获取特定训练任务详情 (GET /{id})

获取单个训练任务的详细信息。

#### 路径参数

- `id`: 训练任务ID

#### 响应 (200 OK)

```json
{
  "id": "job-789",
  "name": "bert-pretrain-job-001",
  "description": "BERT预训练任务",
  "status": "running",
  "job_type": "distributed",
  "framework": "pytorch",
  "distribution_strategy": "ddp",
  "num_nodes": 4,
  "gpus_per_node": 8,
  "container_image": "registry.example.com/pytorch:2.0-cuda11.8",
  "entrypoint": "python /workspace/train.py --config /workspace/configs/bert.yaml",
  "hyperparameters": {
    "learning_rate": 1e-5,
    "batch_size": 32,
    "epochs": 5,
    "gradient_accumulation_steps": 4
  },
  "resource_requirements": {
    "priority": "high",
    "gpu_type": "nvidia-a100-80g",
    "cpu_cores_per_gpu": 8,
    "memory_gb_per_gpu": 128
  },
  "created_at": "2025-12-23T08:15:30Z",
  "updated_at": "2025-12-23T09:10:15Z",
  "started_at": "2025-12-23T09:00:00Z",
  "estimated_completion": "2025-12-25T09:00:00Z",
  "project_id": "project-456",
  "created_by": {
    "id": "user-123",
    "username": "zhang.wei",
    "email": "zhang.wei@example.com"
  },
  "dataset_versions": [
    {
      "id": "dataset-123/v1.2.0",
      "name": "ImageNet-2025",
      "version": "v1.2.0"
    }
  ],
  "metrics_summary": {
    "current_epoch": 2,
    "total_epochs": 5,
    "current_step": 12800,
    "loss": 0.0876,
    "accuracy": 0.9234,
    "learning_rate": 9.8e-6
  },
  "resource_usage": {
    "gpu_hours": 32,
    "cpu_hours": 256,
    "memory_gb_hours": 1024,
    "storage_gb_hours": 2048,
    "cost_estimate_usd": 128.50
  },
  "nodes": [
    {
      "name": "worker-0",
      "role": "chief",
      "status": "running",
      "gpu_utilization": 0.92,
      "memory_utilization": 0.85,
      "instance_type": "p4d.24xlarge"
    }
  ],
  "checkpoint_info": {
    "latest_checkpoint": {
      "id": "checkpoint-456",
      "step": 12800,
      "created_at": "2025-12-23T12:15:00Z",
      "storage_path": "s3://checkpoints/job-789/checkpoint-456",
      "size_bytes": 5368709120
    },
    "total_checkpoints": 3
  },
  "links": {
    "self": "/api/v1/training-jobs/job-789",
    "metrics": "/api/v1/training-jobs/job-789/metrics",
    "logs": "/api/v1/training-jobs/job-789/logs",
    "checkpoints": "/api/v1/training-jobs/job-789/checkpoints"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在

### 更新特定训练任务 (PUT /{id})

更新现有训练任务的配置。只能在任务启动前（pending状态）更新所有字段，已启动的任务只能更新部分字段（如名称、描述、超时时间）。

#### 路径参数

- `id`: 训练任务ID

#### 请求体

```json
{
  "name": "bert-pretrain-job-001-updated",
  "description": "更新后的BERT预训练任务描述",
  "hyperparameters": {
    "learning_rate": 2e-5,
    "batch_size": 64
  },
  "timeout_hours": 96,
  "notifications": {
    "email": ["user@example.com", "team-lead@example.com"]
  }
}
```

#### 响应 (200 OK)

```json
{
  "id": "job-789",
  "name": "bert-pretrain-job-001-updated",
  "status": "pending",
  "updated_at": "2025-12-23T10:30:15Z",
  "links": {
    "self": "/api/v1/training-jobs/job-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足，或尝试更新运行中任务的受限字段
- **404 Not Found**: 指定的训练任务不存在
- **409 Conflict**: 资源冲突，例如同名任务已存在

### 删除/取消训练任务 (DELETE /{id})

删除或取消指定的训练任务。pending状态的任务将被删除，running状态的任务将被取消并停止。completed、failed或stopped状态的任务将标记为删除，但实际数据可能根据保留策略延迟删除。

#### 路径参数

- `id`: 训练任务ID

#### 查询参数

- `force`: 布尔值，是否强制删除（默认false）
- `delete_checkpoints`: 布尔值，是否同时删除任务的检查点（默认false）
- `delete_metrics`: 布尔值，是否同时删除任务的指标数据（默认false）

#### 响应 (204 No Content)

成功删除后无响应体

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在
- **409 Conflict**: 任务处于无法删除的状态

### 启动训练任务 (POST /{id}/actions/start)

启动已创建但尚未启动的训练任务。

#### 路径参数

- `id`: 训练任务ID

#### 请求体

```json
{
  "priority_override": "high",
  "node_selectors_override": {
    "network": "ultra-high-speed-interconnect"
  }
}
```

#### 响应 (202 Accepted)

```json
{
  "id": "job-789",
  "name": "bert-pretrain-job-001",
  "status": "pending",
  "queue_position": 1,
  "estimated_start_time": "2025-12-23T10:45:00Z",
  "links": {
    "self": "/api/v1/training-jobs/job-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在
- **409 Conflict**: 任务状态不允许启动

### 停止训练任务 (POST /{id}/actions/stop)

停止正在运行中的训练任务。

#### 路径参数

- `id`: 训练任务ID

#### 请求体

```json
{
  "reason": "模型收敛已达到目标精度",
  "create_final_checkpoint": true,
  "grace_period_seconds": 300
}
```

#### 响应 (202 Accepted)

```json
{
  "id": "job-789",
  "name": "bert-pretrain-job-001",
  "status": "stopping",
  "estimated_stop_time": "2025-12-23T10:50:00Z",
  "links": {
    "self": "/api/v1/training-jobs/job-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在
- **409 Conflict**: 任务状态不允许停止

### 恢复训练任务 (POST /{id}/actions/resume)

从检查点恢复已停止的训练任务。

#### 路径参数

- `id`: 训练任务ID

#### 请求体

```json
{
  "checkpoint_id": "checkpoint-456",
  "hyperparameters_override": {
    "learning_rate": 5e-6
  },
  "resource_requirements_override": {
    "num_nodes": 2
  }
}
```

#### 响应 (202 Accepted)

```json
{
  "id": "job-790",
  "name": "bert-pretrain-job-001-resumed",
  "status": "pending",
  "original_job_id": "job-789",
  "checkpoint_id": "checkpoint-456",
  "queue_position": 3,
  "estimated_start_time": "2025-12-23T11:00:00Z",
  "links": {
    "self": "/api/v1/training-jobs/job-790",
    "original_job": "/api/v1/training-jobs/job-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务或检查点不存在
- **409 Conflict**: 任务状态不允许恢复

### 获取训练指标 (GET /{id}/metrics)

获取训练任务的详细指标数据，支持时间范围和聚合函数。

#### 路径参数

- `id`: 训练任务ID

#### 查询参数

- `metric_names`: 指标名称列表，用逗号分隔（例如"loss,accuracy,learning_rate"）
- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `interval`: 聚合间隔（例如"1m"，"5m"，"1h"），默认为原始粒度
- `aggregation`: 聚合函数（例如"avg"，"min"，"max"），默认为"avg"
- `step_start`: 开始训练步骤
- `step_end`: 结束训练步骤

#### 响应 (200 OK)

```json
{
  "job_id": "job-789",
  "metrics": {
    "loss": {
      "times": [
        "2025-12-23T09:00:00Z",
        "2025-12-23T09:30:00Z",
        "2025-12-23T10:00:00Z"
      ],
      "steps": [0, 6400, 12800],
      "values": [0.9234, 0.3456, 0.0876],
      "metadata": {
        "description": "训练损失函数",
        "unit": ""
      }
    },
    "accuracy": {
      "times": [
        "2025-12-23T09:00:00Z",
        "2025-12-23T09:30:00Z",
        "2025-12-23T10:00:00Z"
      ],
      "steps": [0, 6400, 12800],
      "values": [0.1023, 0.7456, 0.9234],
      "metadata": {
        "description": "训练准确率",
        "unit": "%"
      }
    },
    "learning_rate": {
      "times": [
        "2025-12-23T09:00:00Z",
        "2025-12-23T09:30:00Z",
        "2025-12-23T10:00:00Z"
      ],
      "steps": [0, 6400, 12800],
      "values": [1e-5, 9.9e-6, 9.8e-6],
      "metadata": {
        "description": "学习率",
        "unit": ""
      }
    }
  },
  "links": {
    "self": "/api/v1/training-jobs/job-789/metrics",
    "job": "/api/v1/training-jobs/job-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在

### 获取训练日志 (GET /{id}/logs)

获取训练任务的日志数据。

#### 路径参数

- `id`: 训练任务ID

#### 查询参数

- `node`: 节点名称（例如"worker-0"），默认为所有节点
- `pod`: Pod名称，默认为所有Pod
- `container`: 容器名称，默认为主容器
- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `limit`: 返回的最大行数，默认为1000
- `filter`: 日志过滤条件（例如"ERROR"，"WARNING"）
- `tail`: 返回最后N行，与limit互斥
- `follow`: 是否持续获取新日志（布尔值），默认为false

#### 响应 (200 OK)

```json
{
  "job_id": "job-789",
  "node": "worker-0",
  "pod": "bert-pretrain-job-001-worker-0",
  "logs": [
    {
      "timestamp": "2025-12-23T09:00:05Z",
      "level": "INFO",
      "message": "Starting training with 4 nodes, 8 GPUs per node"
    },
    {
      "timestamp": "2025-12-23T09:00:10Z",
      "level": "INFO",
      "message": "Using DDP for distributed training"
    },
    {
      "timestamp": "2025-12-23T09:01:00Z",
      "level": "INFO",
      "message": "Epoch 1/5, Step 100/32000, Loss: 0.8765, Accuracy: 0.2345"
    }
  ],
  "continuation_token": "eyJsYXN0VGltZSI6IjIwMjUtMTItMjNUMDk6MDE6MDBaIn0=",
  "links": {
    "self": "/api/v1/training-jobs/job-789/logs",
    "job": "/api/v1/training-jobs/job-789",
    "next": "/api/v1/training-jobs/job-789/logs?continuation_token=eyJsYXN0VGltZSI6IjIwMjUtMTItMjNUMDk6MDE6MDBaIn0="
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在

### 获取训练检查点列表 (GET /{id}/checkpoints)

获取训练任务的检查点列表。

#### 路径参数

- `id`: 训练任务ID

#### 查询参数

- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `sort`: 排序字段 (created_at, step)，默认为created_at
- `order`: 排序方向 (asc, desc)，默认desc

#### 响应 (200 OK)

```json
{
  "job_id": "job-789",
  "items": [
    {
      "id": "checkpoint-456",
      "step": 12800,
      "epoch": 2,
      "created_at": "2025-12-23T12:15:00Z",
      "storage_path": "s3://checkpoints/job-789/checkpoint-456",
      "storage_type": "s3",
      "size_bytes": 5368709120,
      "metrics": {
        "loss": 0.0876,
        "accuracy": 0.9234
      },
      "metadata": {
        "is_best": true,
        "checkpoint_type": "regular"
      },
      "links": {
        "download": "/api/v1/training-jobs/job-789/checkpoints/checkpoint-456/download"
      }
    },
    {
      "id": "checkpoint-455",
      "step": 6400,
      "epoch": 1,
      "created_at": "2025-12-23T10:45:00Z",
      "storage_path": "s3://checkpoints/job-789/checkpoint-455",
      "storage_type": "s3",
      "size_bytes": 5368709120,
      "metrics": {
        "loss": 0.3456,
        "accuracy": 0.7456
      },
      "metadata": {
        "is_best": false,
        "checkpoint_type": "regular"
      },
      "links": {
        "download": "/api/v1/training-jobs/job-789/checkpoints/checkpoint-455/download"
      }
    }
  ],
  "pagination": {
    "total_items": 3,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  },
  "links": {
    "self": "/api/v1/training-jobs/job-789/checkpoints",
    "job": "/api/v1/training-jobs/job-789"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在

## 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 202 | 请求已接受，但处理尚未完成 |
| 204 | 请求成功，无返回内容 |
| 400 | 请求参数无效 |
| 401 | 未提供认证或认证无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 413 | 请求体过大 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

## 错误响应格式

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "训练任务不存在",
    "details": "找不到ID为job-789的训练任务",
    "request_id": "req-abc-123"
  }
}
```

## 速率限制

API实施速率限制以防止滥用。限制信息通过HTTP响应头提供：

- `X-RateLimit-Limit`: 时间窗口内允许的请求数
- `X-RateLimit-Remaining`: 当前时间窗口内剩余的请求数
- `X-RateLimit-Reset`: 当前时间窗口重置的时间（Unix时间戳）

超过限制时返回429状态码。

## 版本控制

API使用语义化版本控制，格式为v{major}.{minor}.{patch}。主要版本号变更表示不向后兼容的更改，客户端应该通过API基础路径中的版本号指定使用的API版本。

## 安全要求

1. 所有API请求必须使用HTTPS
2. 认证使用Bearer Token (JWT)
3. 令牌必须包含适当的权限范围
4. 令牌过期时间不超过12小时
5. 敏感数据（如API密钥、密码）不会记录在日志中