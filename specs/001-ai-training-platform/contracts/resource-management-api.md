# API契约: 资源管理

**版本**: v1.0.0 | **日期**: 2025-12-23 | **特性分支**: `001-ai-training-platform`

## API概述

资源管理API提供了企业级AI训练平台的资源配额分配、监控和治理能力。该API支持按团队/项目设置资源配额、优先级管理、资源使用统计和成本分析。

## 基本信息

- **基础路径**: `/api/v1/resources`
- **认证**: Bearer Token (JWT)
- **内容类型**: application/json
- **响应格式**: JSON

## 端点概览

### 资源配额管理

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /quotas | 创建新资源配额 | `resource:create` |
| GET | /quotas | 获取资源配额列表 | `resource:read` |
| GET | /quotas/{id} | 获取特定资源配额详情 | `resource:read` |
| PUT | /quotas/{id} | 更新特定资源配额 | `resource:update` |
| DELETE | /quotas/{id} | 删除资源配额 | `resource:delete` |
| GET | /quotas/usage | 获取配额使用情况 | `resource:read` |
| PUT | /quotas/{id}/actions/override | 临时覆盖资源配额限制 | `resource:admin` |

### 资源限制配置管理

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /limit-configs | 创建角色资源限制配置 | `resource:admin` |
| GET | /limit-configs | 获取资源限制配置列表 | `resource:read` |
| GET | /limit-configs/{id} | 获取特定资源限制配置详情 | `resource:read` |
| PUT | /limit-configs/{id} | 更新特定资源限制配置 | `resource:admin` |
| DELETE | /limit-configs/{id} | 删除资源限制配置 | `resource:admin` |

### 资源使用统计与分析

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /usage | 获取资源使用统计 | `resource:read` |
| GET | /usage/history | 获取历史资源使用数据 | `resource:read` |
| GET | /usage/{owner_type}/{owner_id} | 获取特定所有者的资源使用统计 | `resource:read` |
| GET | /costs | 获取资源成本分析 | `resource:read` |
| GET | /costs/forecast | 获取资源成本预测 | `resource:read` |
| GET | /costs/{owner_type}/{owner_id} | 获取特定所有者的资源成本分析 | `resource:read` |

### 集群管理

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /clusters | 获取集群列表 | `resource:read` |
| GET | /clusters/{id} | 获取特定集群详情 | `resource:read` |
| GET | /clusters/{id}/nodes | 获取集群节点列表 | `resource:read` |
| GET | /clusters/{id}/metrics | 获取集群指标数据 | `resource:read` |
| POST | /clusters/{id}/actions/scale | 扩缩集群规模 | `resource:admin` |

## 详细定义

### 创建新资源配额 (POST /quotas)

创建新的资源配额配置，为团队或项目分配计算资源。

#### 请求体

```json
{
  "owner_type": "team",
  "owner_id": "team-123",
  "gpu_limit": 128,
  "cpu_limit": 1024,
  "memory_limit_gb": 4096,
  "storage_limit_gb": 20480,
  "priority": 80,
  "can_borrow": true,
  "can_lend": true,
  "borrow_limit_percentage": 200,
  "description": "研发部GPU资源配额",
  "effective_from": "2025-12-23T00:00:00Z",
  "expiration": null
}
```

#### 响应 (201 Created)

```json
{
  "id": "quota-456",
  "owner_type": "team",
  "owner_id": "team-123",
  "owner_name": "研发部",
  "gpu_limit": 128,
  "cpu_limit": 1024,
  "memory_limit_gb": 4096,
  "storage_limit_gb": 20480,
  "priority": 80,
  "can_borrow": true,
  "can_lend": true,
  "borrow_limit_percentage": 200,
  "description": "研发部GPU资源配额",
  "effective_from": "2025-12-23T00:00:00Z",
  "expiration": null,
  "created_at": "2025-12-23T08:15:30Z",
  "created_by": "user-123",
  "updated_at": "2025-12-23T08:15:30Z",
  "links": {
    "self": "/api/v1/resources/quotas/quota-456",
    "usage": "/api/v1/resources/quotas/quota-456/usage"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **409 Conflict**: 资源配额冲突，例如同一所有者已存在配额

### 获取资源配额列表 (GET /quotas)

获取所有资源配额的列表，支持分页和过滤。

#### 查询参数

- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `owner_type`: 按所有者类型过滤 (team, project)
- `owner_id`: 按所有者ID过滤
- `sort`: 排序字段 (created_at, priority, gpu_limit)
- `order`: 排序方向 (asc, desc)，默认desc

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "quota-456",
      "owner_type": "team",
      "owner_id": "team-123",
      "owner_name": "研发部",
      "gpu_limit": 128,
      "cpu_limit": 1024,
      "memory_limit_gb": 4096,
      "storage_limit_gb": 20480,
      "priority": 80,
      "created_at": "2025-12-23T08:15:30Z",
      "updated_at": "2025-12-23T08:15:30Z",
      "usage": {
        "gpu_used": 64,
        "cpu_used": 512,
        "memory_used_gb": 2048,
        "storage_used_gb": 10240,
        "usage_percentage": 50
      },
      "links": {
        "self": "/api/v1/resources/quotas/quota-456"
      }
    },
    {
      "id": "quota-457",
      "owner_type": "team",
      "owner_id": "team-124",
      "owner_name": "市场部",
      "gpu_limit": 64,
      "cpu_limit": 512,
      "memory_limit_gb": 2048,
      "storage_limit_gb": 10240,
      "priority": 50,
      "created_at": "2025-12-22T10:30:00Z",
      "updated_at": "2025-12-22T10:30:00Z",
      "usage": {
        "gpu_used": 16,
        "cpu_used": 128,
        "memory_used_gb": 512,
        "storage_used_gb": 2048,
        "usage_percentage": 25
      },
      "links": {
        "self": "/api/v1/resources/quotas/quota-457"
      }
    }
  ],
  "pagination": {
    "total_items": 8,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  }
}
```

### 获取特定资源配额详情 (GET /quotas/{id})

获取单个资源配额的详细信息。

#### 路径参数

- `id`: 资源配额ID

#### 响应 (200 OK)

```json
{
  "id": "quota-456",
  "owner_type": "team",
  "owner_id": "team-123",
  "owner_name": "研发部",
  "owner_details": {
    "id": "team-123",
    "name": "研发部",
    "description": "AI算法研发团队",
    "member_count": 50
  },
  "gpu_limit": 128,
  "cpu_limit": 1024,
  "memory_limit_gb": 4096,
  "storage_limit_gb": 20480,
  "priority": 80,
  "can_borrow": true,
  "can_lend": true,
  "borrow_limit_percentage": 200,
  "description": "研发部GPU资源配额",
  "effective_from": "2025-12-23T00:00:00Z",
  "expiration": null,
  "created_at": "2025-12-23T08:15:30Z",
  "created_by": {
    "id": "user-123",
    "username": "admin",
    "email": "admin@example.com"
  },
  "updated_at": "2025-12-23T08:15:30Z",
  "usage_current": {
    "gpu_used": 64,
    "cpu_used": 512,
    "memory_used_gb": 2048,
    "storage_used_gb": 10240,
    "usage_percentage": 50,
    "borrowed_gpu": 0,
    "lent_gpu": 32,
    "jobs_running": 8,
    "jobs_pending": 4
  },
  "usage_history": {
    "time_periods": ["2025-12-22", "2025-12-23"],
    "gpu_usage": [45, 64],
    "cpu_usage": [400, 512],
    "memory_usage_gb": [1800, 2048],
    "storage_usage_gb": [9200, 10240]
  },
  "sub_quotas": [
    {
      "id": "quota-458",
      "owner_type": "project",
      "owner_id": "project-456",
      "owner_name": "大模型训练项目",
      "gpu_limit": 64,
      "priority": 85,
      "links": {
        "self": "/api/v1/resources/quotas/quota-458"
      }
    }
  ],
  "links": {
    "self": "/api/v1/resources/quotas/quota-456",
    "usage": "/api/v1/resources/quotas/quota-456/usage",
    "owner": "/api/v1/teams/team-123",
    "override": "/api/v1/resources/quotas/quota-456/actions/override"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的资源配额不存在

### 更新特定资源配额 (PUT /quotas/{id})

更新现有资源配额的配置。

#### 路径参数

- `id`: 资源配额ID

#### 请求体

```json
{
  "gpu_limit": 256,
  "cpu_limit": 2048,
  "memory_limit_gb": 8192,
  "storage_limit_gb": 40960,
  "priority": 90,
  "can_borrow": true,
  "can_lend": false,
  "borrow_limit_percentage": 150,
  "description": "研发部GPU资源配额 - 已升级",
  "expiration": "2026-12-31T23:59:59Z"
}
```

#### 响应 (200 OK)

```json
{
  "id": "quota-456",
  "owner_type": "team",
  "owner_id": "team-123",
  "gpu_limit": 256,
  "cpu_limit": 2048,
  "memory_limit_gb": 8192,
  "storage_limit_gb": 40960,
  "priority": 90,
  "updated_at": "2025-12-23T10:30:00Z",
  "links": {
    "self": "/api/v1/resources/quotas/quota-456"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的资源配额不存在
- **409 Conflict**: 资源冲突，例如配额超过系统限制

### 删除资源配额 (DELETE /quotas/{id})

删除指定的资源配额。

#### 路径参数

- `id`: 资源配额ID

#### 查询参数

- `force`: 布尔值，是否强制删除（默认false）

#### 响应 (204 No Content)

成功删除后无响应体

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的资源配额不存在
- **409 Conflict**: 资源正在使用中，无法删除

### 获取配额使用情况 (GET /quotas/usage)

获取所有配额的当前使用情况概览。

#### 查询参数

- `owner_type`: 按所有者类型过滤 (team, project)
- `include_details`: 布尔值，是否包含详细使用情况（默认false）

#### 响应 (200 OK)

```json
{
  "summary": {
    "total_gpu_limit": 256,
    "total_gpu_used": 128,
    "total_usage_percentage": 50,
    "total_jobs_running": 16,
    "total_jobs_pending": 8
  },
  "by_owner_type": {
    "team": {
      "gpu_limit": 192,
      "gpu_used": 96,
      "usage_percentage": 50
    },
    "project": {
      "gpu_limit": 64,
      "gpu_used": 32,
      "usage_percentage": 50
    }
  },
  "by_priority": {
    "high": {
      "gpu_limit": 128,
      "gpu_used": 64,
      "usage_percentage": 50
    },
    "medium": {
      "gpu_limit": 96,
      "gpu_used": 48,
      "usage_percentage": 50
    },
    "low": {
      "gpu_limit": 32,
      "gpu_used": 16,
      "usage_percentage": 50
    }
  },
  "quotas": [
    {
      "id": "quota-456",
      "owner_type": "team",
      "owner_id": "team-123",
      "owner_name": "研发部",
      "gpu_limit": 128,
      "gpu_used": 64,
      "usage_percentage": 50,
      "jobs_running": 8,
      "jobs_pending": 4,
      "links": {
        "self": "/api/v1/resources/quotas/quota-456"
      }
    },
    {
      "id": "quota-457",
      "owner_type": "team",
      "owner_id": "team-124",
      "owner_name": "市场部",
      "gpu_limit": 64,
      "gpu_used": 16,
      "usage_percentage": 25,
      "jobs_running": 2,
      "jobs_pending": 1,
      "links": {
        "self": "/api/v1/resources/quotas/quota-457"
      }
    }
  ],
  "links": {
    "self": "/api/v1/resources/quotas/usage"
  }
}
```

### 临时覆盖资源配额限制 (PUT /quotas/{id}/actions/override)

临时覆盖特定资源配额的限制，用于紧急情况或特殊任务。

#### 路径参数

- `id`: 资源配额ID

#### 请求体

```json
{
  "gpu_limit_override": 512,
  "priority_override": 95,
  "reason": "紧急大模型训练任务",
  "duration_hours": 48,
  "approved_by": "user-123"
}
```

#### 响应 (200 OK)

```json
{
  "id": "quota-456",
  "owner_type": "team",
  "owner_id": "team-123",
  "original_gpu_limit": 256,
  "gpu_limit_override": 512,
  "original_priority": 90,
  "priority_override": 95,
  "override_reason": "紧急大模型训练任务",
  "override_start": "2025-12-23T10:45:00Z",
  "override_end": "2025-12-25T10:45:00Z",
  "approved_by": "user-123",
  "links": {
    "self": "/api/v1/resources/quotas/quota-456",
    "cancel_override": "/api/v1/resources/quotas/quota-456/actions/cancel-override"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的资源配额不存在

### 创建角色资源限制配置 (POST /limit-configs)

创建基于用户角色和项目的默认资源限制配置。

#### 请求体

```json
{
  "role": "data-scientist",
  "project_id": "project-456",
  "max_gpus": 16,
  "max_cpu": 128,
  "max_memory_gb": 512,
  "max_storage_gb": 2048,
  "description": "数据科学家在大模型训练项目中的资源限制",
  "effective_from": "2025-12-23T00:00:00Z",
  "expiration": null
}
```

#### 响应 (201 Created)

```json
{
  "id": "limit-config-789",
  "role": "data-scientist",
  "project_id": "project-456",
  "project_name": "大模型训练项目",
  "max_gpus": 16,
  "max_cpu": 128,
  "max_memory_gb": 512,
  "max_storage_gb": 2048,
  "description": "数据科学家在大模型训练项目中的资源限制",
  "effective_from": "2025-12-23T00:00:00Z",
  "expiration": null,
  "created_at": "2025-12-23T08:30:00Z",
  "created_by": "user-123",
  "updated_at": "2025-12-23T08:30:00Z",
  "links": {
    "self": "/api/v1/resources/limit-configs/limit-config-789",
    "project": "/api/v1/projects/project-456"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **409 Conflict**: 资源冲突，例如同样角色和项目的配置已存在

### 获取资源限制配置列表 (GET /limit-configs)

获取所有资源限制配置的列表，支持分页和过滤。

#### 查询参数

- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `role`: 按角色过滤
- `project_id`: 按项目ID过滤
- `sort`: 排序字段 (created_at, role)
- `order`: 排序方向 (asc, desc)，默认desc

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "limit-config-789",
      "role": "data-scientist",
      "project_id": "project-456",
      "project_name": "大模型训练项目",
      "max_gpus": 16,
      "max_cpu": 128,
      "max_memory_gb": 512,
      "max_storage_gb": 2048,
      "created_at": "2025-12-23T08:30:00Z",
      "updated_at": "2025-12-23T08:30:00Z",
      "links": {
        "self": "/api/v1/resources/limit-configs/limit-config-789"
      }
    },
    {
      "id": "limit-config-790",
      "role": "ml-engineer",
      "project_id": "project-456",
      "project_name": "大模型训练项目",
      "max_gpus": 32,
      "max_cpu": 256,
      "max_memory_gb": 1024,
      "max_storage_gb": 4096,
      "created_at": "2025-12-23T08:35:00Z",
      "updated_at": "2025-12-23T08:35:00Z",
      "links": {
        "self": "/api/v1/resources/limit-configs/limit-config-790"
      }
    }
  ],
  "pagination": {
    "total_items": 6,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  }
}
```

### 获取特定资源限制配置详情 (GET /limit-configs/{id})

获取单个资源限制配置的详细信息。

#### 路径参数

- `id`: 资源限制配置ID

#### 响应 (200 OK)

```json
{
  "id": "limit-config-789",
  "role": "data-scientist",
  "project_id": "project-456",
  "project_name": "大模型训练项目",
  "project_details": {
    "id": "project-456",
    "name": "大模型训练项目",
    "description": "开发和训练超大规模语言模型",
    "team_id": "team-123"
  },
  "max_gpus": 16,
  "max_cpu": 128,
  "max_memory_gb": 512,
  "max_storage_gb": 2048,
  "description": "数据科学家在大模型训练项目中的资源限制",
  "effective_from": "2025-12-23T00:00:00Z",
  "expiration": null,
  "created_at": "2025-12-23T08:30:00Z",
  "created_by": {
    "id": "user-123",
    "username": "admin",
    "email": "admin@example.com"
  },
  "updated_at": "2025-12-23T08:30:00Z",
  "affected_users_count": 15,
  "links": {
    "self": "/api/v1/resources/limit-configs/limit-config-789",
    "project": "/api/v1/projects/project-456"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的资源限制配置不存在

### 更新特定资源限制配置 (PUT /limit-configs/{id})

更新现有资源限制配置的设置。

#### 路径参数

- `id`: 资源限制配置ID

#### 请求体

```json
{
  "max_gpus": 24,
  "max_cpu": 192,
  "max_memory_gb": 768,
  "max_storage_gb": 3072,
  "description": "数据科学家在大模型训练项目中的资源限制 - 已提升",
  "expiration": "2026-06-30T23:59:59Z"
}
```

#### 响应 (200 OK)

```json
{
  "id": "limit-config-789",
  "role": "data-scientist",
  "project_id": "project-456",
  "max_gpus": 24,
  "max_cpu": 192,
  "max_memory_gb": 768,
  "max_storage_gb": 3072,
  "updated_at": "2025-12-23T11:00:00Z",
  "links": {
    "self": "/api/v1/resources/limit-configs/limit-config-789"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的资源限制配置不存在

### 删除资源限制配置 (DELETE /limit-configs/{id})

删除指定的资源限制配置。

#### 路径参数

- `id`: 资源限制配置ID

#### 响应 (204 No Content)

成功删除后无响应体

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的资源限制配置不存在
- **409 Conflict**: 资源限制配置正在使用中，无法删除

### 获取资源使用统计 (GET /usage)

获取当前资源使用的总体统计数据。

#### 查询参数

- `time_range`: 时间范围，例如"day", "week", "month", "year"，默认为"day"
- `group_by`: 分组方式，例如"owner", "project", "user"，默认为"none"

#### 响应 (200 OK)

```json
{
  "time_range": "day",
  "start_time": "2025-12-23T00:00:00Z",
  "end_time": "2025-12-23T23:59:59Z",
  "total_usage": {
    "gpu_hours": 3072,
    "cpu_hours": 24576,
    "memory_gb_hours": 98304,
    "storage_gb_hours": 491520,
    "job_count": 128,
    "average_job_duration_hours": 6,
    "average_gpu_utilization": 0.85
  },
  "by_owner": [
    {
      "owner_type": "team",
      "owner_id": "team-123",
      "owner_name": "研发部",
      "gpu_hours": 1536,
      "job_count": 64,
      "percentage": 50
    },
    {
      "owner_type": "team",
      "owner_id": "team-124",
      "owner_name": "市场部",
      "gpu_hours": 768,
      "job_count": 32,
      "percentage": 25
    }
  ],
  "by_resource_type": {
    "gpu": {
      "total_hours": 3072,
      "peak_usage": 128,
      "average_usage": 96
    },
    "cpu": {
      "total_hours": 24576,
      "peak_usage": 1024,
      "average_usage": 768
    },
    "memory": {
      "total_gb_hours": 98304,
      "peak_usage_gb": 4096,
      "average_usage_gb": 3072
    }
  },
  "links": {
    "self": "/api/v1/resources/usage?time_range=day",
    "history": "/api/v1/resources/usage/history?time_range=day"
  }
}
```

### 获取历史资源使用数据 (GET /usage/history)

获取一段时间内的资源使用历史数据，用于趋势分析。

#### 查询参数

- `start_date`: 开始日期（ISO 8601格式），必需
- `end_date`: 结束日期（ISO 8601格式），必需
- `interval`: 数据聚合间隔，例如"hour", "day", "week"，默认为"day"
- `owner_type`: 按所有者类型过滤 (team, project)
- `owner_id`: 按所有者ID过滤
- `resource_type`: 资源类型过滤，例如"gpu", "cpu", "memory"，默认为所有类型

#### 响应 (200 OK)

```json
{
  "start_date": "2025-12-01T00:00:00Z",
  "end_date": "2025-12-23T23:59:59Z",
  "interval": "day",
  "time_points": [
    "2025-12-01T00:00:00Z",
    "2025-12-02T00:00:00Z",
    "2025-12-03T00:00:00Z",
    "..."
  ],
  "gpu_usage": {
    "total_hours": [2880, 2976, 3072, "..."],
    "peak_usage": [120, 124, 128, "..."],
    "average_usage": [90, 93, 96, "..."],
    "utilization": [0.82, 0.84, 0.85, "..."]
  },
  "cpu_usage": {
    "total_hours": [23040, 23808, 24576, "..."],
    "peak_usage": [960, 992, 1024, "..."],
    "average_usage": [720, 744, 768, "..."]
  },
  "memory_usage": {
    "total_gb_hours": [92160, 95232, 98304, "..."],
    "peak_usage_gb": [3840, 3968, 4096, "..."],
    "average_usage_gb": [2880, 2976, 3072, "..."]
  },
  "job_metrics": {
    "total_jobs": [120, 124, 128, "..."],
    "average_duration_hours": [5.8, 5.9, 6.0, "..."],
    "queue_time_minutes": [12, 14, 10, "..."]
  },
  "links": {
    "self": "/api/v1/resources/usage/history?start_date=2025-12-01T00:00:00Z&end_date=2025-12-23T23:59:59Z&interval=day"
  }
}
```

### 获取特定所有者的资源使用统计 (GET /usage/{owner_type}/{owner_id})

获取特定团队或项目的资源使用统计详情。

#### 路径参数

- `owner_type`: 所有者类型 (team, project)
- `owner_id`: 所有者ID

#### 查询参数

- `time_range`: 时间范围，例如"day", "week", "month", "year"，默认为"day"
- `include_users`: 布尔值，是否包含用户级别使用明细，默认为false

#### 响应 (200 OK)

```json
{
  "owner_type": "team",
  "owner_id": "team-123",
  "owner_name": "研发部",
  "time_range": "day",
  "start_time": "2025-12-23T00:00:00Z",
  "end_time": "2025-12-23T23:59:59Z",
  "quota": {
    "gpu_limit": 128,
    "cpu_limit": 1024,
    "memory_limit_gb": 4096,
    "storage_limit_gb": 20480
  },
  "usage": {
    "gpu_hours": 1536,
    "cpu_hours": 12288,
    "memory_gb_hours": 49152,
    "storage_gb_hours": 245760,
    "job_count": 64,
    "average_job_duration_hours": 6,
    "average_gpu_utilization": 0.87
  },
  "current": {
    "gpu_used": 64,
    "cpu_used": 512,
    "memory_used_gb": 2048,
    "storage_used_gb": 10240,
    "jobs_running": 8,
    "jobs_pending": 4
  },
  "by_project": [
    {
      "project_id": "project-456",
      "project_name": "大模型训练项目",
      "gpu_hours": 1024,
      "job_count": 40,
      "percentage": 66.7
    },
    {
      "project_id": "project-457",
      "project_name": "计算机视觉项目",
      "gpu_hours": 512,
      "job_count": 24,
      "percentage": 33.3
    }
  ],
  "by_user": [
    {
      "user_id": "user-234",
      "username": "zhang.wei",
      "gpu_hours": 384,
      "job_count": 16,
      "percentage": 25
    },
    {
      "user_id": "user-235",
      "username": "li.ming",
      "gpu_hours": 256,
      "job_count": 12,
      "percentage": 16.7
    }
  ],
  "usage_over_time": {
    "time_points": [
      "2025-12-23T00:00:00Z",
      "2025-12-23T06:00:00Z",
      "2025-12-23T12:00:00Z",
      "2025-12-23T18:00:00Z"
    ],
    "gpu_usage": [48, 56, 64, 60],
    "cpu_usage": [384, 448, 512, 480],
    "memory_usage_gb": [1536, 1792, 2048, 1920]
  },
  "links": {
    "self": "/api/v1/resources/usage/team/team-123?time_range=day",
    "history": "/api/v1/resources/usage/team/team-123/history",
    "owner": "/api/v1/teams/team-123"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的所有者不存在

### 获取资源成本分析 (GET /costs)

获取资源使用的成本分析数据。

#### 查询参数

- `time_range`: 时间范围，例如"day", "week", "month", "year"，默认为"month"
- `group_by`: 分组方式，例如"owner", "project", "user"，默认为"owner"

#### 响应 (200 OK)

```json
{
  "time_range": "month",
  "start_time": "2025-12-01T00:00:00Z",
  "end_time": "2025-12-31T23:59:59Z",
  "currency": "USD",
  "total_cost": 124800.00,
  "breakdown_by_resource": {
    "gpu": {
      "cost": 96000.00,
      "percentage": 76.9,
      "units": "GPU hours",
      "usage": 24000,
      "rate": 4.00
    },
    "cpu": {
      "cost": 9600.00,
      "percentage": 7.7,
      "units": "CPU hours",
      "usage": 192000,
      "rate": 0.05
    },
    "memory": {
      "cost": 7680.00,
      "percentage": 6.2,
      "units": "GB hours",
      "usage": 768000,
      "rate": 0.01
    },
    "storage": {
      "cost": 11520.00,
      "percentage": 9.2,
      "units": "GB months",
      "usage": 23040,
      "rate": 0.50
    }
  },
  "breakdown_by_owner": [
    {
      "owner_type": "team",
      "owner_id": "team-123",
      "owner_name": "研发部",
      "cost": 62400.00,
      "percentage": 50.0,
      "gpu_hours": 12000,
      "gpu_cost": 48000.00
    },
    {
      "owner_type": "team",
      "owner_id": "team-124",
      "owner_name": "市场部",
      "cost": 31200.00,
      "percentage": 25.0,
      "gpu_hours": 6000,
      "gpu_cost": 24000.00
    }
  ],
  "cost_trend": {
    "time_points": [
      "2025-12-01",
      "2025-12-08",
      "2025-12-15",
      "2025-12-22"
    ],
    "weekly_costs": [
      28800.00,
      30400.00,
      32000.00,
      33600.00
    ]
  },
  "links": {
    "self": "/api/v1/resources/costs?time_range=month",
    "forecast": "/api/v1/resources/costs/forecast"
  }
}
```

### 获取资源成本预测 (GET /costs/forecast)

获取未来一段时间的资源成本预测。

#### 查询参数

- `months`: 预测月数，默认为3，最大为12
- `owner_type`: 按所有者类型过滤 (team, project)
- `owner_id`: 按所有者ID过滤

#### 响应 (200 OK)

```json
{
  "forecast_months": 3,
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "currency": "USD",
  "forecast_total": 374400.00,
  "monthly_forecast": [
    {
      "month": "2026-01",
      "total_cost": 124800.00,
      "gpu_cost": 96000.00,
      "other_cost": 28800.00
    },
    {
      "month": "2026-02",
      "total_cost": 124800.00,
      "gpu_cost": 96000.00,
      "other_cost": 28800.00
    },
    {
      "month": "2026-03",
      "total_cost": 124800.00,
      "gpu_cost": 96000.00,
      "other_cost": 28800.00
    }
  ],
  "forecast_by_owner": [
    {
      "owner_type": "team",
      "owner_id": "team-123",
      "owner_name": "研发部",
      "forecast_total": 187200.00,
      "percentage": 50.0,
      "monthly_costs": [62400.00, 62400.00, 62400.00]
    },
    {
      "owner_type": "team",
      "owner_id": "team-124",
      "owner_name": "市场部",
      "forecast_total": 93600.00,
      "percentage": 25.0,
      "monthly_costs": [31200.00, 31200.00, 31200.00]
    }
  ],
  "forecast_methodology": {
    "model_type": "time_series",
    "features": ["historical_usage", "seasonal_patterns", "growth_trend"],
    "confidence": 0.85
  },
  "links": {
    "self": "/api/v1/resources/costs/forecast?months=3"
  }
}
```

### 获取特定所有者的资源成本分析 (GET /costs/{owner_type}/{owner_id})

获取特定团队或项目的资源成本分析详情。

#### 路径参数

- `owner_type`: 所有者类型 (team, project)
- `owner_id`: 所有者ID

#### 查询参数

- `time_range`: 时间范围，例如"month", "quarter", "year"，默认为"month"
- `include_users`: 布尔值，是否包含用户级别成本明细，默认为false

#### 响应 (200 OK)

```json
{
  "owner_type": "team",
  "owner_id": "team-123",
  "owner_name": "研发部",
  "time_range": "month",
  "start_time": "2025-12-01T00:00:00Z",
  "end_time": "2025-12-31T23:59:59Z",
  "currency": "USD",
  "total_cost": 62400.00,
  "budget": {
    "allocated": 80000.00,
    "remaining": 17600.00,
    "usage_percentage": 78.0
  },
  "breakdown_by_resource": {
    "gpu": {
      "cost": 48000.00,
      "percentage": 76.9,
      "units": "GPU hours",
      "usage": 12000,
      "rate": 4.00
    },
    "cpu": {
      "cost": 4800.00,
      "percentage": 7.7,
      "units": "CPU hours",
      "usage": 96000,
      "rate": 0.05
    },
    "memory": {
      "cost": 3840.00,
      "percentage": 6.2,
      "units": "GB hours",
      "usage": 384000,
      "rate": 0.01
    },
    "storage": {
      "cost": 5760.00,
      "percentage": 9.2,
      "units": "GB months",
      "usage": 11520,
      "rate": 0.50
    }
  },
  "breakdown_by_project": [
    {
      "project_id": "project-456",
      "project_name": "大模型训练项目",
      "cost": 41600.00,
      "percentage": 66.7,
      "gpu_hours": 8000,
      "gpu_cost": 32000.00
    },
    {
      "project_id": "project-457",
      "project_name": "计算机视觉项目",
      "cost": 20800.00,
      "percentage": 33.3,
      "gpu_hours": 4000,
      "gpu_cost": 16000.00
    }
  ],
  "breakdown_by_user": [
    {
      "user_id": "user-234",
      "username": "zhang.wei",
      "cost": 15600.00,
      "percentage": 25.0,
      "gpu_hours": 3000,
      "gpu_cost": 12000.00
    },
    {
      "user_id": "user-235",
      "username": "li.ming",
      "cost": 10400.00,
      "percentage": 16.7,
      "gpu_hours": 2000,
      "gpu_cost": 8000.00
    }
  ],
  "cost_trend": {
    "time_points": [
      "2025-12-01",
      "2025-12-08",
      "2025-12-15",
      "2025-12-22"
    ],
    "weekly_costs": [
      14400.00,
      15200.00,
      16000.00,
      16800.00
    ]
  },
  "links": {
    "self": "/api/v1/resources/costs/team/team-123?time_range=month",
    "forecast": "/api/v1/resources/costs/team/team-123/forecast",
    "owner": "/api/v1/teams/team-123"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的所有者不存在

### 获取集群列表 (GET /clusters)

获取所有计算集群的列表。

#### 查询参数

- `status`: 按状态过滤 (active, maintenance, inactive)

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "cluster-001",
      "name": "主生产集群",
      "description": "主要AI训练生产集群",
      "status": "active",
      "region": "cn-north-1",
      "instance_type": "p4d.24xlarge",
      "node_count": 16,
      "gpu_count": 128,
      "cpu_count": 1536,
      "memory_gb": 49152,
      "utilization": {
        "gpu": 0.85,
        "cpu": 0.75,
        "memory": 0.80
      },
      "links": {
        "self": "/api/v1/resources/clusters/cluster-001",
        "nodes": "/api/v1/resources/clusters/cluster-001/nodes",
        "metrics": "/api/v1/resources/clusters/cluster-001/metrics"
      }
    },
    {
      "id": "cluster-002",
      "name": "开发测试集群",
      "description": "开发和测试用AI训练集群",
      "status": "active",
      "region": "cn-north-1",
      "instance_type": "p3.8xlarge",
      "node_count": 8,
      "gpu_count": 32,
      "cpu_count": 256,
      "memory_gb": 2048,
      "utilization": {
        "gpu": 0.65,
        "cpu": 0.55,
        "memory": 0.60
      },
      "links": {
        "self": "/api/v1/resources/clusters/cluster-002",
        "nodes": "/api/v1/resources/clusters/cluster-002/nodes",
        "metrics": "/api/v1/resources/clusters/cluster-002/metrics"
      }
    }
  ]
}
```

### 获取特定集群详情 (GET /clusters/{id})

获取单个计算集群的详细信息。

#### 路径参数

- `id`: 集群ID

#### 响应 (200 OK)

```json
{
  "id": "cluster-001",
  "name": "主生产集群",
  "description": "主要AI训练生产集群",
  "status": "active",
  "region": "cn-north-1",
  "zone": "cn-north-1a",
  "instance_type": "p4d.24xlarge",
  "gpu_type": "nvidia-a100-80g",
  "node_count": 16,
  "gpu_count": 128,
  "cpu_count": 1536,
  "memory_gb": 49152,
  "storage_gb": 327680,
  "network": {
    "type": "vpc",
    "bandwidth_gbps": 400,
    "interconnect": "high-speed"
  },
  "utilization": {
    "gpu": 0.85,
    "cpu": 0.75,
    "memory": 0.80,
    "storage": 0.65
  },
  "job_stats": {
    "jobs_running": 32,
    "jobs_pending": 16,
    "average_wait_time_minutes": 15
  },
  "status_history": {
    "last_maintenance": "2025-12-01T00:00:00Z",
    "next_maintenance": "2026-01-01T00:00:00Z",
    "uptime_percentage": 99.95
  },
  "costs": {
    "hourly_rate_usd": 400.00,
    "monthly_cost_usd": 288000.00
  },
  "links": {
    "self": "/api/v1/resources/clusters/cluster-001",
    "nodes": "/api/v1/resources/clusters/cluster-001/nodes",
    "metrics": "/api/v1/resources/clusters/cluster-001/metrics",
    "scale": "/api/v1/resources/clusters/cluster-001/actions/scale"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的集群不存在

### 获取集群节点列表 (GET /clusters/{id}/nodes)

获取特定集群的节点列表。

#### 路径参数

- `id`: 集群ID

#### 查询参数

- `status`: 按状态过滤 (ready, not-ready, maintenance)
- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100

#### 响应 (200 OK)

```json
{
  "cluster_id": "cluster-001",
  "items": [
    {
      "id": "node-001",
      "name": "worker-0",
      "status": "ready",
      "health": "healthy",
      "instance_type": "p4d.24xlarge",
      "gpu_count": 8,
      "cpu_count": 96,
      "memory_gb": 1152,
      "uptime_days": 45,
      "utilization": {
        "gpu": 0.92,
        "cpu": 0.85,
        "memory": 0.88
      },
      "jobs": [
        {
          "id": "job-789",
          "name": "bert-pretrain-job-001",
          "user": "zhang.wei",
          "gpu_count": 8
        }
      ],
      "links": {
        "self": "/api/v1/resources/clusters/cluster-001/nodes/node-001",
        "metrics": "/api/v1/resources/clusters/cluster-001/nodes/node-001/metrics"
      }
    },
    {
      "id": "node-002",
      "name": "worker-1",
      "status": "ready",
      "health": "healthy",
      "instance_type": "p4d.24xlarge",
      "gpu_count": 8,
      "cpu_count": 96,
      "memory_gb": 1152,
      "uptime_days": 32,
      "utilization": {
        "gpu": 0.88,
        "cpu": 0.80,
        "memory": 0.82
      },
      "jobs": [
        {
          "id": "job-790",
          "name": "gpt-finetune",
          "user": "li.ming",
          "gpu_count": 8
        }
      ],
      "links": {
        "self": "/api/v1/resources/clusters/cluster-001/nodes/node-002",
        "metrics": "/api/v1/resources/clusters/cluster-001/nodes/node-002/metrics"
      }
    }
  ],
  "pagination": {
    "total_items": 16,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  },
  "summary": {
    "total_nodes": 16,
    "ready_nodes": 16,
    "not_ready_nodes": 0,
    "maintenance_nodes": 0,
    "average_gpu_utilization": 0.85
  },
  "links": {
    "self": "/api/v1/resources/clusters/cluster-001/nodes",
    "cluster": "/api/v1/resources/clusters/cluster-001"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的集群不存在

### 获取集群指标数据 (GET /clusters/{id}/metrics)

获取特定集群的详细指标数据。

#### 路径参数

- `id`: 集群ID

#### 查询参数

- `start_time`: 开始时间（ISO 8601格式）
- `end_time`: 结束时间（ISO 8601格式）
- `interval`: 数据聚合间隔，例如"5m", "1h", "1d"，默认为"1h"
- `metrics`: 要获取的指标列表，用逗号分隔（例如"gpu_utilization,cpu_utilization,memory_utilization"）

#### 响应 (200 OK)

```json
{
  "cluster_id": "cluster-001",
  "start_time": "2025-12-23T00:00:00Z",
  "end_time": "2025-12-23T23:59:59Z",
  "interval": "1h",
  "time_points": [
    "2025-12-23T00:00:00Z",
    "2025-12-23T01:00:00Z",
    "2025-12-23T02:00:00Z",
    "..."
  ],
  "gpu_utilization": {
    "average": [0.82, 0.84, 0.85, "..."],
    "max": [0.95, 0.96, 0.97, "..."],
    "min": [0.75, 0.76, 0.78, "..."]
  },
  "cpu_utilization": {
    "average": [0.72, 0.74, 0.75, "..."],
    "max": [0.85, 0.86, 0.87, "..."],
    "min": [0.65, 0.66, 0.68, "..."]
  },
  "memory_utilization": {
    "average": [0.78, 0.79, 0.80, "..."],
    "max": [0.90, 0.91, 0.92, "..."],
    "min": [0.70, 0.71, 0.72, "..."]
  },
  "network_throughput_gbps": {
    "ingress": [120, 125, 130, "..."],
    "egress": [110, 115, 120, "..."]
  },
  "job_metrics": {
    "running": [28, 30, 32, "..."],
    "pending": [14, 15, 16, "..."],
    "completed": [5, 6, 7, "..."],
    "failed": [0, 1, 0, "..."]
  },
  "links": {
    "self": "/api/v1/resources/clusters/cluster-001/metrics?interval=1h",
    "cluster": "/api/v1/resources/clusters/cluster-001"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的集群不存在

### 扩缩集群规模 (POST /clusters/{id}/actions/scale)

调整计算集群的规模。

#### 路径参数

- `id`: 集群ID

#### 请求体

```json
{
  "target_node_count": 24,
  "reason": "满足业务峰值需求",
  "schedule": {
    "start_time": "2025-12-24T00:00:00Z",
    "end_time": null
  },
  "approval": {
    "approver_id": "user-123",
    "approval_code": "AP12345"
  }
}
```

#### 响应 (202 Accepted)

```json
{
  "cluster_id": "cluster-001",
  "current_node_count": 16,
  "target_node_count": 24,
  "scaling_operation_id": "scaling-789",
  "operation_type": "scale_up",
  "status": "pending",
  "schedule": {
    "start_time": "2025-12-24T00:00:00Z",
    "estimated_completion_time": "2025-12-24T01:00:00Z"
  },
  "estimated_cost_change": {
    "additional_hourly_cost_usd": 200.00,
    "additional_monthly_cost_usd": 144000.00
  },
  "links": {
    "self": "/api/v1/resources/clusters/cluster-001/actions/scale",
    "operation": "/api/v1/operations/scaling-789",
    "cluster": "/api/v1/resources/clusters/cluster-001"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的集群不存在
- **409 Conflict**: 集群状态不允许缩放操作

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
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

## 错误响应格式

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "资源配额不存在",
    "details": "找不到ID为quota-456的资源配额",
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