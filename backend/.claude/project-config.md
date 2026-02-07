# 项目配置 - AI Training Platform

> **职责**: AI Training Platform 项目的特定配置，包含模块列表和导入路径。

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。

---

## 项目信息

| 配置项 | 值 |
|--------|-----|
| **项目名称** | ai-studio-project (AI Training Platform) |
| **项目描述** | 基于 AWS SageMaker HyperPod 的企业级 AI 训练平台 |
| **架构模式** | DDD + Modular Monolith + Clean Architecture |
| **Python 版本** | 3.11 |
| **源码根路径** | `src` |
| **模块路径** | `src/modules` |
| **共享路径** | `src/shared` |

---

## 业务模块

> **维护提示**: 新增模块时同步更新此表和 `src/modules/` 目录。

| 模块 | 职责 | 核心实体 | 外部依赖 |
|------|------|---------|---------|
| `auth` | 用户认证、授权、RBAC | User, LoginAttempt | SSO Provider |
| `training` | 训练任务生命周期管理 | TrainingJob, Checkpoint | HyperPod, Kueue |
| `models` | 模型版本控制、审批 | Model, ModelVersion | Model Registry |
| `quotas` | 资源配额配置与管理 | ResourceQuota, ResourceLimitConfig | Kueue ClusterQueue |
| `spaces` | 在线开发环境管理 | Space | SageMaker Spaces |
| `datasets` | 数据集版本管理与存储 | Dataset, DatasetVersion | S3, FSx |
| `billing` | 成本统计与计费分析 | CostRecord, UsageReport | - |
| `monitoring` | 训练监控与告警 | Metric, Alert | CloudWatch |
| `audit` | 审计日志记录与查询 | AuditLog | - |

---

## 核心域事件

> **设计原则**: 事件用于模块间解耦通信，订阅者不应直接依赖发布者的实现。

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| `training` | `TrainingJobSubmittedEvent` | 任务提交 | quotas, audit |
| `training` | `TrainingJobCompletedEvent` | 任务完成 | audit, monitoring |
| `training` | `TrainingJobFailedEvent` | 任务失败 | audit, monitoring |
| `quotas` | `QuotaExceededEvent` | 配额超限 | monitoring |
| `auth` | `UserCreatedEvent` | 用户创建 | quotas (初始化配额) |
| `models` | `ModelPublishedEvent` | 模型发布 | audit |

---

## 导入路径配置

> **原则**: 参考 [rules/architecture.md](rules/architecture.md) 模块隔离章节。

### 共享内核导入

```python
# Domain 层共享
from src.shared.domain import (
    BaseEntity, PydanticEntity,
    IRepository,
    DomainError, EntityNotFoundError, ValidationError,
    DuplicateEntityError, InvalidStateTransitionError,
    ResourceQuotaExceededError,
    DomainEvent, event_bus, event_handler,
    IQuotaChecker,  # 跨模块接口
)

# Infrastructure 层共享
from src.shared.infrastructure import get_db, get_settings
from src.shared.infrastructure.security import hash_password, verify_password
from src.shared.infrastructure import PydanticRepository

# API 层共享
from src.shared.api import domain_exception_handler
from src.shared.api.schemas import EntitySchema, PaginatedResponse
```

### 认证依赖 (唯一跨模块例外)

```python
# 仅允许在 API 层导入
from src.modules.auth.api.dependencies import (
    get_current_active_user,
    require_admin,
    require_engineer,
    require_viewer,
)
from src.modules.auth.api.current_user import CurrentUser
```

---

## 外部服务配置

> **位置约定**: 所有外部服务适配器放在对应模块的 `infrastructure/` 下。

| 服务 | 用途 | 适配器位置 |
|------|------|-----------|
| AWS SageMaker HyperPod | 分布式训练管理 | `modules/training/infrastructure/hyperpod/` |
| AWS S3 | 数据集和模型存储 | `shared/infrastructure/storage/s3_client.py` |
| AWS S3 (分片上传) | 大文件断点续传 | `modules/datasets/infrastructure/s3/` |
| Kueue | 资源调度和优先级管理 | `modules/training/infrastructure/` |
| MLflow | 实验追踪和指标记录 | `modules/training/application/services/mlflow_service.py` |

---

## 待解决问题

### 数据模型一致性问题

#### 问题1: resource_quotas 表与 Kueue 配额重复

| 项目 | 说明 |
|------|------|
| **现状** | 应用层存储 `max_gpu_count`, `max_cpu_cores`, `max_memory_gb` |
| **问题** | Kueue ClusterQueue 已管理这些配额值，存在数据不一致风险 |
| **待确认** | 应用层是"配置源"同步到 Kueue，还是只存业务元数据？ |

#### 问题2: development_spaces 表与 SageMaker Spaces 状态同步

| 项目 | 说明 |
|------|------|
| **现状** | 应用层缓存 `status`, `instance_type` 等字段 |
| **问题** | SageMaker Spaces API 已提供这些信息，需要同步策略 |
| **待确认** | 缓存更新机制（轮询/事件驱动） |

---

## HyperPod 集成

> **踩坑记录和诊断清单参见**: `../.claude/skills/hyperpod-scheduling/SKILL.md`

已解决的关键问题:
- TAS 配置问题（Workload Pending）
- 抢占不生效（Cohort 配置）
- PriorityClass 双重资源（WorkloadPriorityClass vs PriorityClass）
- PodsRunning 状态不一致
- set_cluster_context 必须先调用

---

## 架构合规

> 详见 [rules/architecture.md](rules/architecture.md)
