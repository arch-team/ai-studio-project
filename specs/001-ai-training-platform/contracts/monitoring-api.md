# API契约: 监控服务

**版本**: v1.0.0 | **日期**: 2025-12-23 | **特性分支**: `001-ai-training-platform`

## API概述

监控服务API提供了企业级AI训练平台的实时和历史监控功能，支持训练任务、资源使用、系统健康状态的监控和告警管理。

## 基本信息

- **基础路径**: `/api/v1/monitoring`
- **认证**: Bearer Token (JWT)
- **内容类型**: application/json
- **响应格式**: JSON

## 端点概览

### 指标查询

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /metrics | 获取平台指标数据 | `monitoring:read` |
| POST | /metrics/query | 执行PromQL查询 | `monitoring:read` |
| GET | /metrics/training-jobs/{job_id} | 获取特定训练任务的指标 | `monitoring:read` |
| GET | /metrics/nodes/{node_id} | 获取特定节点的指标 | `monitoring:read` |
| GET | /metrics/dashboards | 获取仪表板列表 | `monitoring:read` |
| GET | /metrics/dashboards/{id} | 获取特定仪表板 | `monitoring:read` |

### 日志管理

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /logs | 获取系统日志 | `monitoring:read` |
| GET | /logs/training-jobs/{job_id} | 获取特定训练任务的日志 | `monitoring:read` |
| GET | /logs/nodes/{node_id} | 获取特定节点的日志 | `monitoring:read` |
| POST | /logs/search | 搜索日志 | `monitoring:read` |

### 告警管理

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /alerts | 获取告警列表 | `monitoring:read` |
| GET | /alerts/{id} | 获取特定告警详情 | `monitoring:read` |
| PUT | /alerts/{id}/actions/acknowledge | 确认告警 | `monitoring:write` |
| PUT | /alerts/{id}/actions/resolve | 解决告警 | `monitoring:write` |
| GET | /alert-rules | 获取告警规则列表 | `monitoring:read` |
| POST | /alert-rules | 创建告警规则 | `monitoring:admin` |
| GET | /alert-rules/{id} | 获取特定告警规则详情 | `monitoring:read` |
| PUT | /alert-rules/{id} | 更新特定告警规则 | `monitoring:admin` |
| DELETE | /alert-rules/{id} | 删除告警规则 | `monitoring:admin` |

### 健康检查与系统状态

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /health | 获取系统健康状态 | `monitoring:read` |
| GET | /health/components | 获取各组件健康状态 | `monitoring:read` |
| GET | /health/nodes | 获取节点健康状态 | `monitoring:read` |
| GET | /status/incidents | 获取系统事件历史 | `monitoring:read` |
| GET | /status/maintenance | 获取维护计划 | `monitoring:read` |

### 通知配置

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /notifications/channels | 获取通知渠道列表 | `monitoring:read` |
| POST | /notifications/channels | 创建新通知渠道 | `monitoring:admin` |
| GET | /notifications/channels/{id} | 获取特定通知渠道详情 | `monitoring:read` |
| PUT | /notifications/channels/{id} | 更新特定通知渠道 | `monitoring:admin` |
| DELETE | /notifications/channels/{id} | 删除通知渠道 | `monitoring:admin` |
| GET | /notifications/subscriptions | 获取通知订阅列表 | `monitoring:read` |
| POST | /notifications/subscriptions | 创建新通知订阅 | `monitoring:write` |
| GET | /notifications/subscriptions/{id} | 获取特定通知订阅详情 | `monitoring:read` |
| PUT | /notifications/subscriptions/{id} | 更新特定通知订阅 | `monitoring:write` |
| DELETE | /notifications/subscriptions/{id} | 删除通知订阅 | `monitoring:write` |

## 详细定义

### 获取平台指标数据 (GET /metrics)

获取平台级别的关键指标数据。

#### 查询参数

- `metric_names`: 指标名称列表，用逗号分隔 (例如 "gpu_utilization,job_count,queue_depth")
- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `interval`: 数据聚合间隔，例如"5m", "1h", "1d"，默认为"5m"
- `aggregation`: 聚合函数，例如"avg", "max", "min", "sum"，默认为"avg"

#### 响应 (200 OK)

```json
{
  "start_time": "2025-12-23T00:00:00Z",
  "end_time": "2025-12-23T12:00:00Z",
  "interval": "1h",
  "time_points": [
    "2025-12-23T00:00:00Z",
    "2025-12-23T01:00:00Z",
    "2025-12-23T02:00:00Z",
    "...",
    "2025-12-23T12:00:00Z"
  ],
  "metrics": {
    "gpu_utilization": {
      "values": [0.82, 0.84, 0.85, "...", 0.88],
      "unit": "percentage",
      "description": "GPU利用率"
    },
    "job_count": {
      "values": [120, 122, 125, "...", 132],
      "unit": "count",
      "description": "运行中的训练任务数量"
    },
    "queue_depth": {
      "values": [15, 14, 16, "...", 10],
      "unit": "count",
      "description": "等待中的训练任务数量"
    }
  },
  "links": {
    "self": "/api/v1/monitoring/metrics?metric_names=gpu_utilization,job_count,queue_depth&interval=1h",
    "query": "/api/v1/monitoring/metrics/query"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 执行PromQL查询 (POST /metrics/query)

执行自定义PromQL查询来获取指标数据。

#### 请求体

```json
{
  "query": "sum(rate(training_job_gpu_hours_total[1h])) by (project_id)",
  "start_time": "2025-12-23T00:00:00Z",
  "end_time": "2025-12-23T12:00:00Z",
  "step": "1h"
}
```

#### 响应 (200 OK)

```json
{
  "query": "sum(rate(training_job_gpu_hours_total[1h])) by (project_id)",
  "result_type": "matrix",
  "result": [
    {
      "metric": {
        "project_id": "project-456"
      },
      "values": [
        [1735129200, "45.2"],
        [1735132800, "46.8"],
        [1735136400, "48.5"],
        "...",
        [1735171200, "52.3"]
      ]
    },
    {
      "metric": {
        "project_id": "project-457"
      },
      "values": [
        [1735129200, "22.1"],
        [1735132800, "23.4"],
        [1735136400, "24.2"],
        "...",
        [1735171200, "26.7"]
      ]
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/metrics/query"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效或PromQL查询语法错误
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **413 Request Entity Too Large**: 查询结果过大
- **504 Gateway Timeout**: 查询超时

### 获取特定训练任务的指标 (GET /metrics/training-jobs/{job_id})

获取单个训练任务的详细指标数据。

#### 路径参数

- `job_id`: 训练任务ID

#### 查询参数

- `metric_names`: 指标名称列表，用逗号分隔 (例如 "gpu_utilization,gpu_memory_used,loss,accuracy")
- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `interval`: 数据聚合间隔，默认为"1m"
- `include_training_metrics`: 布尔值，是否包含训练特定指标（例如loss, accuracy），默认为true

#### 响应 (200 OK)

```json
{
  "job_id": "job-789",
  "job_name": "bert-pretrain-job-001",
  "start_time": "2025-12-23T09:00:00Z",
  "end_time": "2025-12-23T12:00:00Z",
  "interval": "10m",
  "time_points": [
    "2025-12-23T09:00:00Z",
    "2025-12-23T09:10:00Z",
    "2025-12-23T09:20:00Z",
    "...",
    "2025-12-23T12:00:00Z"
  ],
  "system_metrics": {
    "gpu_utilization": {
      "values": [0.75, 0.88, 0.92, "...", 0.90],
      "unit": "percentage",
      "description": "GPU利用率"
    },
    "gpu_memory_used": {
      "values": [68.5, 72.3, 74.1, "...", 73.8],
      "unit": "GB",
      "description": "GPU内存使用量"
    },
    "gpu_power": {
      "values": [285, 310, 315, "...", 312],
      "unit": "W",
      "description": "GPU功耗"
    },
    "cpu_utilization": {
      "values": [65, 68, 70, "...", 69],
      "unit": "percentage",
      "description": "CPU利用率"
    },
    "memory_used": {
      "values": [820, 845, 860, "...", 855],
      "unit": "GB",
      "description": "系统内存使用量"
    },
    "network_throughput": {
      "values": [8.2, 8.5, 8.7, "...", 8.6],
      "unit": "GB/s",
      "description": "网络吞吐量"
    }
  },
  "training_metrics": {
    "loss": {
      "values": [0.9234, 0.8765, 0.8234, "...", 0.2345],
      "unit": "",
      "description": "训练损失函数值"
    },
    "accuracy": {
      "values": [0.1023, 0.2356, 0.3456, "...", 0.8765],
      "unit": "",
      "description": "训练准确率"
    },
    "learning_rate": {
      "values": [1e-5, 9.9e-6, 9.8e-6, "...", 9.5e-6],
      "unit": "",
      "description": "学习率"
    },
    "throughput": {
      "values": [1256, 1320, 1345, "...", 1352],
      "unit": "samples/s",
      "description": "训练吞吐量"
    }
  },
  "checkpoints": [
    {
      "timestamp": "2025-12-23T09:30:00Z",
      "step": 6400,
      "metrics": {
        "loss": 0.3456,
        "accuracy": 0.7456
      }
    },
    {
      "timestamp": "2025-12-23T12:15:00Z",
      "step": 12800,
      "metrics": {
        "loss": 0.0876,
        "accuracy": 0.9234
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/metrics/training-jobs/job-789",
    "job": "/api/v1/training-jobs/job-789",
    "logs": "/api/v1/monitoring/logs/training-jobs/job-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在

### 获取特定节点的指标 (GET /metrics/nodes/{node_id})

获取单个计算节点的详细指标数据。

#### 路径参数

- `node_id`: 节点ID

#### 查询参数

- `metric_names`: 指标名称列表，用逗号分隔
- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `interval`: 数据聚合间隔，默认为"1m"

#### 响应 (200 OK)

```json
{
  "node_id": "node-001",
  "node_name": "worker-0",
  "cluster_id": "cluster-001",
  "start_time": "2025-12-23T09:00:00Z",
  "end_time": "2025-12-23T12:00:00Z",
  "interval": "10m",
  "time_points": [
    "2025-12-23T09:00:00Z",
    "2025-12-23T09:10:00Z",
    "2025-12-23T09:20:00Z",
    "...",
    "2025-12-23T12:00:00Z"
  ],
  "metrics": {
    "gpu_utilization": {
      "values": [0.92, 0.94, 0.95, "...", 0.93],
      "unit": "percentage",
      "description": "GPU利用率"
    },
    "gpu_memory_used": {
      "values": [74.2, 75.6, 76.8, "...", 76.2],
      "unit": "GB",
      "description": "GPU内存使用量"
    },
    "gpu_temperature": {
      "values": [72, 74, 75, "...", 73],
      "unit": "°C",
      "description": "GPU温度"
    },
    "cpu_utilization": {
      "values": [70, 72, 73, "...", 71],
      "unit": "percentage",
      "description": "CPU利用率"
    },
    "memory_used": {
      "values": [920, 935, 945, "...", 940],
      "unit": "GB",
      "description": "系统内存使用量"
    },
    "disk_used": {
      "values": [1250, 1260, 1270, "...", 1280],
      "unit": "GB",
      "description": "磁盘使用量"
    },
    "network_rx": {
      "values": [4.2, 4.3, 4.4, "...", 4.3],
      "unit": "GB/s",
      "description": "网络接收速率"
    },
    "network_tx": {
      "values": [3.8, 3.9, 4.0, "...", 3.9],
      "unit": "GB/s",
      "description": "网络发送速率"
    }
  },
  "active_jobs": [
    {
      "job_id": "job-789",
      "job_name": "bert-pretrain-job-001",
      "user": "zhang.wei",
      "gpu_count": 8
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/metrics/nodes/node-001",
    "cluster": "/api/v1/resources/clusters/cluster-001",
    "logs": "/api/v1/monitoring/logs/nodes/node-001",
    "health": "/api/v1/monitoring/health/nodes/node-001"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的节点不存在

### 获取仪表板列表 (GET /metrics/dashboards)

获取可用的监控仪表板列表。

#### 查询参数

- `category`: 按类别过滤 (例如 "system", "training", "resource")
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "dashboard-001",
      "name": "平台概览仪表板",
      "description": "显示平台级别的关键指标和健康状态",
      "category": "system",
      "created_at": "2025-11-01T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-01T00:00:00Z",
      "panels_count": 12,
      "favorite_count": 45,
      "is_default": true,
      "links": {
        "self": "/api/v1/monitoring/metrics/dashboards/dashboard-001",
        "view": "/dashboards/system/overview"
      }
    },
    {
      "id": "dashboard-002",
      "name": "训练性能仪表板",
      "description": "用于分析训练任务性能的详细指标",
      "category": "training",
      "created_at": "2025-11-05T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-05T00:00:00Z",
      "panels_count": 10,
      "favorite_count": 38,
      "is_default": false,
      "links": {
        "self": "/api/v1/monitoring/metrics/dashboards/dashboard-002",
        "view": "/dashboards/training/performance"
      }
    },
    {
      "id": "dashboard-003",
      "name": "资源使用仪表板",
      "description": "跟踪资源使用情况和成本分析",
      "category": "resource",
      "created_at": "2025-11-10T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-10T00:00:00Z",
      "panels_count": 8,
      "favorite_count": 32,
      "is_default": false,
      "links": {
        "self": "/api/v1/monitoring/metrics/dashboards/dashboard-003",
        "view": "/dashboards/resource/usage"
      }
    }
  ],
  "pagination": {
    "total_items": 12,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  }
}
```

### 获取特定仪表板 (GET /metrics/dashboards/{id})

获取单个仪表板的详细配置和面板列表。

#### 路径参数

- `id`: 仪表板ID

#### 响应 (200 OK)

```json
{
  "id": "dashboard-001",
  "name": "平台概览仪表板",
  "description": "显示平台级别的关键指标和健康状态",
  "category": "system",
  "created_at": "2025-11-01T00:00:00Z",
  "created_by": {
    "id": "user-123",
    "username": "admin",
    "email": "admin@example.com"
  },
  "updated_at": "2025-12-01T00:00:00Z",
  "is_default": true,
  "refresh_interval_seconds": 60,
  "time_range": {
    "default": "last_24_hours",
    "options": ["last_1_hour", "last_6_hours", "last_24_hours", "last_7_days", "custom"]
  },
  "panels": [
    {
      "id": "panel-001",
      "title": "GPU利用率",
      "type": "graph",
      "position": {
        "x": 0,
        "y": 0,
        "width": 8,
        "height": 6
      },
      "datasource": "prometheus",
      "targets": [
        {
          "expr": "avg(gpu_utilization)",
          "legend": "平均GPU利用率"
        },
        {
          "expr": "max(gpu_utilization)",
          "legend": "最大GPU利用率"
        }
      ],
      "visualization": {
        "type": "line",
        "options": {
          "fill": 1,
          "lineWidth": 2,
          "points": false,
          "thresholds": [
            {
              "value": 0.9,
              "color": "red",
              "line": true
            }
          ]
        }
      }
    },
    {
      "id": "panel-002",
      "title": "活跃训练任务",
      "type": "stat",
      "position": {
        "x": 8,
        "y": 0,
        "width": 4,
        "height": 3
      },
      "datasource": "prometheus",
      "targets": [
        {
          "expr": "count(job_status{status='running'})",
          "instant": true
        }
      ],
      "visualization": {
        "type": "number",
        "options": {
          "color": {
            "mode": "thresholds"
          },
          "thresholds": [
            {
              "value": 100,
              "color": "green"
            },
            {
              "value": 150,
              "color": "yellow"
            },
            {
              "value": 200,
              "color": "red"
            }
          ]
        }
      }
    }
  ],
  "variables": [
    {
      "name": "cluster",
      "label": "集群",
      "type": "query",
      "query": "label_values(cluster)",
      "multi": true,
      "default": "all"
    },
    {
      "name": "interval",
      "label": "间隔",
      "type": "custom",
      "options": ["1m", "5m", "10m", "30m", "1h"],
      "default": "5m"
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/metrics/dashboards/dashboard-001",
    "view": "/dashboards/system/overview"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的仪表板不存在

### 获取系统日志 (GET /logs)

获取系统级别的日志数据。

#### 查询参数

- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `levels`: 日志级别列表，用逗号分隔 (例如 "error,warn,info")
- `sources`: 日志源列表，用逗号分隔 (例如 "scheduler,monitor,node-controller")
- `limit`: 返回的最大日志条数，默认为1000
- `offset`: 起始偏移量，用于分页
- `sort`: 排序方向 (asc, desc)，默认为desc
- `filter`: 日志内容过滤表达式

#### 响应 (200 OK)

```json
{
  "start_time": "2025-12-23T00:00:00Z",
  "end_time": "2025-12-23T12:00:00Z",
  "filter_applied": {
    "levels": ["error", "warn", "info"],
    "sources": ["scheduler", "monitor", "node-controller"]
  },
  "total_count": 1245,
  "returned_count": 1000,
  "items": [
    {
      "id": "log-12345",
      "timestamp": "2025-12-23T11:45:32Z",
      "level": "error",
      "source": "node-controller",
      "node_id": "node-005",
      "message": "节点连接超时，尝试重新连接",
      "details": {
        "error_code": "NODE_TIMEOUT",
        "attempts": 3,
        "last_seen": "2025-12-23T11:40:12Z"
      }
    },
    {
      "id": "log-12344",
      "timestamp": "2025-12-23T11:42:18Z",
      "level": "warn",
      "source": "scheduler",
      "message": "任务调度延迟超过阈值",
      "details": {
        "job_id": "job-790",
        "delay_seconds": 65,
        "threshold_seconds": 60
      }
    },
    {
      "id": "log-12343",
      "timestamp": "2025-12-23T11:38:45Z",
      "level": "info",
      "source": "monitor",
      "message": "系统负载监控周期完成",
      "details": {
        "duration_ms": 1250,
        "metrics_collected": 1500
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/logs?limit=1000&offset=0",
    "next": "/api/v1/monitoring/logs?limit=1000&offset=1000",
    "search": "/api/v1/monitoring/logs/search"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 获取特定训练任务的日志 (GET /logs/training-jobs/{job_id})

获取单个训练任务的详细日志数据。

#### 路径参数

- `job_id`: 训练任务ID

#### 查询参数

- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `levels`: 日志级别列表，用逗号分隔
- `node`: 节点名称，用于过滤特定节点的日志
- `container`: 容器名称，用于过滤特定容器的日志
- `limit`: 返回的最大日志条数，默认为1000
- `offset`: 起始偏移量，用于分页
- `sort`: 排序方向 (asc, desc)，默认为asc
- `filter`: 日志内容过滤表达式
- `follow`: 布尔值，是否持续获取新日志，默认为false

#### 响应 (200 OK)

```json
{
  "job_id": "job-789",
  "job_name": "bert-pretrain-job-001",
  "start_time": "2025-12-23T09:00:00Z",
  "end_time": "2025-12-23T12:00:00Z",
  "filter_applied": {
    "levels": ["error", "warn", "info"],
    "node": "worker-0",
    "container": "training"
  },
  "total_count": 3280,
  "returned_count": 1000,
  "items": [
    {
      "id": "job-log-56789",
      "timestamp": "2025-12-23T09:00:05.123Z",
      "level": "info",
      "node": "worker-0",
      "container": "training",
      "message": "Starting training with 4 nodes, 8 GPUs per node"
    },
    {
      "id": "job-log-56790",
      "timestamp": "2025-12-23T09:00:10.456Z",
      "level": "info",
      "node": "worker-0",
      "container": "training",
      "message": "Using DDP for distributed training"
    },
    {
      "id": "job-log-56791",
      "timestamp": "2025-12-23T09:01:00.789Z",
      "level": "info",
      "node": "worker-0",
      "container": "training",
      "message": "Epoch 1/5, Step 100/32000, Loss: 0.8765, Accuracy: 0.2345"
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/logs/training-jobs/job-789?limit=1000&offset=0",
    "next": "/api/v1/monitoring/logs/training-jobs/job-789?limit=1000&offset=1000",
    "job": "/api/v1/training-jobs/job-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的训练任务不存在

### 获取特定节点的日志 (GET /logs/nodes/{node_id})

获取单个计算节点的系统日志数据。

#### 路径参数

- `node_id`: 节点ID

#### 查询参数

- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `levels`: 日志级别列表，用逗号分隔
- `components`: 组件名称列表，用逗号分隔
- `limit`: 返回的最大日志条数，默认为1000
- `offset`: 起始偏移量，用于分页
- `sort`: 排序方向 (asc, desc)，默认为desc
- `filter`: 日志内容过滤表达式

#### 响应 (200 OK)

```json
{
  "node_id": "node-001",
  "node_name": "worker-0",
  "cluster_id": "cluster-001",
  "start_time": "2025-12-23T00:00:00Z",
  "end_time": "2025-12-23T12:00:00Z",
  "filter_applied": {
    "levels": ["error", "warn", "info"],
    "components": ["kubelet", "containerd", "nvidia-driver"]
  },
  "total_count": 2150,
  "returned_count": 1000,
  "items": [
    {
      "id": "node-log-45678",
      "timestamp": "2025-12-23T11:55:12.345Z",
      "level": "info",
      "component": "kubelet",
      "message": "Successfully started container training for pod bert-pretrain-job-001-worker-0"
    },
    {
      "id": "node-log-45677",
      "timestamp": "2025-12-23T11:54:58.765Z",
      "level": "info",
      "component": "nvidia-driver",
      "message": "NVIDIA MIG mode configured successfully"
    },
    {
      "id": "node-log-45676",
      "timestamp": "2025-12-23T11:53:45.123Z",
      "level": "info",
      "component": "containerd",
      "message": "Successfully pulled image registry.example.com/pytorch:2.0-cuda11.8"
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/logs/nodes/node-001?limit=1000&offset=0",
    "next": "/api/v1/monitoring/logs/nodes/node-001?limit=1000&offset=1000",
    "node": "/api/v1/resources/clusters/cluster-001/nodes/node-001"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的节点不存在

### 搜索日志 (POST /logs/search)

执行高级日志搜索查询。

#### 请求体

```json
{
  "query": "error AND (\"out of memory\" OR OOM)",
  "time_range": {
    "start": "2025-12-20T00:00:00Z",
    "end": "2025-12-23T23:59:59Z"
  },
  "filters": {
    "levels": ["error", "fatal"],
    "sources": ["training-job"],
    "job_ids": ["job-780", "job-785", "job-789"],
    "node_ids": ["node-001", "node-002"]
  },
  "aggregations": [
    {
      "field": "source",
      "type": "terms",
      "size": 10
    },
    {
      "field": "timestamp",
      "type": "date_histogram",
      "interval": "1h"
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0
  },
  "sort": {
    "field": "timestamp",
    "order": "desc"
  }
}
```

#### 响应 (200 OK)

```json
{
  "query": "error AND (\"out of memory\" OR OOM)",
  "time_range": {
    "start": "2025-12-20T00:00:00Z",
    "end": "2025-12-23T23:59:59Z"
  },
  "total_hits": 28,
  "execution_time_ms": 250,
  "aggregations": {
    "source": [
      {
        "key": "training-job",
        "doc_count": 25
      },
      {
        "key": "node-controller",
        "doc_count": 3
      }
    ],
    "timestamp": [
      {
        "key": 1735129200000,
        "key_as_string": "2025-12-20T00:00:00Z",
        "doc_count": 5
      },
      {
        "key": 1735215600000,
        "key_as_string": "2025-12-21T00:00:00Z",
        "doc_count": 8
      },
      {
        "key": 1735302000000,
        "key_as_string": "2025-12-22T00:00:00Z",
        "doc_count": 6
      },
      {
        "key": 1735388400000,
        "key_as_string": "2025-12-23T00:00:00Z",
        "doc_count": 9
      }
    ]
  },
  "hits": [
    {
      "id": "log-12340",
      "timestamp": "2025-12-23T10:15:32Z",
      "level": "error",
      "source": "training-job",
      "job_id": "job-789",
      "node_id": "node-001",
      "message": "训练进程异常终止: CUDA out of memory",
      "details": {
        "error_code": "OOM",
        "gpu_id": 0,
        "allocated_memory": 79.2,
        "total_memory": 80.0
      }
    },
    {
      "id": "log-12245",
      "timestamp": "2025-12-23T08:45:18Z",
      "level": "error",
      "source": "training-job",
      "job_id": "job-785",
      "node_id": "node-002",
      "message": "训练进程异常终止: CUDA out of memory",
      "details": {
        "error_code": "OOM",
        "gpu_id": 3,
        "allocated_memory": 79.8,
        "total_memory": 80.0
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/logs/search",
    "next": "/api/v1/monitoring/logs/search?query=error+AND+%28%22out+of+memory%22+OR+OOM%29&offset=100&limit=100"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效或查询语法错误
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **413 Request Entity Too Large**: 查询结果过大
- **504 Gateway Timeout**: 查询超时

### 获取告警列表 (GET /alerts)

获取系统告警的列表。

#### 查询参数

- `status`: 按状态过滤 (例如 "firing", "resolved", "acknowledged")
- `severity`: 按严重程度过滤 (例如 "critical", "high", "medium", "low")
- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `source`: 告警源
- `labels`: 告警标签过滤条件
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `sort`: 排序字段 (例如 "start_time", "severity")
- `order`: 排序方向 (asc, desc)，默认为desc

#### 响应 (200 OK)

```json
{
  "summary": {
    "total": 15,
    "by_status": {
      "firing": 5,
      "acknowledged": 3,
      "resolved": 7
    },
    "by_severity": {
      "critical": 2,
      "high": 3,
      "medium": 5,
      "low": 5
    }
  },
  "items": [
    {
      "id": "alert-12345",
      "name": "NodeGPUHighTemperature",
      "summary": "节点GPU温度过高",
      "description": "节点worker-2上的GPU 5温度已经超过阈值85°C达到92°C",
      "severity": "high",
      "status": "firing",
      "start_time": "2025-12-23T10:15:00Z",
      "end_time": null,
      "source": "prometheus-alertmanager",
      "labels": {
        "cluster": "cluster-001",
        "node": "node-003",
        "gpu_id": "5",
        "environment": "production"
      },
      "annotations": {
        "temperature": "92",
        "threshold": "85",
        "runbook_url": "https://docs.example.com/runbooks/node-gpu-high-temperature"
      },
      "fingerprint": "a1b2c3d4e5f6g7h8",
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12345",
        "source": "/api/v1/resources/clusters/cluster-001/nodes/node-003",
        "rule": "/api/v1/monitoring/alert-rules/rule-789"
      }
    },
    {
      "id": "alert-12344",
      "name": "JobFailureRateHigh",
      "summary": "训练任务失败率过高",
      "description": "最近30分钟内训练任务失败率达到15%，超过阈值10%",
      "severity": "critical",
      "status": "acknowledged",
      "start_time": "2025-12-23T09:45:00Z",
      "end_time": null,
      "acknowledged_at": "2025-12-23T09:55:00Z",
      "acknowledged_by": "user-123",
      "source": "prometheus-alertmanager",
      "labels": {
        "job_type": "training",
        "environment": "production"
      },
      "annotations": {
        "failure_rate": "15",
        "threshold": "10",
        "affected_jobs": "5",
        "runbook_url": "https://docs.example.com/runbooks/job-failure-rate-high"
      },
      "fingerprint": "h8g7f6e5d4c3b2a1",
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12344",
        "rule": "/api/v1/monitoring/alert-rules/rule-456"
      }
    },
    {
      "id": "alert-12343",
      "name": "StorageNearingCapacity",
      "summary": "存储使用率接近容量",
      "description": "共享存储使用率达到85%，超过阈值80%",
      "severity": "medium",
      "status": "resolved",
      "start_time": "2025-12-23T08:30:00Z",
      "end_time": "2025-12-23T09:30:00Z",
      "source": "prometheus-alertmanager",
      "labels": {
        "storage_type": "shared_fs",
        "environment": "production"
      },
      "annotations": {
        "usage_percent": "85",
        "threshold": "80",
        "runbook_url": "https://docs.example.com/runbooks/storage-nearing-capacity"
      },
      "fingerprint": "i9j8k7l6m5n4o3p2",
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12343",
        "rule": "/api/v1/monitoring/alert-rules/rule-789"
      }
    }
  ],
  "pagination": {
    "total_items": 15,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  },
  "links": {
    "self": "/api/v1/monitoring/alerts"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 获取特定告警详情 (GET /alerts/{id})

获取单个告警的详细信息，包括历史状态变更和关联事件。

#### 路径参数

- `id`: 告警ID

#### 响应 (200 OK)

```json
{
  "id": "alert-12345",
  "name": "NodeGPUHighTemperature",
  "summary": "节点GPU温度过高",
  "description": "节点worker-2上的GPU 5温度已经超过阈值85°C达到92°C",
  "severity": "high",
  "status": "firing",
  "start_time": "2025-12-23T10:15:00Z",
  "end_time": null,
  "source": "prometheus-alertmanager",
  "labels": {
    "cluster": "cluster-001",
    "node": "node-003",
    "gpu_id": "5",
    "environment": "production"
  },
  "annotations": {
    "temperature": "92",
    "threshold": "85",
    "runbook_url": "https://docs.example.com/runbooks/node-gpu-high-temperature"
  },
  "fingerprint": "a1b2c3d4e5f6g7h8",
  "generator_url": "https://prometheus.example.com/graph?g0.expr=gpu_temperature+%3E+85",
  "values": [
    {
      "timestamp": "2025-12-23T10:15:00Z",
      "value": 92
    },
    {
      "timestamp": "2025-12-23T10:20:00Z",
      "value": 94
    },
    {
      "timestamp": "2025-12-23T10:25:00Z",
      "value": 93
    },
    {
      "timestamp": "2025-12-23T10:30:00Z",
      "value": 90
    }
  ],
  "history": [
    {
      "timestamp": "2025-12-23T10:15:00Z",
      "status": "firing",
      "value": 92
    },
    {
      "timestamp": "2025-12-23T10:30:00Z",
      "status": "firing",
      "value": 90
    }
  ],
  "related_alerts": [
    {
      "id": "alert-12340",
      "name": "NodeGPUHighTemperature",
      "summary": "节点GPU温度过高",
      "severity": "high",
      "status": "firing",
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12340"
      }
    }
  ],
  "related_events": [
    {
      "id": "event-5678",
      "timestamp": "2025-12-23T10:10:00Z",
      "type": "node_warning",
      "summary": "GPU风扇速度增加到100%",
      "links": {
        "self": "/api/v1/monitoring/status/incidents/event-5678"
      }
    }
  ],
  "rule": {
    "id": "rule-789",
    "name": "NodeGPUHighTemperature",
    "severity": "high",
    "links": {
      "self": "/api/v1/monitoring/alert-rules/rule-789"
    }
  },
  "affected_resources": {
    "node": {
      "id": "node-003",
      "name": "worker-2",
      "links": {
        "self": "/api/v1/resources/clusters/cluster-001/nodes/node-003"
      }
    }
  },
  "links": {
    "self": "/api/v1/monitoring/alerts/alert-12345",
    "acknowledge": "/api/v1/monitoring/alerts/alert-12345/actions/acknowledge",
    "resolve": "/api/v1/monitoring/alerts/alert-12345/actions/resolve"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的告警不存在

### 确认告警 (PUT /alerts/{id}/actions/acknowledge)

确认告警，表示已知悉并正在处理。

#### 路径参数

- `id`: 告警ID

#### 请求体

```json
{
  "comment": "已知悉，正在调查原因",
  "assigned_to": "user-234",
  "expected_resolve_time": "2025-12-23T14:00:00Z"
}
```

#### 响应 (200 OK)

```json
{
  "id": "alert-12345",
  "status": "acknowledged",
  "previous_status": "firing",
  "acknowledged_at": "2025-12-23T11:30:00Z",
  "acknowledged_by": "user-123",
  "comment": "已知悉，正在调查原因",
  "assigned_to": "user-234",
  "expected_resolve_time": "2025-12-23T14:00:00Z",
  "links": {
    "self": "/api/v1/monitoring/alerts/alert-12345",
    "resolve": "/api/v1/monitoring/alerts/alert-12345/actions/resolve"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的告警不存在
- **409 Conflict**: 告警状态不允许此操作

### 解决告警 (PUT /alerts/{id}/actions/resolve)

将告警标记为已解决。

#### 路径参数

- `id`: 告警ID

#### 请求体

```json
{
  "resolution_comment": "已调整GPU负载并清理散热系统",
  "root_cause": "散热系统积尘导致温度异常",
  "resolution_type": "manual"
}
```

#### 响应 (200 OK)

```json
{
  "id": "alert-12345",
  "status": "resolved",
  "previous_status": "acknowledged",
  "resolved_at": "2025-12-23T13:15:00Z",
  "resolved_by": "user-123",
  "resolution_comment": "已调整GPU负载并清理散热系统",
  "root_cause": "散热系统积尘导致温度异常",
  "resolution_type": "manual",
  "links": {
    "self": "/api/v1/monitoring/alerts/alert-12345"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的告警不存在
- **409 Conflict**: 告警状态不允许此操作

### 获取告警规则列表 (GET /alert-rules)

获取系统中配置的告警规则列表。

#### 查询参数

- `severity`: 按严重程度过滤
- `status`: 按状态过滤 (active, paused)
- `type`: 按规则类型过滤 (prometheus, system, custom)
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `sort`: 排序字段
- `order`: 排序方向 (asc, desc)，默认为asc

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "rule-789",
      "name": "NodeGPUHighTemperature",
      "description": "检测节点GPU温度是否超过阈值",
      "severity": "high",
      "status": "active",
      "type": "prometheus",
      "query": "gpu_temperature > 85",
      "duration": "5m",
      "labels": {
        "team": "infrastructure",
        "environment": "production"
      },
      "annotations": {
        "summary": "节点GPU温度过高",
        "description": "节点{{ $labels.node }}上的GPU {{ $labels.gpu_id }}温度已经超过阈值85°C达到{{ $value }}°C",
        "runbook_url": "https://docs.example.com/runbooks/node-gpu-high-temperature"
      },
      "created_at": "2025-11-01T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-01T00:00:00Z",
      "alert_count": {
        "firing": 1,
        "pending": 0,
        "resolved": 2
      },
      "links": {
        "self": "/api/v1/monitoring/alert-rules/rule-789",
        "alerts": "/api/v1/monitoring/alerts?rule_id=rule-789"
      }
    },
    {
      "id": "rule-456",
      "name": "JobFailureRateHigh",
      "description": "检测训练任务失败率是否超过阈值",
      "severity": "critical",
      "status": "active",
      "type": "prometheus",
      "query": "sum(rate(job_failures[30m])) / sum(rate(job_total[30m])) > 0.1",
      "duration": "10m",
      "labels": {
        "team": "ml-platform",
        "environment": "production"
      },
      "annotations": {
        "summary": "训练任务失败率过高",
        "description": "最近30分钟内训练任务失败率达到{{ $value | humanizePercentage }}，超过阈值10%",
        "runbook_url": "https://docs.example.com/runbooks/job-failure-rate-high"
      },
      "created_at": "2025-10-15T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-15T00:00:00Z",
      "alert_count": {
        "firing": 0,
        "pending": 0,
        "resolved": 5
      },
      "links": {
        "self": "/api/v1/monitoring/alert-rules/rule-456",
        "alerts": "/api/v1/monitoring/alerts?rule_id=rule-456"
      }
    }
  ],
  "pagination": {
    "total_items": 25,
    "total_pages": 2,
    "current_page": 1,
    "per_page": 20,
    "next": "/api/v1/monitoring/alert-rules?page=2&per_page=20",
    "prev": null
  },
  "links": {
    "self": "/api/v1/monitoring/alert-rules"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 创建告警规则 (POST /alert-rules)

创建新的告警规则。

#### 请求体

```json
{
  "name": "CPUUtilizationHigh",
  "description": "检测节点CPU利用率是否超过阈值",
  "severity": "medium",
  "type": "prometheus",
  "query": "avg(cpu_utilization) by (node) > 90",
  "duration": "15m",
  "labels": {
    "team": "infrastructure",
    "environment": "production"
  },
  "annotations": {
    "summary": "节点CPU利用率过高",
    "description": "节点{{ $labels.node }}的CPU利用率达到{{ $value }}%，超过阈值90%",
    "runbook_url": "https://docs.example.com/runbooks/cpu-utilization-high"
  },
  "notification_channels": ["channel-123", "channel-456"]
}
```

#### 响应 (201 Created)

```json
{
  "id": "rule-123",
  "name": "CPUUtilizationHigh",
  "description": "检测节点CPU利用率是否超过阈值",
  "severity": "medium",
  "status": "active",
  "type": "prometheus",
  "query": "avg(cpu_utilization) by (node) > 90",
  "duration": "15m",
  "labels": {
    "team": "infrastructure",
    "environment": "production"
  },
  "annotations": {
    "summary": "节点CPU利用率过高",
    "description": "节点{{ $labels.node }}的CPU利用率达到{{ $value }}%，超过阈值90%",
    "runbook_url": "https://docs.example.com/runbooks/cpu-utilization-high"
  },
  "notification_channels": [
    {
      "id": "channel-123",
      "name": "Platform Team Email",
      "type": "email"
    },
    {
      "id": "channel-456",
      "name": "Ops Slack Channel",
      "type": "slack"
    }
  ],
  "created_at": "2025-12-23T14:00:00Z",
  "created_by": "user-123",
  "updated_at": "2025-12-23T14:00:00Z",
  "links": {
    "self": "/api/v1/monitoring/alert-rules/rule-123"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **409 Conflict**: 资源冲突，例如同名告警规则已存在

### 获取特定告警规则详情 (GET /alert-rules/{id})

获取单个告警规则的详细信息。

#### 路径参数

- `id`: 告警规则ID

#### 响应 (200 OK)

```json
{
  "id": "rule-789",
  "name": "NodeGPUHighTemperature",
  "description": "检测节点GPU温度是否超过阈值",
  "severity": "high",
  "status": "active",
  "type": "prometheus",
  "query": "gpu_temperature > 85",
  "duration": "5m",
  "labels": {
    "team": "infrastructure",
    "environment": "production"
  },
  "annotations": {
    "summary": "节点GPU温度过高",
    "description": "节点{{ $labels.node }}上的GPU {{ $labels.gpu_id }}温度已经超过阈值85°C达到{{ $value }}°C",
    "runbook_url": "https://docs.example.com/runbooks/node-gpu-high-temperature"
  },
  "notification_channels": [
    {
      "id": "channel-123",
      "name": "Platform Team Email",
      "type": "email"
    },
    {
      "id": "channel-456",
      "name": "Ops Slack Channel",
      "type": "slack"
    }
  ],
  "created_at": "2025-11-01T00:00:00Z",
  "created_by": {
    "id": "user-123",
    "username": "admin",
    "email": "admin@example.com"
  },
  "updated_at": "2025-12-01T00:00:00Z",
  "last_triggered": "2025-12-23T10:15:00Z",
  "alert_count": {
    "firing": 1,
    "pending": 0,
    "resolved": 2
  },
  "recent_alerts": [
    {
      "id": "alert-12345",
      "status": "firing",
      "start_time": "2025-12-23T10:15:00Z",
      "end_time": null,
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12345"
      }
    },
    {
      "id": "alert-12340",
      "status": "resolved",
      "start_time": "2025-12-22T14:30:00Z",
      "end_time": "2025-12-22T16:45:00Z",
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12340"
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/alert-rules/rule-789",
    "alerts": "/api/v1/monitoring/alerts?rule_id=rule-789",
    "update": "/api/v1/monitoring/alert-rules/rule-789",
    "delete": "/api/v1/monitoring/alert-rules/rule-789"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的告警规则不存在

### 更新特定告警规则 (PUT /alert-rules/{id})

更新现有告警规则的配置。

#### 路径参数

- `id`: 告警规则ID

#### 请求体

```json
{
  "description": "检测节点GPU温度是否超过更新后的阈值",
  "severity": "high",
  "query": "gpu_temperature > 90",
  "duration": "3m",
  "status": "active",
  "annotations": {
    "summary": "节点GPU温度过高",
    "description": "节点{{ $labels.node }}上的GPU {{ $labels.gpu_id }}温度已经超过阈值90°C达到{{ $value }}°C",
    "runbook_url": "https://docs.example.com/runbooks/node-gpu-high-temperature"
  },
  "notification_channels": ["channel-123", "channel-789"]
}
```

#### 响应 (200 OK)

```json
{
  "id": "rule-789",
  "name": "NodeGPUHighTemperature",
  "description": "检测节点GPU温度是否超过更新后的阈值",
  "severity": "high",
  "status": "active",
  "query": "gpu_temperature > 90",
  "duration": "3m",
  "updated_at": "2025-12-23T15:00:00Z",
  "links": {
    "self": "/api/v1/monitoring/alert-rules/rule-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的告警规则不存在
- **409 Conflict**: 资源冲突

### 删除告警规则 (DELETE /alert-rules/{id})

删除指定的告警规则。

#### 路径参数

- `id`: 告警规则ID

#### 查询参数

- `force`: 布尔值，是否强制删除，即使规则当前有活跃告警，默认为false

#### 响应 (204 No Content)

成功删除后无响应体

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的告警规则不存在
- **409 Conflict**: 告警规则有活跃告警且force参数为false

### 获取系统健康状态 (GET /health)

获取整个系统的健康状态概览。

#### 响应 (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2025-12-23T15:30:00Z",
  "components": {
    "compute": {
      "status": "healthy",
      "message": "所有计算资源正常运行"
    },
    "storage": {
      "status": "healthy",
      "message": "所有存储资源正常运行"
    },
    "network": {
      "status": "healthy",
      "message": "网络连接正常"
    },
    "api": {
      "status": "healthy",
      "message": "API服务正常运行"
    },
    "scheduler": {
      "status": "healthy",
      "message": "调度器正常运行"
    }
  },
  "clusters": [
    {
      "id": "cluster-001",
      "name": "主生产集群",
      "status": "healthy",
      "nodes_total": 16,
      "nodes_ready": 16,
      "message": "集群正常运行"
    },
    {
      "id": "cluster-002",
      "name": "开发测试集群",
      "status": "healthy",
      "nodes_total": 8,
      "nodes_ready": 8,
      "message": "集群正常运行"
    }
  ],
  "metrics": {
    "api_success_rate": 99.98,
    "job_success_rate": 98.5,
    "resource_utilization": 72.5,
    "active_users": 125
  },
  "recent_incidents": [
    {
      "id": "incident-123",
      "title": "短暂的API延迟增加",
      "status": "resolved",
      "started_at": "2025-12-22T08:15:00Z",
      "resolved_at": "2025-12-22T09:30:00Z",
      "links": {
        "self": "/api/v1/monitoring/status/incidents/incident-123"
      }
    }
  ],
  "scheduled_maintenance": [
    {
      "id": "maintenance-456",
      "title": "计划内集群升级",
      "description": "升级Kubernetes版本到1.32.5",
      "start_time": "2025-12-28T02:00:00Z",
      "end_time": "2025-12-28T06:00:00Z",
      "links": {
        "self": "/api/v1/monitoring/status/maintenance/maintenance-456"
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/health",
    "components": "/api/v1/monitoring/health/components",
    "nodes": "/api/v1/monitoring/health/nodes",
    "incidents": "/api/v1/monitoring/status/incidents",
    "maintenance": "/api/v1/monitoring/status/maintenance"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 获取各组件健康状态 (GET /health/components)

获取系统各组件的健康状态详情。

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "compute",
      "name": "计算资源",
      "status": "healthy",
      "message": "所有计算资源正常运行",
      "last_check_time": "2025-12-23T15:29:00Z",
      "details": {
        "clusters": {
          "total": 2,
          "healthy": 2
        },
        "nodes": {
          "total": 24,
          "ready": 24
        },
        "gpus": {
          "total": 160,
          "healthy": 160
        }
      }
    },
    {
      "id": "storage",
      "name": "存储资源",
      "status": "healthy",
      "message": "所有存储资源正常运行",
      "last_check_time": "2025-12-23T15:29:30Z",
      "details": {
        "s3": {
          "status": "healthy",
          "latency_ms": 45
        },
        "fsx_lustre": {
          "status": "healthy",
          "throughput_gbps": 9.5
        },
        "efs": {
          "status": "healthy",
          "throughput_gbps": 2.8
        }
      }
    },
    {
      "id": "network",
      "name": "网络",
      "status": "healthy",
      "message": "网络连接正常",
      "last_check_time": "2025-12-23T15:29:45Z",
      "details": {
        "vpc": {
          "status": "healthy"
        },
        "internet_gateway": {
          "status": "healthy",
          "bandwidth_gbps": 45
        },
        "cluster_networking": {
          "status": "healthy",
          "latency_ms": 0.2
        }
      }
    },
    {
      "id": "api",
      "name": "API服务",
      "status": "healthy",
      "message": "API服务正常运行",
      "last_check_time": "2025-12-23T15:29:50Z",
      "details": {
        "success_rate": 99.98,
        "p50_latency_ms": 45,
        "p95_latency_ms": 120,
        "p99_latency_ms": 250
      }
    },
    {
      "id": "scheduler",
      "name": "调度器",
      "status": "healthy",
      "message": "调度器正常运行",
      "last_check_time": "2025-12-23T15:29:55Z",
      "details": {
        "job_success_rate": 98.5,
        "average_queue_time_s": 45,
        "pending_jobs": 12
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/health/components"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 获取节点健康状态 (GET /health/nodes)

获取所有计算节点的健康状态详情。

#### 查询参数

- `cluster_id`: 按集群ID过滤
- `status`: 按状态过滤 (ready, not-ready)
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100

#### 响应 (200 OK)

```json
{
  "summary": {
    "total_nodes": 24,
    "ready_nodes": 24,
    "not_ready_nodes": 0,
    "nodes_with_issues": 1
  },
  "items": [
    {
      "id": "node-001",
      "name": "worker-0",
      "cluster_id": "cluster-001",
      "status": "ready",
      "health": {
        "status": "warning",
        "message": "GPU温度接近阈值"
      },
      "last_check_time": "2025-12-23T15:29:00Z",
      "uptime_days": 45,
      "resources": {
        "gpu": {
          "total": 8,
          "healthy": 8,
          "utilization": 0.92
        },
        "cpu": {
          "total_cores": 96,
          "utilization": 0.85
        },
        "memory": {
          "total_gb": 1152,
          "utilization": 0.88
        }
      },
      "issues": [
        {
          "type": "warning",
          "component": "gpu-5",
          "message": "GPU 5温度接近阈值 (84°C/85°C)",
          "start_time": "2025-12-23T15:25:00Z",
          "alert_id": "alert-12345"
        }
      ],
      "links": {
        "self": "/api/v1/monitoring/health/nodes/node-001",
        "metrics": "/api/v1/monitoring/metrics/nodes/node-001",
        "logs": "/api/v1/monitoring/logs/nodes/node-001"
      }
    },
    {
      "id": "node-002",
      "name": "worker-1",
      "cluster_id": "cluster-001",
      "status": "ready",
      "health": {
        "status": "healthy",
        "message": "节点运行正常"
      },
      "last_check_time": "2025-12-23T15:29:00Z",
      "uptime_days": 32,
      "resources": {
        "gpu": {
          "total": 8,
          "healthy": 8,
          "utilization": 0.88
        },
        "cpu": {
          "total_cores": 96,
          "utilization": 0.80
        },
        "memory": {
          "total_gb": 1152,
          "utilization": 0.82
        }
      },
      "issues": [],
      "links": {
        "self": "/api/v1/monitoring/health/nodes/node-002",
        "metrics": "/api/v1/monitoring/metrics/nodes/node-002",
        "logs": "/api/v1/monitoring/logs/nodes/node-002"
      }
    }
  ],
  "pagination": {
    "total_items": 24,
    "total_pages": 2,
    "current_page": 1,
    "per_page": 20,
    "next": "/api/v1/monitoring/health/nodes?page=2&per_page=20",
    "prev": null
  },
  "links": {
    "self": "/api/v1/monitoring/health/nodes"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 获取系统事件历史 (GET /status/incidents)

获取系统事件和故障历史记录。

#### 查询参数

- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `severity`: 按严重程度过滤
- `status`: 按状态过滤 (active, resolved)
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `sort`: 排序字段
- `order`: 排序方向 (asc, desc)，默认为desc

#### 响应 (200 OK)

```json
{
  "summary": {
    "total_incidents": 25,
    "active_incidents": 1,
    "resolved_incidents": 24,
    "by_severity": {
      "critical": 2,
      "high": 5,
      "medium": 10,
      "low": 8
    }
  },
  "items": [
    {
      "id": "incident-123",
      "title": "短暂的API延迟增加",
      "description": "API响应时间出现暂时性增加，P99延迟从250ms上升到450ms",
      "severity": "medium",
      "status": "resolved",
      "started_at": "2025-12-22T08:15:00Z",
      "detected_at": "2025-12-22T08:20:00Z",
      "acknowledged_at": "2025-12-22T08:25:00Z",
      "resolved_at": "2025-12-22T09:30:00Z",
      "duration_minutes": 75,
      "components_affected": ["api"],
      "users_affected": 85,
      "root_cause": "数据库连接池耗尽导致查询延迟",
      "resolution": "增加连接池上限并优化长时间运行的查询",
      "created_alerts": [
        {
          "id": "alert-11111",
          "name": "APILatencyHigh",
          "links": {
            "self": "/api/v1/monitoring/alerts/alert-11111"
          }
        }
      ],
      "timeline": [
        {
          "time": "2025-12-22T08:15:00Z",
          "event": "API延迟开始增加",
          "author": "system"
        },
        {
          "time": "2025-12-22T08:20:00Z",
          "event": "触发告警APILatencyHigh",
          "author": "system"
        },
        {
          "time": "2025-12-22T08:25:00Z",
          "event": "平台团队确认告警",
          "author": "user-123"
        },
        {
          "time": "2025-12-22T09:00:00Z",
          "event": "增加数据库连接池上限",
          "author": "user-234"
        },
        {
          "time": "2025-12-22T09:15:00Z",
          "event": "优化长时间运行的查询",
          "author": "user-234"
        },
        {
          "time": "2025-12-22T09:30:00Z",
          "event": "API延迟恢复正常",
          "author": "system"
        }
      ],
      "links": {
        "self": "/api/v1/monitoring/status/incidents/incident-123",
        "related_alerts": "/api/v1/monitoring/alerts?incident_id=incident-123"
      }
    },
    {
      "id": "incident-122",
      "title": "数据集存储暂时不可用",
      "description": "FSx for Lustre存储系统暂时不可用，影响数据集访问",
      "severity": "high",
      "status": "resolved",
      "started_at": "2025-12-15T04:30:00Z",
      "detected_at": "2025-12-15T04:35:00Z",
      "acknowledged_at": "2025-12-15T04:40:00Z",
      "resolved_at": "2025-12-15T06:15:00Z",
      "duration_minutes": 105,
      "components_affected": ["storage"],
      "users_affected": 42,
      "root_cause": "FSx自动维护操作导致临时不可用",
      "resolution": "存储系统维护完成后自动恢复",
      "links": {
        "self": "/api/v1/monitoring/status/incidents/incident-122",
        "related_alerts": "/api/v1/monitoring/alerts?incident_id=incident-122"
      }
    }
  ],
  "pagination": {
    "total_items": 25,
    "total_pages": 2,
    "current_page": 1,
    "per_page": 20,
    "next": "/api/v1/monitoring/status/incidents?page=2&per_page=20",
    "prev": null
  },
  "links": {
    "self": "/api/v1/monitoring/status/incidents"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 获取维护计划 (GET /status/maintenance)

获取系统维护计划列表。

#### 查询参数

- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `status`: 按状态过滤 (scheduled, in-progress, completed, cancelled)
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `sort`: 排序字段
- `order`: 排序方向 (asc, desc)，默认为asc

#### 响应 (200 OK)

```json
{
  "summary": {
    "total_maintenance": 15,
    "scheduled": 3,
    "in_progress": 0,
    "completed": 12,
    "cancelled": 0
  },
  "items": [
    {
      "id": "maintenance-456",
      "title": "计划内集群升级",
      "description": "升级Kubernetes版本到1.32.5",
      "status": "scheduled",
      "impact_level": "medium",
      "impact_description": "升级期间可能导致任务调度延迟，但不影响正在运行的训练任务",
      "start_time": "2025-12-28T02:00:00Z",
      "end_time": "2025-12-28T06:00:00Z",
      "duration_hours": 4,
      "created_at": "2025-12-15T10:00:00Z",
      "created_by": "user-123",
      "components_affected": ["scheduler", "api"],
      "clusters_affected": ["cluster-001", "cluster-002"],
      "notification_sent": true,
      "notification_time": "2025-12-21T10:00:00Z",
      "links": {
        "self": "/api/v1/monitoring/status/maintenance/maintenance-456"
      }
    },
    {
      "id": "maintenance-455",
      "title": "存储系统扩容",
      "description": "FSx for Lustre存储系统扩容，增加吞吐能力",
      "status": "completed",
      "impact_level": "low",
      "impact_description": "期间可能有短暂的数据访问延迟，但不影响训练任务运行",
      "start_time": "2025-12-20T01:00:00Z",
      "end_time": "2025-12-20T03:00:00Z",
      "actual_start_time": "2025-12-20T01:00:00Z",
      "actual_end_time": "2025-12-20T02:30:00Z",
      "duration_hours": 1.5,
      "created_at": "2025-12-10T10:00:00Z",
      "created_by": "user-123",
      "components_affected": ["storage"],
      "clusters_affected": ["cluster-001"],
      "notification_sent": true,
      "notification_time": "2025-12-13T10:00:00Z",
      "completion_status": "success",
      "completion_notes": "扩容成功完成，吞吐能力从9Gbps增加到12Gbps",
      "links": {
        "self": "/api/v1/monitoring/status/maintenance/maintenance-455"
      }
    }
  ],
  "pagination": {
    "total_items": 15,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  },
  "links": {
    "self": "/api/v1/monitoring/status/maintenance"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 获取通知渠道列表 (GET /notifications/channels)

获取配置的通知渠道列表。

#### 查询参数

- `type`: 按通知类型过滤 (email, slack, webhook, etc)
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "channel-123",
      "name": "Platform Team Email",
      "description": "平台团队电子邮件通知",
      "type": "email",
      "created_at": "2025-11-01T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-01T00:00:00Z",
      "config": {
        "recipients": ["platform-team@example.com"],
        "send_resolved": true
      },
      "status": "active",
      "last_test_time": "2025-12-15T00:00:00Z",
      "last_test_status": "success",
      "usage_count": 15,
      "links": {
        "self": "/api/v1/monitoring/notifications/channels/channel-123",
        "test": "/api/v1/monitoring/notifications/channels/channel-123/actions/test"
      }
    },
    {
      "id": "channel-456",
      "name": "Ops Slack Channel",
      "description": "运维团队Slack通知",
      "type": "slack",
      "created_at": "2025-11-05T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-05T00:00:00Z",
      "config": {
        "webhook_url": "https://hooks.slack.com/services/REDACTED",
        "channel": "#ops-alerts",
        "username": "AI Platform Monitor",
        "send_resolved": true
      },
      "status": "active",
      "last_test_time": "2025-12-10T00:00:00Z",
      "last_test_status": "success",
      "usage_count": 28,
      "links": {
        "self": "/api/v1/monitoring/notifications/channels/channel-456",
        "test": "/api/v1/monitoring/notifications/channels/channel-456/actions/test"
      }
    }
  ],
  "pagination": {
    "total_items": 5,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  },
  "links": {
    "self": "/api/v1/monitoring/notifications/channels"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 创建新通知渠道 (POST /notifications/channels)

创建新的通知渠道。

#### 请求体

```json
{
  "name": "DevOps WeChat Group",
  "description": "DevOps团队微信群通知",
  "type": "wechat",
  "config": {
    "corp_id": "wx123456789",
    "corp_secret": "REDACTED",
    "agent_id": 1000002,
    "to_user": "@all",
    "send_resolved": true
  },
  "settings": {
    "throttling_duration_minutes": 10,
    "max_alerts_per_message": 5
  }
}
```

#### 响应 (201 Created)

```json
{
  "id": "channel-789",
  "name": "DevOps WeChat Group",
  "description": "DevOps团队微信群通知",
  "type": "wechat",
  "created_at": "2025-12-23T16:00:00Z",
  "created_by": "user-123",
  "updated_at": "2025-12-23T16:00:00Z",
  "config": {
    "corp_id": "wx123456789",
    "agent_id": 1000002,
    "to_user": "@all",
    "send_resolved": true
  },
  "settings": {
    "throttling_duration_minutes": 10,
    "max_alerts_per_message": 5
  },
  "status": "active",
  "links": {
    "self": "/api/v1/monitoring/notifications/channels/channel-789",
    "test": "/api/v1/monitoring/notifications/channels/channel-789/actions/test"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **409 Conflict**: 资源冲突，例如同名通知渠道已存在

### 获取特定通知渠道详情 (GET /notifications/channels/{id})

获取单个通知渠道的详细信息。

#### 路径参数

- `id`: 通知渠道ID

#### 响应 (200 OK)

```json
{
  "id": "channel-123",
  "name": "Platform Team Email",
  "description": "平台团队电子邮件通知",
  "type": "email",
  "created_at": "2025-11-01T00:00:00Z",
  "created_by": {
    "id": "user-123",
    "username": "admin",
    "email": "admin@example.com"
  },
  "updated_at": "2025-12-01T00:00:00Z",
  "config": {
    "recipients": ["platform-team@example.com"],
    "send_resolved": true,
    "subject_template": "{{ .Status | toUpper }}: {{ .CommonLabels.alertname }}",
    "message_template": "告警状态: {{ .Status }}\n告警名称: {{ .CommonLabels.alertname }}\n严重程度: {{ .CommonLabels.severity }}\n{{ range .Alerts -}}\n---\n{{ range .Labels.SortedPairs }}{{ .Name }}: {{ .Value }}\n{{ end }}{{ end }}"
  },
  "settings": {
    "throttling_duration_minutes": 5,
    "max_alerts_per_message": 10,
    "include_dashboard_links": true,
    "attach_screenshots": false
  },
  "status": "active",
  "last_test_time": "2025-12-15T00:00:00Z",
  "last_test_status": "success",
  "last_notification_time": "2025-12-23T10:15:00Z",
  "usage_count": 15,
  "usage_stats": {
    "total_notifications": 150,
    "notifications_last_24h": 5,
    "notifications_last_7d": 25,
    "notifications_last_30d": 75,
    "by_severity": {
      "critical": 15,
      "high": 35,
      "medium": 65,
      "low": 35
    }
  },
  "linked_alert_rules": [
    {
      "id": "rule-789",
      "name": "NodeGPUHighTemperature",
      "severity": "high",
      "links": {
        "self": "/api/v1/monitoring/alert-rules/rule-789"
      }
    }
  ],
  "linked_subscriptions": [
    {
      "id": "subscription-456",
      "name": "平台团队告警订阅",
      "links": {
        "self": "/api/v1/monitoring/notifications/subscriptions/subscription-456"
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/notifications/channels/channel-123",
    "test": "/api/v1/monitoring/notifications/channels/channel-123/actions/test",
    "history": "/api/v1/monitoring/notifications/channels/channel-123/history"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的通知渠道不存在

### 更新特定通知渠道 (PUT /notifications/channels/{id})

更新现有通知渠道的配置。

#### 路径参数

- `id`: 通知渠道ID

#### 请求体

```json
{
  "description": "平台团队和管理层电子邮件通知",
  "config": {
    "recipients": ["platform-team@example.com", "management@example.com"],
    "send_resolved": true
  },
  "settings": {
    "throttling_duration_minutes": 10,
    "max_alerts_per_message": 5
  },
  "status": "active"
}
```

#### 响应 (200 OK)

```json
{
  "id": "channel-123",
  "name": "Platform Team Email",
  "description": "平台团队和管理层电子邮件通知",
  "updated_at": "2025-12-23T16:30:00Z",
  "links": {
    "self": "/api/v1/monitoring/notifications/channels/channel-123"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的通知渠道不存在

### 删除通知渠道 (DELETE /notifications/channels/{id})

删除指定的通知渠道。

#### 路径参数

- `id`: 通知渠道ID

#### 查询参数

- `force`: 布尔值，是否强制删除，即使该渠道正被告警规则或订阅使用，默认为false

#### 响应 (204 No Content)

成功删除后无响应体

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的通知渠道不存在
- **409 Conflict**: 通知渠道正被使用且force参数为false

### 获取通知订阅列表 (GET /notifications/subscriptions)

获取通知订阅列表。

#### 查询参数

- `user_id`: 按用户ID过滤
- `team_id`: 按团队ID过滤
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "subscription-456",
      "name": "平台团队告警订阅",
      "description": "平台团队关注的所有重要告警",
      "created_at": "2025-11-15T00:00:00Z",
      "created_by": "user-123",
      "updated_at": "2025-12-15T00:00:00Z",
      "filters": {
        "severities": ["critical", "high"],
        "alert_names": ["NodeGPUHighTemperature", "JobFailureRateHigh"]
      },
      "channels": [
        {
          "id": "channel-123",
          "name": "Platform Team Email",
          "type": "email"
        },
        {
          "id": "channel-456",
          "name": "Ops Slack Channel",
          "type": "slack"
        }
      ],
      "status": "active",
      "links": {
        "self": "/api/v1/monitoring/notifications/subscriptions/subscription-456"
      }
    },
    {
      "id": "subscription-457",
      "name": "个人训练任务通知",
      "description": "用户自己训练任务相关的通知",
      "created_at": "2025-11-20T00:00:00Z",
      "created_by": "user-234",
      "updated_at": "2025-12-20T00:00:00Z",
      "filters": {
        "severities": ["critical", "high", "medium"],
        "labels": {
          "created_by": "user-234"
        }
      },
      "channels": [
        {
          "id": "channel-789",
          "name": "张伟个人邮箱",
          "type": "email"
        }
      ],
      "status": "active",
      "links": {
        "self": "/api/v1/monitoring/notifications/subscriptions/subscription-457"
      }
    }
  ],
  "pagination": {
    "total_items": 10,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  },
  "links": {
    "self": "/api/v1/monitoring/notifications/subscriptions"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足

### 创建新通知订阅 (POST /notifications/subscriptions)

创建新的通知订阅。

#### 请求体

```json
{
  "name": "存储系统告警通知",
  "description": "存储团队关注的存储系统告警",
  "filters": {
    "severities": ["critical", "high", "medium"],
    "alert_names": ["StorageNearingCapacity", "StoragePerformanceDegraded"],
    "labels": {
      "component": "storage"
    }
  },
  "channels": ["channel-123", "channel-789"],
  "settings": {
    "throttling_duration_minutes": 15,
    "group_by": ["alertname", "severity"]
  }
}
```

#### 响应 (201 Created)

```json
{
  "id": "subscription-458",
  "name": "存储系统告警通知",
  "description": "存储团队关注的存储系统告警",
  "created_at": "2025-12-23T17:00:00Z",
  "created_by": "user-123",
  "updated_at": "2025-12-23T17:00:00Z",
  "filters": {
    "severities": ["critical", "high", "medium"],
    "alert_names": ["StorageNearingCapacity", "StoragePerformanceDegraded"],
    "labels": {
      "component": "storage"
    }
  },
  "channels": [
    {
      "id": "channel-123",
      "name": "Platform Team Email",
      "type": "email"
    },
    {
      "id": "channel-789",
      "name": "DevOps WeChat Group",
      "type": "wechat"
    }
  ],
  "settings": {
    "throttling_duration_minutes": 15,
    "group_by": ["alertname", "severity"]
  },
  "status": "active",
  "links": {
    "self": "/api/v1/monitoring/notifications/subscriptions/subscription-458"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **409 Conflict**: 资源冲突，例如同名订阅已存在

### 获取特定通知订阅详情 (GET /notifications/subscriptions/{id})

获取单个通知订阅的详细信息。

#### 路径参数

- `id`: 通知订阅ID

#### 响应 (200 OK)

```json
{
  "id": "subscription-456",
  "name": "平台团队告警订阅",
  "description": "平台团队关注的所有重要告警",
  "created_at": "2025-11-15T00:00:00Z",
  "created_by": {
    "id": "user-123",
    "username": "admin",
    "email": "admin@example.com"
  },
  "updated_at": "2025-12-15T00:00:00Z",
  "filters": {
    "severities": ["critical", "high"],
    "alert_names": ["NodeGPUHighTemperature", "JobFailureRateHigh"],
    "labels": {},
    "annotations": {},
    "status": ["firing"]
  },
  "channels": [
    {
      "id": "channel-123",
      "name": "Platform Team Email",
      "type": "email",
      "status": "active"
    },
    {
      "id": "channel-456",
      "name": "Ops Slack Channel",
      "type": "slack",
      "status": "active"
    }
  ],
  "settings": {
    "throttling_duration_minutes": 5,
    "max_alerts_per_notification": 10,
    "group_by": ["alertname", "severity"],
    "include_resolved": true,
    "repeat_interval_minutes": 60
  },
  "status": "active",
  "stats": {
    "total_notifications": 45,
    "notifications_last_24h": 3,
    "notifications_last_7d": 12,
    "notifications_last_30d": 35
  },
  "matched_alerts": [
    {
      "id": "alert-12345",
      "name": "NodeGPUHighTemperature",
      "status": "firing",
      "severity": "high",
      "notified_at": "2025-12-23T10:15:00Z",
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12345"
      }
    },
    {
      "id": "alert-12344",
      "name": "JobFailureRateHigh",
      "status": "acknowledged",
      "severity": "critical",
      "notified_at": "2025-12-23T09:45:00Z",
      "links": {
        "self": "/api/v1/monitoring/alerts/alert-12344"
      }
    }
  ],
  "links": {
    "self": "/api/v1/monitoring/notifications/subscriptions/subscription-456",
    "history": "/api/v1/monitoring/notifications/subscriptions/subscription-456/history",
    "test": "/api/v1/monitoring/notifications/subscriptions/subscription-456/actions/test"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的通知订阅不存在

### 更新特定通知订阅 (PUT /notifications/subscriptions/{id})

更新现有通知订阅的配置。

#### 路径参数

- `id`: 通知订阅ID

#### 请求体

```json
{
  "description": "平台团队关注的所有重要和中等告警",
  "filters": {
    "severities": ["critical", "high", "medium"],
    "alert_names": ["NodeGPUHighTemperature", "JobFailureRateHigh", "StorageNearingCapacity"]
  },
  "channels": ["channel-123", "channel-456", "channel-789"],
  "settings": {
    "throttling_duration_minutes": 10
  },
  "status": "active"
}
```

#### 响应 (200 OK)

```json
{
  "id": "subscription-456",
  "name": "平台团队告警订阅",
  "description": "平台团队关注的所有重要和中等告警",
  "updated_at": "2025-12-23T17:30:00Z",
  "links": {
    "self": "/api/v1/monitoring/notifications/subscriptions/subscription-456"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的通知订阅不存在

### 删除通知订阅 (DELETE /notifications/subscriptions/{id})

删除指定的通知订阅。

#### 路径参数

- `id`: 通知订阅ID

#### 响应 (204 No Content)

成功删除后无响应体

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的通知订阅不存在

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
| 504 | 网关超时 |

## 错误响应格式

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "找不到指定的告警",
    "details": "找不到ID为alert-12345的告警",
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

## 实时数据流

对于实时指标和日志数据，API支持以下实时数据流机制：

1. **Server-Sent Events (SSE)**
   - 指标实时更新: `/api/v1/monitoring/metrics/stream`
   - 日志实时流: `/api/v1/monitoring/logs/stream`
   - 告警实时通知: `/api/v1/monitoring/alerts/stream`

2. **WebSocket**
   - 连接端点: `wss://api.example.com/api/v1/monitoring/ws`
   - 支持双向通信，可用于实时监控仪表板

## 版本控制

API使用语义化版本控制，格式为v{major}.{minor}.{patch}。主要版本号变更表示不向后兼容的更改，客户端应该通过API基础路径中的版本号指定使用的API版本。

## 安全要求

1. 所有API请求必须使用HTTPS
2. 认证使用Bearer Token (JWT)
3. 令牌必须包含适当的权限范围
4. 令牌过期时间不超过12小时
5. 敏感数据（如API密钥、密码）不会记录在日志中